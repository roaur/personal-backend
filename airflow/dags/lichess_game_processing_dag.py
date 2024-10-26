from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime
from utils.lichess_utils import (
    download_games_batch,
    parse_game,
    extract_moves_from_game,
    extract_players_from_game,
    link_players_to_game,
    post_game,
    post_with_retry
)

# Function to download games in batch and pass the data to downstream tasks
def download_games(**context):
    games = download_games_batch(username='roaur', batch_size=100)
    for batch in games:
        for game in batch:
            game_data = parse_game(game)  # Parse the game data
            context['ti'].xcom_push(key='game_data', value=game_data)

# Function to send game data to FastAPI
def post_game_data(**context):
    game_data = context['ti'].xcom_pull(key='game_data')
    post_game(game_data)  # Send to FastAPI

# Function to send players data to FastAPI
def post_player_data(**context):
    game_data = context['ti'].xcom_pull(key='game_data')
    white_player, black_player = extract_players_from_game(game_data)
    
    # Post the white player data
    post_with_retry("http://localhost:8000/players/", white_player)
    # Post the black player data
    post_with_retry("http://localhost:8000/players/", black_player)

# Function to send moves data to FastAPI
def post_moves_data(**context):
    game_data = context['ti'].xcom_pull(key='game_data')
    moves = extract_moves_from_game(game_data)
    
    for i, move in enumerate(moves):
        move_data = {
            "lichess_game_id": game_data['lichess_game_id'],
            "move_number": i + 1,
            "move": move
        }
        post_with_retry(f"http://localhost:8000/games/{game_data['lichess_game_id']}/moves/", move_data)

# Define the Airflow DAG
with DAG('lichess_game_processing', start_date=datetime(2024, 1, 1), schedule_interval='@daily', catchup=False) as dag:

    # Download games
    download_task = PythonOperator(
        task_id='download_games',
        python_callable=download_games,
        provide_context=True
    )

    # Post game data
    post_game_task = PythonOperator(
        task_id='post_game_data',
        python_callable=post_game_data,
        provide_context=True
    )

    # Post player data
    post_player_task = PythonOperator(
        task_id='post_player_data',
        python_callable=post_player_data,
        provide_context=True
    )

    # Post moves data
    post_moves_task = PythonOperator(
        task_id='post_moves_data',
        python_callable=post_moves_data,
        provide_context=True
    )

    # Set task dependencies
    download_task >> post_game_task >> post_player_task >> post_moves_task
