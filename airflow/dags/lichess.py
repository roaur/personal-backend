import logging

from typing import Dict, List, Tuple, Generator
from airflow.decorators import task, dag, task_group
from airflow.utils.dates import days_ago
from requests.adapters import HTTPAdapter
import requests
from urllib3 import Retry
import berserk
import datetime

from utils.lichess_utils import (
    setup_berserk_client, 
    parse_and_enumerate_moves,
    format_match_core,
    post_game,
    extract_players_from_game,
    post_moves_to_match,
    post_player,
    post_player_to_match
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

MAX_RETRIES = 10
BACKOFF_FACTOR = 2

import utils.config as config

settings = config.settings

@dag(
    schedule_interval="* * * * *",  # Run every minute
    start_date=days_ago(1),  # Allows the DAG to backfill if needed
    catchup=False,  # Don't execute past runs automatically
    tags=["lichess"],
    is_paused_upon_creation=False,
)
def lichess():   
    @task
    def get_last_move_time() -> int:
        url = "http://fastapi:8000/games/get_last_move_played_time"
        response = requests.get(url)
        response.raise_for_status()
        output = response.json()
        logger.info("Last move time received: %s", output["last_move_time"])
        return output['last_move_time']

    @task
    def get_matches(start: int) -> List[dict]:
        """
        Fetch matches from Lichess using the client and a given start time.
        """
        session = setup_berserk_client()
        client = berserk.Client(session)
        games = client.games.export_by_player(settings.lichess_username, since=start, max=100, sort="dateAsc")
        matches = [game for game in games]
        logger.info("Fetched %s matches", len(matches))
        return matches
    
    
    @task_group
    def process_matches(matches: List[dict]):
        """
        Process matches by writing to database, extracting players,
        writing them to the database, extracting moves, writing them to the database
        """


    @task_group
    def process_matches(matches: List[dict]):
        """
        Process matches by writing to database, extracting players,
        writing them to the database, extracting moves, writing them to the database
        """

    @task
    def write_game(match: dict):
        """
        Take match, serialize it, then post to api.
        """
        post_game(match)
        

    @task
    def extract_players(match: dict) -> List[dict]:
        """
        Take match, extract players, return list of players.
        """
        white_player, black_player = extract_players_from_game(match)
        return [white_player, black_player]

    @task
    def write_player(player: dict):
        """
        Use the api and write this player to the database
        """
        post_player(player)

    @task
    def assign_player_to_match(player: dict, game_id: str):
        """
        Take a player object and assign it to a match via api
        """
        post_player_to_match(player, game_id)

    @task
    def extract_moves(match: dict) -> List[dict]:
        """
        Extract moves from lichess object. Return list of dicts.
        """
        move_list = match.get("moves", "").split()
        return move_list

    @task
    def write_moves(moves: List[dict], game_id: str):
        """
        Take the list of moves and assign them to their match via API.
        """
        post_moves_to_match(moves, game_id)

    @task
    def process_match(match: Dict):
        """Process a single match: write the game, players, and moves."""
        # logger.debug("Match: %s", match)
        game_id = match["id"]
        post_game(match)

        # Process players
        white_player, black_player = extract_players_from_game(match)
        post_player(white_player)
        post_player_to_match(white_player, game_id, "white")
        post_player(black_player)
        post_player_to_match(black_player, game_id, "black")

        # Process moves
        move_list = {"moves": match["moves"]}
        post_moves_to_match(move_list, game_id)

    # Define DAG flow
    last_move_time = get_last_move_time()
    matches = get_matches(last_move_time)

    # Use dynamic task mapping to process each match
    process_match.expand(match=matches)

lichess()
