import berserk
import json
import requests
import time


def validate_game_object(game):
    """Ensure the game object is a valid dictionary."""
    if isinstance(game, str):
        # If the input is a string, try to parse it as JSON
        try:
            game = json.loads(game)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON string passed as game object.")
    
    if not isinstance(game, dict):
        raise ValueError("Game object must be a dictionary.")
    
    return game


def download_lichess_games(token: str, username: str, max_games: int = 100):
    """Download games for a given Lichess user using the Berserk API."""
    with open('./.lichess.token') as f:
        token = f.read()

    session = berserk.TokenSession(token)
    client = berserk.Client(session=session)
    
    games = client.games.export_by_player(username, max=max_games)
    return list(games)


# Download games in batches from Berserk generator
def download_games_batch(username, batch_size=100):
    with open('./.lichess.token') as f:
        token = f.read()
    client = berserk.Client(token=token)
    game_generator = client.games.export_by_player(username)
    batch = []
    
    for game in game_generator:
        batch.append(game)
        if len(batch) == batch_size:
            yield batch  # Return the batch once it's full
            batch = []

    if batch:  # If there's a partial batch left, yield it
        yield batch


def parse_game(game):
    """Parse individual game details from Lichess."""
    return {
        "lichess_game_id": game['id'],
        "rated": game.get('rated', False),
        "variant": game['variant'],
        "speed": game['speed'],
        "perf": game['perf'],
        "created_at": game['createdAt'],
        "last_move_at": game['lastMoveAt'],
        "status": game['status'],
        "source": game.get('source', ''),
        "winner": game.get('winner', ''),
        "pgn": game.get('pgn', ''),
        "clock_initial": game.get('clock', {}).get('initial', 0),
        "clock_increment": game.get('clock', {}).get('increment', 0),
        "clock_total_time": game.get('clock', {}).get('totalTime', 0)
    }

def extract_moves_from_game(game: dict):
    """Extract individual moves from the 'moves' field in the game object."""
    validate_game_object(game)
    
    moves_str = game.get('moves', '')
    if not moves_str:
        raise ValueError("No moves found in the game object.")
    
    # Split the moves string by spaces
    moves = moves_str.split(' ')
    return moves

def extract_players_from_game(game: dict):
    """Extract the white and black player information from the game object."""
    validate_game_object(game)
    
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

    return white_player, black_player

def link_players_to_game(game: dict):
    """Prepare the many-to-many link data for players and game from the game object."""
    validate_game_object(game)
    
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