import psycopg
import requests
from config import settings
from typing import Dict

# Database Configurations
DATABASE_URL = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}/{settings.POSTGRES_DB}"

# 1. Database Insertion with Psycopg
def connect_db():
    """Establish a connection to the PostgreSQL database."""
    return psycopg.connect(DATABASE_URL)

def insert_game_psycopg(game_data: Dict):
    """Insert a game record into the database using psycopg."""
    with connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO chess.games (lichess_game_id, rated, variant, speed, perf, created_at, last_move_at, status, source, winner, pgn, clock_initial, clock_increment, clock_total_time)
                VALUES (%(lichess_game_id)s, %(rated)s, %(variant)s, %(speed)s, %(perf)s, %(created_at)s, %(last_move_at)s, %(status)s, %(source)s, %(winner)s, %(pgn)s, %(clock_initial)s, %(clock_increment)s, %(clock_total_time)s)
                ON CONFLICT (lichess_game_id) DO UPDATE
                SET rated = EXCLUDED.rated,
                    variant = EXCLUDED.variant,
                    speed = EXCLUDED.speed,
                    perf = EXCLUDED.perf,
                    created_at = EXCLUDED.created_at,
                    last_move_at = EXCLUDED.last_move_at,
                    status = EXCLUDED.status,
                    source = EXCLUDED.source,
                    winner = EXCLUDED.winner,
                    pgn = EXCLUDED.pgn,
                    clock_initial = EXCLUDED.clock_initial,
                    clock_increment = EXCLUDED.clock_increment,
                    clock_total_time = EXCLUDED.clock_total_time;
            """, game_data)
        conn.commit()

# 2. API Insertion
def post_game_api(game_data: Dict):
    """Post game data to the API."""
    url = f"{settings.API_BASE_URL}/games/"
    response = requests.post(url, json=game_data)
    if response.status_code == 201:
        print(f"Game {game_data['lichess_game_id']} posted successfully.")
    else:
        print(f"Failed to post game {game_data['lichess_game_id']}: {response.status_code} - {response.text}")

# Additional utility for handling either option
def save_game(game_data: Dict, use_api: bool = False):
    """
    Save game data using either psycopg or API, depending on the `use_api` flag.
    """
    if use_api:
        post_game_api(game_data)
    else:
        insert_game_psycopg(game_data)