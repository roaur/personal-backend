import logging

from typing import Dict, List, Tuple, Generator
from airflow.decorators import task, dag, task_group
from requests.adapters import HTTPAdapter
from urllib3 import Retry
import berserk
import datetime

from ..lichess_utils import setup_berserk_client
from ..database_utils import are_there_games_already

logger = logging.getLogger(__name__)

MAX_RETRIES = 10
BACKOFF_FACTOR = 2

import config

settings = config.settings

@dag
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
    def get_matches(client: berserk.Client) -> List[dict]:
        games = [{}]
        if are_there_games_already(): # are there games in the database?
            now = datetime.datetime.now()
            yesterday_night = (
                now - datetime.timedelts(days=1)
                ).replace(hour=0, minute=0, second=0, microsecond=0)
            start = berserk.utils.to_millis(yesterday_night)
            games = client.games.export_by_player(settings.lichess_username, since=start)
        else:
            games = client.games.export_by_player(settings.lichess_username)

        return [game for game in games]
    
    @task
    def write_games(matches: List[dict]):
        pass

        


