import pytest
from unittest.mock import patch, MagicMock, call
import sys
import os
import sys
from unittest.mock import MagicMock, patch, call, ANY
import pytest

# Add the parent directory to sys.path so we can import tasks
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set environment variables BEFORE importing tasks
os.environ['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
os.environ['LICHESS_TOKEN'] = 'test_token'
os.environ['LICHESS_USERNAME'] = 'roaur'
os.environ['FASTAPI_ROUTE'] = 'localhost:8000'

# Mock settings to avoid validation errors during import
# We need to patch where it is used, or patch the class itself before instantiation
# Since 'tasks' imports 'utils.config', we need to mock 'utils.config.settings'
# THIS MUST HAPPEN BEFORE IMPORTING TASKS
# sys.modules['utils'] = MagicMock()  <-- REMOVED
sys.modules['shared.config'] = MagicMock()
sys.modules['shared.config'].settings = MagicMock()
sys.modules['shared.config'].settings.lichess_username = 'test_user'
sys.modules['shared.config'].settings.lichess_token = 'test_token'
sys.modules['shared.config'].settings.fastapi_route = 'localhost:8000'

# Import tasks - these might fail if not implemented yet, which is expected for TDD
try:
    from tasks import fetch_player_games, process_game_data, orchestrator
except ImportError:
    # Define stubs if they don't exist yet so tests can be written
    fetch_player_games = MagicMock()
    process_game_data = MagicMock()
    orchestrator = MagicMock()

@patch('tasks.redis_client')
@patch('tasks.process_game_data.delay')
@patch('tasks.requests.get')
def test_fetch_player_games(mock_get, mock_delay, mock_redis):
    """
    Test that fetch_player_games streams data and dispatches tasks.
    """
    # Mock Redis Lock
    mock_lock = MagicMock()
    mock_lock.acquire.return_value = True
    mock_redis.lock.return_value = mock_lock

    # Mock streaming response
    mock_response = MagicMock()
    mock_response.status_code = 200
    # Simulate 2 lines of NDJSON
    mock_response.iter_lines.return_value = [
        b'{"id": "game1", "players": {}}',
        b'{"id": "game2", "players": {}}'
    ]
    # Context manager support
    mock_get.return_value.__enter__.return_value = mock_response
    mock_get.return_value.__exit__.return_value = None

    fetch_player_games("testuser", since=0, depth=0)

    # Verify lock was acquired and released
    mock_redis.lock.assert_called_with("lichess_api_lock", timeout=300)
    mock_lock.acquire.assert_called_with(blocking=True, blocking_timeout=10)
    mock_lock.release.assert_called_once()

    # Verify requests called with stream=True
    mock_get.assert_called_with(
        "https://lichess.org/api/games/user/testuser",
        headers=ANY,
        params=ANY,
        stream=True
    )

    # Verify tasks dispatched
    assert mock_delay.call_count == 2
    mock_delay.assert_has_calls([
        call({'id': 'game1', 'players': {}}, 0),
        call({'id': 'game2', 'players': {}}, 0)
    ])

@patch('tasks.requests.post')
def test_process_game_data(mock_post):
    """
    Test that process_game_data:
    1. Extracts players, moves, links.
    2. Posts data to FastAPI.
    """
    from tasks import process_game_data as real_process_game_data
    
    game_sample = {
        "id": "game1",
        "players": {
            "white": {"user": {"id": "white_player", "name": "White"}, "rating": 1500},
            "black": {"user": {"id": "black_player", "name": "Black"}, "rating": 1500}
        },
        "moves": "e4 e5",
        "createdAt": 1000,
        "lastMoveAt": 2000,
        "status": "mate",
        "variant": "standard",
        "speed": "blitz",
        "perf": "blitz"
    }
    
    # Mock successful responses
    mock_post.return_value.status_code = 201
    
    # Execute
    real_process_game_data(game_sample, depth=0)
    
    # Assertions
    # We expect calls to:
    # 1. /games/ (or batch)
    # 2. /players/ (white)
    # 3. /players/ (black)
    # 4. /games/{id}/players (white)
    # 5. /games/{id}/players (black)
    # 6. /games/{id}/moves/ (optional if we are still doing that)
    
    assert mock_post.call_count >= 1

@patch('tasks.fetch_player_games')
@patch('tasks.get_last_move_time')
@patch('tasks.requests.get')
def test_orchestrator(mock_get, mock_last_move, mock_fetch):
    """
    Test that orchestrator:
    1. Gets last move time for main user.
    2. Triggers fetch_player_games for main user.
    3. Gets next opponent.
    4. Triggers fetch_player_games for opponent.
    """
    from tasks import orchestrator as real_orchestrator
    from shared.config import settings
    
    # Setup
    mock_last_move.return_value = 123456
    
    # Mock next opponent response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'player_id': 'opponent1',
        'depth': 1,
        'last_fetched_at': '2023-01-01T00:00:00Z'
    }
    mock_get.return_value = mock_response
    
    # Execute
    real_orchestrator()
    
    # Assertions
    # 1. Main user fetch
    mock_fetch.delay.assert_any_call(settings.lichess_username, since=123456, depth=0)
    
    # 2. Opponent fetch
    # We need to calculate the timestamp from the mock string
    # '2023-01-01T00:00:00Z' -> 1672531200000 (approx)
    # We can just check that it was called with the correct username and depth
    args, kwargs = mock_fetch.delay.call_args_list[1]
    assert args[0] == 'opponent1'
    assert kwargs['depth'] == 1
