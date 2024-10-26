# data_transformers.py
from datetime import datetime

def flatten_clock_data(game_data: dict) -> dict:
    """Extracts and flattens 'clock' data into individual fields for the game."""
    if 'clock' in game_data:
        game_data['clock_initial'] = game_data['clock'].get('initial')
        game_data['clock_increment'] = game_data['clock'].get('increment')
        game_data['clock_total_time'] = game_data['clock'].get('totalTime')
        del game_data['clock']  # Remove nested 'clock' after flattening
    return game_data

def extract_players(game_data: dict) -> list[dict]:
    """Extracts player data for association with the game."""
    players = []
    for color, player_info in game_data.get('players', {}).items():
        player = {
            "lichess_id": player_info["user"]["id"],
            "name": player_info["user"].get("name", ""),
            "rating": player_info.get("rating", 0),
            "flair": player_info.get("flair"),
            "color": color,
            "rating_diff": player_info.get("ratingDiff")
        }
        players.append(player)
    return players

def enumerate_moves(game_data: dict) -> list[dict]:
    """Extracts and enumerates moves from the game data."""
    moves = game_data.get("moves", "").split()  # Split moves string into individual moves
    lichess_game_id = game_data["id"]
    
    # Enumerate moves with a move number for each one
    enumerated_moves = [
        {
            "lichess_game_id": lichess_game_id,
            "move_number": i + 1,
            "move": move
        }
        for i, move in enumerate(moves)
    ]
    return enumerated_moves