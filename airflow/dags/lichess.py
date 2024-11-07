import logging

import requests
from airflow.decorators import task, dag, task_group
from requests.adapters import HTTPAdapter
from urllib3 import Retry

logger = logging.getLogger(__name__)

import config

settings = config.settings

@dag
def lichess():
    pass
