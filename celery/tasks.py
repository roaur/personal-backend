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

# Helper function to get last move time
def get_last_move_time() -> int:
    url = f"http://{settings.fastapi_route}/games/get_last_move_played_time"
    response = requests.get(url)
    response.raise_for_status()
    output = response.json()
    logging.info("Last move time received: %s", output["last_move_time"])
    return output['last_move_time']

# Helper function to get matches
def get_matches(start: int) -> list[dict]:
    """
    Fetch matches from Lichess using the client and a given start time.
    """
    session = setup_berserk_client()
    client = berserk.Client(session)
    games = client.games.export_by_player(settings.lichess_username, since=start, max=100, sort="dateAsc", pgn_in_json=True)
    matches = [game for game in games]
    logging.info("Fetched %s matches", len(matches))
    return matches

# Configure Celery app
app = Celery('tasks', broker=os.getenv('CELERY_BROKER_URL'))

# Configure Beat Schedule
app.conf.beat_schedule = {
    'pull-matches-every-minute': {
        'task': 'tasks.pull_matches',
        'schedule': 60.0,  # Run every 60 seconds
    },
}

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Call pull_matches immediately on startup
    sender.add_periodic_task(10.0, pull_matches.s(), name='pull-matches-every-minute')
    pull_matches.delay()

@app.task
def pull_matches():

    """
    Fetch matches from Lichess and post them to FastAPI.
    This logic is being migrated from Airflow.
    """
    try:
        last_move_time = get_last_move_time()
        matches = get_matches(last_move_time)
        
        for match in matches:
            logging.info(f"Processing match {match.get('id')}")
            game_id = match["id"]
            post_game(match)

            # Process players
            white_player, black_player = extract_players_from_game(match)
            post_player(white_player)
            post_player_to_match(white_player, game_id, "white")
            post_player(black_player)
            post_player_to_match(black_player, game_id, "black")

            # Process moves
            move_list = {
                "moves": match["moves"],
                "variant": match["variant"],
                "initial_fen": match.get("initialFen")
            }
            post_moves_to_match(move_list, game_id)
            
    except Exception as e:
        logging.error(f"Error in pull_matches: {e}")
        raise e

