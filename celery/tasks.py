import logging
import requests
import berserk
from celery import Celery
import os
from utils.config import settings
from utils.lichess_utils import (
    setup_berserk_client, 
    post_game,
    extract_players_from_game,
    post_player,
    post_player_to_match,
)
from datetime import datetime
import redis
import json

# =============================================================================
# Celery Architecture: Producer-Consumer Pattern
# =============================================================================
# This system is designed to fetch game data from the Lichess API and store it
# in a PostgreSQL database via a FastAPI backend.
#
# It uses a Producer-Consumer pattern to strictly adhere to Lichess API rate limits
# (1 request/second) while maximizing data processing throughput.
#
# Components:
# 1. Orchestrator (Scheduler):
#    - Runs every 60 seconds.
#    - Identifies which players need to be updated (Main User + Opponents).
#    - Dispatches `fetch_player_games` tasks to the `api_queue`.
#
# 2. Producer (`fetch_player_games`):
#    - Queue: `api_queue` (Concurrency: 1).
#    - Responsibility: Streams game data from Lichess API (NDJSON).
#    - Constraint: MUST run serially to respect the 1 req/sec limit.
#    - Mechanism: Uses a Redis distributed lock (`lichess_api_lock`) to ensure
#      ABSOLUTELY NO CONCURRENT REQUESTS across the entire system, even if
#      multiple producer workers are running.
#    - Action: For each game received in the stream, immediately dispatches a
#      `process_game_data` task to the `db_queue`.
#
# 3. Consumer (`process_game_data`):
#    - Queue: `db_queue` (Concurrency: Scalable, e.g., 8).
#    - Responsibility: Processes raw game data and writes to the DB.
#    - Action: Parses JSON, extracts players, and posts to FastAPI.
#
# =============================================================================

# Configure Celery app
# Use Redis as the message broker
app = Celery('tasks', broker=os.getenv('CELERY_BROKER_URL'))
app.conf.task_compression = 'gzip' # Compress messages to save Redis memory

# Initialize Redis client for distributed locking
# We reuse the broker URL for the Redis client connection
redis_client = redis.from_url(os.getenv('CELERY_BROKER_URL'))

# Helper function to get last move time (for main user)
def get_last_move_time() -> int:
    """
    Fetches the timestamp (ms) of the last move played by the main user
    from the database via FastAPI. Used as a cursor for fetching new games.
    """
    url = f"http://{settings.fastapi_route}/games/get_last_move_played_time"
    response = requests.get(url)
    response.raise_for_status()
    output = response.json()
    logging.info("Last move time received: %s", output["last_move_time"])
    return output['last_move_time']

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """
    Configures periodic tasks (Celery Beat).
    """
    # Run the orchestrator every 60 seconds
    sender.add_periodic_task(60.0, orchestrator.s(), name='orchestrator-every-60-seconds')
    # Trigger immediately on startup
    orchestrator.delay()

@app.task
def orchestrator():
    """
    Orchestrator Task.
    
    Role: Scheduler / Manager
    Queue: Default (or api_queue)
    
    Responsibilities:
    1. Checks the main user (roaur) for new games.
    2. Asks the backend for the next opponent who needs updating.
    3. Dispatches `fetch_player_games` tasks to the `api_queue`.
    """
    # 1. Process Main User
    try:
        last_move_time = get_last_move_time()
        # Trigger producer for main user
        # We use delay() to send the task to the queue
        fetch_player_games.delay(settings.lichess_username, since=last_move_time, depth=0)
    except Exception as e:
        logging.error(f"Error processing main user: {e}")

    # 2. Process Next Opponent
    try:
        url = f"http://{settings.fastapi_route}/players/process/next"
        response = requests.get(url)
        if response.status_code == 200:
            player = response.json()
            logging.info(f"Processing next player: {player['player_id']} (Depth {player['depth']})")
            
            since = 0
            if player.get('last_fetched_at'):
                # Convert ISO string to timestamp (ms)
                dt = datetime.fromisoformat(player['last_fetched_at'].replace('Z', '+00:00'))
                since = int(dt.timestamp() * 1000)
            
            # Trigger producer for opponent
            fetch_player_games.delay(player['player_id'], since=since, depth=player['depth'])
    except Exception as e:
        # It's okay if there are no players to process or if request fails
        logging.warning(f"Could not process next opponent: {e}")

@app.task(bind=True, queue='api_queue')
def fetch_player_games(self, username: str, since: int, depth: int):
    """
    Producer Task.
    
    Role: Data Fetcher
    Queue: `api_queue` (MUST have concurrency=1 in worker config)
    
    Responsibilities:
    1. Acquires a GLOBAL REDIS LOCK to ensure absolutely no concurrent requests.
    2. Connects to Lichess API `/api/games/user/{username}`.
    3. Uses streaming (NDJSON) to receive games line-by-line.
    4. For EACH game received, immediately dispatches a `process_game_data` task.
    
    This ensures that we never block on the API request and can process games
    in parallel as they arrive.
    """
    logging.info(f"Fetching games for {username} since {since}")
    
    # Use direct requests for explicit streaming control
    headers = {
        'Authorization': f'Bearer {settings.lichess_token}',
        'Accept': 'application/x-ndjson'
    }
    
    params = {
        "max": 1000,          # Fetch up to 1000 games
        "sort": "dateAsc",    # Oldest first (to maintain chronological order)
        "pgnInJson": "true"   # Include PGN in the JSON response
    }
    if since:
        params["since"] = int(since)
        
    url = f"https://lichess.org/api/games/user/{username}"
    
    # Distributed Lock: Ensure ONLY ONE request to Lichess happens at a time across ALL workers.
    # We use a blocking lock with a timeout. 
    # If we can't get the lock within 10 seconds, we retry later.
    lock = redis_client.lock("lichess_api_lock", timeout=300) # 5 minute lock timeout (safety net)
    
    have_lock = False
    try:
        # Try to acquire the lock, waiting up to 10 seconds
        have_lock = lock.acquire(blocking=True, blocking_timeout=10)
        
        if not have_lock:
            logging.warning(f"Could not acquire Lichess API lock for {username}. Retrying...")
            raise Exception("Could not acquire lock") # Will trigger retry below

        # stream=True is critical here! It keeps the connection open and yields data chunks.
        with requests.get(url, headers=headers, params=params, stream=True) as response:
            if response.status_code == 429:
                logging.warning(f"Rate limit hit for {username}. Retrying in 60s.")
                # self.retry(countdown=60) # Optional: Retry logic
                return

            response.raise_for_status()
            
            count = 0
            # Iterate line by line (NDJSON format)
            for line in response.iter_lines():
                if line:
                    try:
                        game = json.loads(line)
                        # Dispatch to consumer immediately
                        # This puts the heavy lifting (DB writes) onto the db_queue
                        process_game_data.delay(game, depth)
                        count += 1
                    except json.JSONDecodeError as e:
                        logging.error(f"Error decoding line: {e}")
            
            logging.info(f"Dispatched {count} games for {username}")
        
    except Exception as e:
        logging.error(f"Error fetching games for {username}: {e}")
        # Retry with exponential backoff if we couldn't get the lock or failed
        self.retry(exc=e, countdown=10, max_retries=5)
        
    finally:
        if have_lock:
            try:
                lock.release()
            except redis.LockError:
                # Lock might have expired or already been released
                pass
@app.task(queue='db_queue')
def process_game_data(game: dict, depth: int):
    """
    Consumer Task.
    
    Role: Data Processor
    Queue: `db_queue` (Can have high concurrency, e.g., 8+)
    
    Responsibilities:
    1. Receives a single raw game dictionary.
    2. Extracts player information (White/Black).
    3. Posts the game, players, and match links to the backend.
    """
    try:
        game_id = game.get("id")
        logging.info(f"Processing game {game_id}")
        
        # 1. Post Game to DB
        post_game(game)
        
        # 2. Extract and Process Players
        white_player, black_player = extract_players_from_game(game)
        
        # Update depths for graph traversal
        # Logic: If I am depth N, my opponents are depth N+1
        next_depth = depth + 1
        
        def prepare_player(p_data):
            p_data['depth'] = next_depth
            return p_data

        white_player = prepare_player(white_player)
        black_player = prepare_player(black_player)

        # Post Players to DB
        post_player(white_player)
        post_player(black_player)
        
        # 3. Link Players to Match (Many-to-Many relationship)
        post_player_to_match(white_player, game_id, "white")
        post_player_to_match(black_player, game_id, "black")
        
    except Exception as e:
        logging.error(f"Error processing game {game.get('id')}: {e}")
