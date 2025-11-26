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
    post_moves_to_match,
    post_player,
    post_player_to_match
)

from datetime import datetime, timezone

# Helper function to get last move time (for main user)
def get_last_move_time() -> int:
    url = f"http://{settings.fastapi_route}/games/get_last_move_played_time"
    response = requests.get(url)
    response.raise_for_status()
    output = response.json()
    logging.info("Last move time received: %s", output["last_move_time"])
    return output['last_move_time']

# Helper function to get matches
def get_matches(username: str, start: int = 0) -> list[dict]:
    """
    Fetch matches from Lichess using the client and a given start time.
    """
    session = setup_berserk_client()
    client = berserk.Client(session)
    # If start is 0 or None, berserk/lichess handles it (fetches all)
    # Ensure start is int if provided
    kwargs = {"max": 100, "sort": "dateAsc", "pgn_in_json": True}
    if start:
        kwargs["since"] = int(start)
        
    games = client.games.export_by_player(username, **kwargs)
    matches = [game for game in games]
    logging.info("Fetched %s matches for %s", len(matches), username)
    return matches

# Configure Celery app
app = Celery('tasks', broker=os.getenv('CELERY_BROKER_URL'))

# Configure Beat Schedule
app.conf.beat_schedule = {
    'pull-matches-every-5-seconds': {
        'task': 'tasks.pull_matches',
        'schedule': 10.0,  # Run every 5 seconds
    },
}

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Call pull_matches immediately on startup
    sender.add_periodic_task(5.0, pull_matches.s(), name='pull-matches-every-5-seconds')
    pull_matches.delay()

@app.task
def pull_matches():
    """
    Orchestrator task.
    1. Fetches matches for the main user (roaur).
    2. Fetches matches for the next eligible opponent from the DB.
    """
    # 1. Process Main User
    # For main user, we use the max(last_move_at) from DB as the cursor
    try:
        last_move_time = get_last_move_time()
        process_player(settings.lichess_username, depth=0, since=last_move_time)
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
            
            process_player(player['player_id'], depth=player['depth'], since=since)
    except Exception as e:
        # It's okay if there are no players to process or if request fails
        logging.warning(f"Could not process next opponent: {e}")

def process_player(username: str, depth: int, since: int = 0):
    """
    Fetch matches for a specific player and process them.
    """
    try:
        matches = get_matches(username, start=since)
        
        for match in matches:
            logging.info(f"Processing match {match.get('id')}")
            game_id = match["id"]
            post_game(match)

            # Process players
            white_player, black_player = extract_players_from_game(match)
            
            # Update depths
            next_depth = depth + 1
            
            def prepare_player(p_data):
                p_data['depth'] = next_depth
                if p_data['player_id'].lower() == username.lower():
                    p_data['depth'] = depth 
                return p_data

            white_player = prepare_player(white_player)
            black_player = prepare_player(black_player)

            post_player(white_player)
            post_player_to_match(white_player, game_id, "white")
            post_player(black_player)
            post_player_to_match(black_player, game_id, "black")

    except Exception as e:
        logging.error(f"Error in process_player for {username}: {e}")
        # Don't raise, just log, so orchestrator can continue


