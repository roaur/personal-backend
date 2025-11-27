import logging
import requests
import berserk
from celery import Celery
import os
from shared.config import settings
from worker.utils.lichess_utils import (
    setup_berserk_client, 
    post_game,
    extract_players_from_game,
    post_player,
    post_player_to_match,
)
from datetime import datetime
import redis
import json
from sqlalchemy import create_engine, text
from worker.analysis.plugin_manager import PluginManager
from worker.analysis.storage import StorageManager

# =============================================================================
# Celery Architecture: Producer-Consumer Pattern
# =============================================================================
# This system is designed to fetch game data from the Lichess API and store it
# in a PostgreSQL database via a FastAPI backend.
#
# It uses a Producer-Consumer pattern to strictly adhere to Lichess API rate limits
# (1 request at a time) while maximizing data processing throughput.
#
# Components:
# 1. Orchestrator (Scheduler):
#    - Runs every 60 seconds.
#    - Identifies which players need to be updated (Main User then Opponents).
#    - Dispatches `fetch_player_games` tasks to the `api_queue`.
#
# 2. Producer (`fetch_player_games`):
#    - Queue: `api_queue` (Concurrency: 1).
#    - Responsibility: Streams game data from Lichess API (NDJSON).
#    - Constraint: MUST run serially to respect the 1 request at a time limit.
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
app = Celery('worker', broker=os.getenv('CELERY_BROKER_URL'))
app.conf.task_compression = 'gzip' # Compress messages to save Redis memory

# Initialize Redis client for distributed locking
# We reuse the broker URL for the Redis client connection
redis_client = redis.from_url(os.getenv('CELERY_BROKER_URL'))

# Helper function to get last move time (for main user)
def get_last_move_time(username: str) -> int:
    """
    Fetches the timestamp (ms) of the last move played by the specified user
    from the database via FastAPI. Used as a cursor for fetching new games.
    """
    url = f"http://{settings.fastapi_route}/games/get_last_move_played_time/{username}"
    response = requests.get(url)
    response.raise_for_status()
    output = response.json()
    logging.info(f"Last move time received for {username}: {output['last_move_time']}")
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
        last_move_time = get_last_move_time(settings.lichess_username)
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
            
            # Use the last_move_time returned by the backend as the cursor
            since = player.get('last_move_time', 0)
            
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
    """
    logging.info(f"Fetching games for {username} since {since}")
    
    lock = _acquire_lichess_lock(username)
    if not lock:
        logging.warning(f"Could not acquire Lichess API lock for {username}. Retrying...")
        self.retry(countdown=10, max_retries=5)
        return

    try:
        params = {
            "max": 1000,
            "sort": "dateAsc",
            "pgnInJson": "true"
        }
        if since:
            params["since"] = int(since)
        else:
            # Idempotency: If 'since' is not provided, check the DB for the last move time.
            # This ensures we don't re-fetch games we already have if the task is triggered manually or retried without context.
            try:
                last_db_time = get_last_move_time(username)
                if last_db_time > 0:
                    params["since"] = last_db_time
                    logging.info(f"Idempotency: Resuming fetch for {username} from {last_db_time}")
            except Exception as e:
                logging.warning(f"Could not fetch last move time for {username}: {e}")

        # Fetch ONE batch of games
        # We removed the loop to allow "interleaving" of tasks for different users.
        # If there are more games, we re-queue the task.
        
        logging.info(f"Requesting games for {username} with params: {params}")
        
        count, last_game_time = _fetch_and_dispatch_batch(username, params, depth)
        
        # Pagination Logic:
        # If we got the maximum number of games (1000), there are likely more.
        # We re-queue the task with the new 'since' cursor.
        if count >= params["max"]:
            if last_game_time:
                logging.info(f"Pagination: Re-queuing fetch for {username} starting from {last_game_time}")
                # Dispatch new task to the back of the queue
                fetch_player_games.delay(username, since=last_game_time, depth=depth)
            else:
                logging.warning("Pagination: Could not determine last game time. Stopping.")
        
    except Exception as e:
        logging.error(f"Error fetching games for {username}: {e}")
        self.retry(exc=e, countdown=10, max_retries=5)
        
    finally:
        try:
            lock.release()
        except redis.LockError:
            pass

def _acquire_lichess_lock(username: str):
    """Attempts to acquire the global Lichess API lock."""
    lock = redis_client.lock("lichess_api_lock", timeout=300)
    if lock.acquire(blocking=True, blocking_timeout=10):
        return lock
    return None

def _fetch_and_dispatch_batch(username: str, params: dict, depth: int):
    """
    Fetches a single batch of games and dispatches them.
    Returns (count, last_game_time).
    """
    headers = {
        'Authorization': f'Bearer {settings.lichess_token}',
        'Accept': 'application/x-ndjson'
    }
    url = f"https://lichess.org/api/games/user/{username}"
    
    count = 0
    last_game_time = 0

    with requests.get(url, headers=headers, params=params, stream=True) as response:
        if response.status_code == 429:
            logging.warning(f"Rate limit hit for {username}. Retrying in 60s.")
            raise Exception("Rate limit hit")

        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                try:
                    game = json.loads(line)
                    process_game_data.delay(game, depth)
                    count += 1
                    
                    if 'lastMoveAt' in game:
                        last_game_time = game['lastMoveAt']
                        
                except json.JSONDecodeError as e:
                    logging.error(f"Error decoding line: {e}")
    
    logging.info(f"Dispatched {count} games for {username}")
    return count, last_game_time

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

@app.task(queue='analysis_queue')
def analyze_new_games(batch_size: int = 100):
    """
    Analysis Task.
    
    Role: ETL Engine
    Queue: `analysis_queue`
    
    Responsibilities:
    1. Fetches unanalyzed games from Postgres.
    2. Runs all discovered analysis plugins on them.
    3. Stores the extracted features back to Postgres (game_features table).
    """
    logging.info("Starting analysis task...")
    
    # 1. Setup
    plugin_manager = PluginManager()
    plugin_manager.discover_plugins()
    storage_manager = StorageManager() # Uses settings from utils.config implicitly via internal logic or we pass db_url
    
    # We need a DB connection to fetch games. 
    # Since we are in a task, we can use sqlalchemy directly.
    # We reuse the settings.database_url which we added to config.
    engine = create_engine(settings.database_url)
    
    try:
        with engine.connect() as conn:
            # 2. Fetch Unanalyzed Games
            # Simple strategy: Find games that don't have ANY features yet.
            # This is a simplification; ideally we'd track 'analyzed' status or version.
            # For now, this is idempotent enough: if features exist, we skip.
            query = text("""
                SELECT g.game_id, g.pgn 
                FROM chess.games g
                WHERE NOT EXISTS (
                    SELECT 1 FROM chess.game_features gf WHERE gf.game_id = g.game_id
                )
                AND g.pgn IS NOT NULL
                LIMIT :limit
            """)
            
            result = conn.execute(query, {"limit": batch_size})
            games_to_analyze = result.fetchall()
            
            if not games_to_analyze:
                logging.info("No new games to analyze.")
                return

            logging.info(f"Analyzing {len(games_to_analyze)} games...")

            # 3. Run Plugins & Store Results
            for row in games_to_analyze:
                game_id = row.game_id
                pgn_text = row.pgn
                
                # Construct game dict expected by plugins
                game_data = {"game_id": game_id, "pgn": pgn_text}
                
                try:
                    # Run all plugins
                    features = plugin_manager.run_all(game_data)
                    
                    # Store features
                    if features:
                        storage_manager.save_features(game_id, features)
                        
                except Exception as e:
                    logging.error(f"Error analyzing game {game_id}: {e}")
                    # Continue to next game even if one fails
                    continue
                    
            logging.info("Analysis batch complete.")

    except Exception as e:
        logging.error(f"Analysis task failed: {e}")
        raise
