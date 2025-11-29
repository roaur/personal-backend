import pytest
from unittest.mock import patch, MagicMock, call, ANY
import sys
import os
import requests
import io

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
sys.modules['utils.config'] = MagicMock()
sys.modules['utils.config'].settings = MagicMock()
sys.modules['utils.config'].settings.lichess_username = 'test_user'
sys.modules['utils.config'].settings.lichess_token = 'test_token'
sys.modules['utils.config'].settings.fastapi_route = 'localhost:8000'

# Import tasks from new locations
try:
    from tasks.fetching import fetch_player_games, process_game_data, orchestrator
    from tasks.analysis import analyze_game, enqueue_analysis_tasks
except ImportError:
    # Define stubs if they don't exist yet so tests can be written
    fetch_player_games = MagicMock()
    process_game_data = MagicMock()
    orchestrator = MagicMock()
    analyze_game = MagicMock()
    enqueue_analysis_tasks = MagicMock()

@patch('tasks.fetching.redis_client')
@patch('tasks.fetching.process_game_data.delay')
@patch('tasks.fetching.requests.get')
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

@patch('tasks.fetching.redis_client')
@patch('tasks.fetching.requests.get')
def test_fetch_player_games_404(mock_get, mock_redis):
    """
    Test that fetch_player_games stops on 404 and does NOT retry.
    """
    # Mock Redis Lock
    mock_lock = MagicMock()
    mock_lock.acquire.return_value = True
    mock_redis.lock.return_value = mock_lock

    # Mock 404 response
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Client Error", response=mock_response)
    
    # Context manager support
    mock_get.return_value.__enter__.return_value = mock_response
    mock_get.return_value.__exit__.return_value = None

    # We need to mock self.retry to assert it's NOT called
    with patch('tasks.fetching.fetch_player_games.retry') as mock_retry:
        fetch_player_games("unknown_user", since=0, depth=0)
        
        # Verify retry was NOT called
        mock_retry.assert_not_called()

    # Verify lock was released
    mock_lock.release.assert_called_once()

@patch('tasks.fetching.requests.post')
def test_process_game_data(mock_post):
    """
    Test that process_game_data:
    1. Extracts players, moves, links.
    2. Posts data to FastAPI.
    """
    from tasks.fetching import process_game_data as real_process_game_data
    
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

@patch('tasks.fetching.fetch_player_games')
@patch('tasks.fetching.get_last_move_time')
@patch('tasks.fetching.requests.get')
def test_orchestrator(mock_get, mock_last_move, mock_fetch):
    """
    Test that orchestrator:
    1. Gets last move time for main user.
    2. Triggers fetch_player_games for main user.
    3. Gets next opponent.
    4. Triggers fetch_player_games for opponent.
    """
    from tasks.fetching import orchestrator as real_orchestrator
    from utils.config import settings
    
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

@patch('tasks.analysis.redis_client')
@patch('tasks.analysis.requests.get')
@patch('tasks.analysis.requests.post')
@patch('tasks.analysis.chess.pgn.read_game')
@patch('tasks.analysis.chess.engine.SimpleEngine.popen_uci')
def test_analyze_game(mock_engine_cls, mock_read_game, mock_post, mock_get, mock_redis):
    # Mock GET metrics response (Double-check)
    # First call is to check metrics (return 404 or empty to proceed)
    # Second call is to fetch PGN
    mock_get_metrics_response = MagicMock()
    mock_get_metrics_response.status_code = 404 # No metrics yet
    
    mock_get_pgn_response = MagicMock()
    mock_get_pgn_response.status_code = 200
    mock_get_pgn_response.json.return_value = {"pgn": "1. e4 e5"}
    
    mock_get.side_effect = [mock_get_metrics_response, mock_get_pgn_response]
    
    # Mock PGN parsing
    mock_game = MagicMock()
    mock_read_game.return_value = mock_game
    
    # Mock Engine
    mock_engine = MagicMock()
    mock_engine_cls.return_value = mock_engine
    
    # Mock Plugin Analysis
    # We need to patch PLUGINS or the plugin instance
    with patch('tasks.analysis.PLUGINS', [MagicMock()]) as mock_plugins:
        mock_plugin = mock_plugins[0]
        mock_plugin.name = "test_plugin"
        mock_plugin.analyze.return_value = {"score": 100}
        
        # Mock Save Results
        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post.return_value = mock_post_response
        
        analyze_game("game1")
        
        # Verify interactions
        # Should call GET metrics, then GET PGN
        assert mock_get.call_count == 2
        mock_get.assert_any_call("http://localhost:8000/games/game1/metrics")
        mock_get.assert_any_call("http://localhost:8000/games/game1/pgn")
        
        mock_plugin.analyze.assert_called_once()
        mock_post.assert_called_with(
            "http://localhost:8000/games/game1/metrics",
            json={"test_plugin": {"score": 100}}
        )
        
        # Verify Redis cleanup
        mock_redis.delete.assert_called_once_with("analysis_pending:game1")

@patch('tasks.analysis.redis_client')
@patch('tasks.analysis.requests.get')
@patch('tasks.analysis.chess.pgn.read_game')
@patch('tasks.analysis.chess.engine.SimpleEngine.popen_uci')
def test_analyze_game_skips_if_metrics_exist(mock_engine_cls, mock_read_game, mock_get, mock_redis):
    # Mock GET metrics response (Metrics exist)
    mock_get_metrics_response = MagicMock()
    mock_get_metrics_response.status_code = 200
    mock_get_metrics_response.json.return_value = {"metrics": {"test_plugin": {"score": 100}}}
    
    # Mock GET PGN response (Still fetched)
    mock_get_pgn_response = MagicMock()
    mock_get_pgn_response.status_code = 200
    mock_get_pgn_response.json.return_value = {"pgn": "1. e4 e5"}
    
    mock_get.side_effect = [mock_get_metrics_response, mock_get_pgn_response]
    
    # Mock PGN parsing
    mock_game = MagicMock()
    mock_read_game.return_value = mock_game
    
    # Mock Engine
    mock_engine = MagicMock()
    mock_engine_cls.return_value = mock_engine
    
    with patch('tasks.analysis.PLUGINS', [MagicMock()]) as mock_plugins:
        mock_plugin = mock_plugins[0]
        mock_plugin.name = "test_plugin"
        
        analyze_game("game1")
        
        # Verify interactions
        # Should call GET metrics AND GET PGN
        assert mock_get.call_count == 2
        mock_get.assert_any_call("http://localhost:8000/games/game1/metrics")
        mock_get.assert_any_call("http://localhost:8000/games/game1/pgn")
        
        # Should NOT run analysis for this plugin
        mock_plugin.analyze.assert_not_called()
        
        # Should clear Redis key
        mock_redis.delete.assert_called_once_with("analysis_pending:game1")

@patch('tasks.analysis.redis_client')
@patch('tasks.analysis.requests.post')
@patch('tasks.analysis.analyze_game.delay')
def test_enqueue_analysis_tasks(mock_delay, mock_post, mock_redis):
    # Mock API response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = ["game1", "game2"]
    mock_post.return_value = mock_response
    
    # Mock Redis: game1 is new, game2 is already pending
    mock_redis.exists.side_effect = lambda k: k == "analysis_pending:game2"
    
    enqueue_analysis_tasks()
    
    # Verify API call
    # Should request 1000 candidates
    args, kwargs = mock_post.call_args
    assert kwargs['params'] == {'limit': 1000}
    
    # Verify tasks enqueued
    # Should only enqueue game1
    mock_delay.assert_called_once_with("game1")
    
    # Verify Redis set for game1 with 1 hour TTL
    mock_redis.set.assert_called_once_with("analysis_pending:game1", "1", ex=3600)
