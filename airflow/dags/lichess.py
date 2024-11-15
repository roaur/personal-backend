import logging

from typing import Dict, List, Tuple, Generator
from airflow.decorators import task, dag, task_group
from airflow.utils.dates import days_ago
from requests.adapters import HTTPAdapter
import requests
from urllib3 import Retry
import berserk
import datetime

from ..lichess_utils import setup_berserk_client

logger = logging.getLogger(__name__)

MAX_RETRIES = 10
BACKOFF_FACTOR = 2

import config

settings = config.settings

@dag(
    schedule_interval="* * * * *",  # Run every minute
    start_date=days_ago(1),  # Allows the DAG to backfill if needed
    catchup=False,  # Don't execute past runs automatically
    tags=["lichess"],
)
def lichess():

    @task
    def get_client() -> berserk.Client:
        """
        Initialize the berserk client using the Lichess token from settings
        and make the lichess-specific rate-limiting rules as an adapter.
        """
        session = setup_berserk_client()
        client = berserk.Client(session)
        return client
    
    @task
    def get_last_move_time() -> int:
        url = "http://fastapi:8000/games/get_last_move_played_time"
        response = requests.get(url)
        response.raise_for_status()
        output = response.json()
        logger.info("Last move time received: %s", output["last_move_time"])
        return output['last_move_time']

    @task
    def get_matches(client: berserk.Client, start: int) -> List[dict]:
        games = [{}]
        games = client.games.export_by_player(settings.lichess_username, since=start, max=100)
        matches = [game for game in games]
        logger.info("Fetches %s matches", len(matches))
        return matches
    
    @task_group
    def process_matches(matches: List[dict]):
        """
        Process matches by writing to database, extracting players,
        writing them to the database, extracting moves, writing them to the database
        """

        @task
        def write_games(matche: dict):
            """
            Take match, serialize it, then post to api.
            """
            

        @task
        def extract_players(match: dict) -> List[dict]:
            """
            Take match, extract players, return list of players.
            """
            pass

        @task
        def write_players(player: dict):
            """
            Use the api and write this player to the database
            """
            pass

        @task
        def assign_player_to_match(player: dict, game_id: str):
            """
            Take a player object and assign it to a match via api
            """
            pass

    


        


