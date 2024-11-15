import berserk
from config import settings
from typing import Dict, List, Tuple, Generator
import json
import chess
from datetime import datetime
import requests
import time
import logging

from berserk import TokenSession
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class RateLimitingAdapter(HTTPAdapter):
    """
    Custom HTTPAdapter to handle rate-limiting for the Lichess API.
    Retries on HTTP 429 responses with a delay.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_retries = Retry(
            total=5,  # Maximum number of retries
            backoff_factor=75,  # Wait 75 seconds for 429 responses
            status_forcelist=[429],  # Retry on Too Many Requests
        )

    def send(self, request, **kwargs):
        response = super().send(request, **kwargs)
        if response.status_code == 429:
            logger.info("Rate limit reached. Waiting for 60 seconds...")
        return response


def setup_berserk_client() -> TokenSession:
    """
    Set up Berserk's TokenSession with a custom HTTPAdapter.
    """
    session = TokenSession(settings.lichess_token)
    adapter = RateLimitingAdapter()
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def json_serializer(json_to_post: dict) -> dict:
    if isinstance(json_to_post, datetime):
        return json_to_post.isoformat()

def parse_and_enumerate_moves(game_id: str, moves: list[str]) -> list[dict]:
    """
    Parses and enumerates a list of chess moves.
    """
    board = chess.Board()  # Create a new board instance
    move_data = []

    for move_number, move in enumerate(moves, start=1):
        try:
            board.push_san(move)  # Push the move to the board (validates the move)
            move_data.append({
                "game_id": game_id,
                "move_number": move_number,
                "move": move,
            })
        except ValueError as e:
            raise ValueError(f"Invalid move '{move}' at move number {move_number}: {str(e)}")

    return move_data

def format_match_core(game: Dict) -> Dict:
    """
    Extract core game information for the main game table.
    """
    return {
        "game_id": game["id"],
        "rated": game.get("rated", False),
        "variant": game["variant"],
        "speed": game["speed"],
        "perf": game["perf"],
        "created_at": game["createdAt"],
        "last_move_at": game["lastMoveAt"],
        "status": game["status"],
        "source": game.get("source", ""),
        "winner": game.get("winner", ""),
        "pgn": game.get("pgn", ""),
        "clock_initial": game.get("clock", {}).get("initial", 0),
        "clock_increment": game.get("clock", {}).get("increment", 0),
        "clock_total_time": game.get("clock", {}).get("totalTime", 0)
    }

def format_players(game: Dict) -> List[Dict]:
    """
    Extract player information, returning a list of player records.
    """
    players_data = []
    for color, player_info in game["players"].items():
        players_data.append({
            "lichess_game_id": game["id"],
            "player_lichess_id": player_info["user"]["id"],
            "name": player_info["user"]["name"],
            "color": color,
            "rating": player_info.get("rating"),
            "rating_diff": player_info.get("ratingDiff", 0),
            "flair": player_info.get("flair")
        })
    return players_data

def format_moves(game: Dict) -> List[Dict]:
    """
    Extract moves as individual records with move numbers.
    """
    moves_list = game["moves"].split(" ")
    return [
        {
            "lichess_game_id": game["id"],
            "move_number": i + 1,
            "move": move
        }
        for i, move in enumerate(moves_list)
    ]

def extract_moves_from_game(game: dict):
    """Extract individual moves from the 'moves' field in the game object."""
    moves_str = game.get('moves', '')
    if not moves_str:
        raise ValueError("No moves found in the game object.")
    
    # Split the moves string by spaces
    moves = moves_str.split(' ')
    return moves

def extract_players_from_game(game: dict):
    """Extract the white and black player information from the game object."""
    
    game_id = game.get('game_id', '')

    players = game.get('players', {})
    if not players:
        raise ValueError("No players found in the game object.")
    
    # Extract white player
    white_player = {
        "lichess_id": players['white']['user']['id'],
        "name": players['white']['user']['name'],
        "rating": players['white']['rating'],
        "rating_diff": players['white'].get('ratingDiff', 0),
        "flair": players['white'].get('flair', None)
    }
    
    # Extract black player
    black_player = {
        "lichess_id": players['black']['user']['id'],
        "name": players['black']['user']['name'],
        "rating": players['black']['rating'],
        "rating_diff": players['black'].get('ratingDiff', 0),
        "flair": players['black'].get('flair', None)
    }

    return game_id, white_player, black_player

def link_players_to_game(game: dict):
    """Prepare the many-to-many link data for players and game from the game object."""
    game_id = game.get('id')
    if not game_id:
        raise ValueError("No game ID found in the game object.")
    
    white_player, black_player = extract_players_from_game(game)

    # Prepare the link data for white and black players
    white_game_player = {
        "lichess_game_id": game_id,
        "player_id": white_player['lichess_id'],
        "color": "white",
        "rating_diff": white_player['rating_diff'],
    }

    black_game_player = {
        "lichess_game_id": game_id,
        "player_id": black_player['lichess_id'],
        "color": "black",
        "rating_diff": black_player['rating_diff'],
    }

    return white_game_player, black_game_player


def post_with_retry(url, data, retries=3, delay=2):
    for attempt in range(retries):
        response = requests.post(url, json=data)
        if response.status_code == 201:
            return response
        else:
            print(f"Failed to insert data: {response.status_code} - {response.text}. Retrying...")
            time.sleep(delay)
    raise Exception(f"Failed to insert data after {retries} attempts.")


def post_game(game: dict):
    url = "http://localhost:8000/games/"
    post_with_retry(url, game)