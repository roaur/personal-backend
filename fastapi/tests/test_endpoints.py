import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime

# =============================================================================
# Game Endpoint Tests
# =============================================================================

@pytest.mark.anyio
async def test_create_game_batch(client):
    """Test batch game creation with empty array"""
    with patch("app.crud.create_games_batch", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = []
        response = await client.post("/games/batch", json=[])
        assert response.status_code == 201
        assert response.json() == []
        mock_create.assert_called_once()

@pytest.mark.anyio
async def test_create_game_batch_multiple(client):
    """Test batch game creation with multiple games"""
    with patch("app.crud.create_games_batch", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = [
            {
                "game_id": "game1",
                "rated": True,
                "variant": "standard",
                "speed": "blitz",
                "perf": "blitz",
                "created_at": datetime.now(),
                "last_move_at": datetime.now(),
                "status": "mate",
                "source": "lichess",
                "winner": "white",
                "pgn": "1. e4 e5",
                "clock_initial": 180,
                "clock_increment": 0,
                "clock_total_time": 180
            },
            {
                "game_id": "game2",
                "rated": False,
                "variant": "standard",
                "speed": "rapid",
                "perf": "rapid",
                "created_at": datetime.now(),
                "last_move_at": datetime.now(),
                "status": "resign",
                "source": "lichess",
                "winner": "black",
                "pgn": "1. d4 d5",
                "clock_initial": 600,
                "clock_increment": 5,
                "clock_total_time": 610
            }
        ]
        payload = [
            {
                "game_id": "game1",
                "rated": True,
                "variant": "standard",
                "speed": "blitz",
                "perf": "blitz",
                "created_at": datetime.now().isoformat(),
                "last_move_at": datetime.now().isoformat(),
                "status": "mate",
                "source": "lichess",
                "clock": {
                    "initial": 180,
                    "increment": 0,
                    "total_time": 180
                }
            },
            {
                "game_id": "game2",
                "rated": False,
                "variant": "standard",
                "speed": "rapid",
                "perf": "rapid",
                "created_at": datetime.now().isoformat(),
                "last_move_at": datetime.now().isoformat(),
                "status": "resign",
                "source": "lichess",
                "clock": {
                    "initial": 600,
                    "increment": 5,
                    "total_time": 610
                }
            }
        ]
        response = await client.post("/games/batch", json=payload)

        assert response.status_code == 201
        assert len(response.json()) == 2
        assert response.json()[0]["game_id"] == "game1"
        assert response.json()[1]["game_id"] == "game2"



@pytest.mark.anyio
async def test_create_game(client):
    with patch("app.crud.create_game", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = {
            "game_id": "test1234",
            "rated": True,
            "variant": "standard",
            "speed": "blitz",
            "perf": "blitz",
            "created_at": datetime.now(),
            "last_move_at": datetime.now(),
            "status": "mate",
            "source": "lichess",
            "winner": "white",
            "pgn": "1. e4 e5",
            "clock_initial": 180,
            "clock_increment": 0,
            "clock_total_time": 180
        }
        payload = {
            "game_id": "test1234",
            "rated": True,
            "variant": "standard",
            "speed": "blitz",
            "perf": "blitz",
            "created_at": datetime.now().isoformat(),
            "last_move_at": datetime.now().isoformat(),
            "status": "mate",
            "source": "lichess",
            "winner": "white",
            "pgn": "1. e4 e5",
            "clock": {
                "initial": 180,
                "increment": 0,
                "total_time": 180
            }
        }
        response = await client.post("/games/", json=payload)
        assert response.status_code == 201
        
        # Verify full response structure
        data = response.json()
        assert data["game_id"] == "test1234"
        assert data["variant"] == "standard"
        assert data["rated"] is True
        assert data["winner"] == "white"
        assert data["speed"] == "blitz"
        assert data["perf"] == "blitz"
        assert data["status"] == "mate"
        assert data["source"] == "lichess"
        assert data["pgn"] == "1. e4 e5"
        
        # Verify mock was called correctly
        mock_create.assert_called_once()


@pytest.mark.anyio
async def test_get_games(client):
    with patch("app.crud.get_games", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = [
            {
                "game_id": "test1234",
                "rated": True,
                "variant": "standard",
                "speed": "blitz",
                "perf": "blitz",
                "created_at": datetime.now(),
                "last_move_at": datetime.now(),
                "status": "mate",
                "source": "lichess",
                "winner": "white",
                "pgn": "1. e4 e5",
                "clock_initial": 180,
                "clock_increment": 0,
                "clock_total_time": 180
            }
        ]
        response = await client.get("/games/")
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["game_id"] == "test1234"

@pytest.mark.anyio
async def test_get_games_with_pagination(client):
    """Test game retrieval with custom pagination parameters"""
    with patch("app.crud.get_games", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = []
        response = await client.get("/games/?skip=10&limit=5")
        assert response.status_code == 200
        # Verify skip and limit were passed correctly
        mock_get.assert_called_once()
        assert mock_get.call_args[1]["skip"] == 10
        assert mock_get.call_args[1]["limit"] == 5

@pytest.mark.anyio
async def test_get_games_pagination_boundaries(client):
    """Test edge cases for pagination"""
    with patch("app.crud.get_games", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = []
        # Test limit=0
        response = await client.get("/games/?skip=0&limit=0")
        assert response.status_code == 200


@pytest.mark.anyio
async def test_create_game_invalid_data(client):
    """Test game creation with missing required fields"""
    payload = {"game_id": "test123"}  # Missing other required fields
    response = await client.post("/games/", json=payload)
    assert response.status_code == 422

@pytest.mark.anyio
async def test_create_game_invalid_types(client):
    """Test game creation with invalid data types"""
    payload = {
        "game_id": "test1234",
        "rated": "not_a_boolean",  # Should be boolean
        "variant": "standard",
        "speed": "blitz",
        "perf": "blitz",
        "created_at": datetime.now().isoformat(),
        "last_move_at": datetime.now().isoformat(),
        "status": "mate",
        "source": "lichess"
    }
    response = await client.post("/games/", json=payload)
    assert response.status_code == 422

@pytest.mark.anyio
async def test_get_last_move_time(client):
    with patch("app.crud.get_last_move_time", new_callable=AsyncMock) as mock:
        mock.return_value = {"last_move_time": 1234567890}
        response = await client.get("/games/get_last_move_played_time")
        assert response.status_code == 200
        assert response.json()["last_move_time"] == 1234567890

@pytest.mark.anyio
async def test_get_last_move_time_for_player(client):
    with patch("app.crud.get_last_move_time_for_player", new_callable=AsyncMock) as mock:
        mock.return_value = 9876543210
        response = await client.get("/games/get_last_move_played_time/test_player")
        assert response.status_code == 200
        assert response.json()["last_move_time"] == 9876543210

@pytest.mark.anyio
async def test_add_moves(client):
    with patch("app.utils.parse_and_enumerate_moves") as mock_parse, \
         patch("app.crud.add_moves", new_callable=AsyncMock) as mock_add:
        mock_parse.return_value = []
        mock_add.return_value = []
        response = await client.post("/games/test123/moves/", json={"moves": "e4 e5"})
        assert response.status_code == 201
        # Verify parser was called with correct arguments
        mock_parse.assert_called_once_with("test123", ["e4", "e5"], "standard", None)

@pytest.mark.anyio
async def test_add_moves_invalid_format(client):
    """Test add_moves with invalid move format - should return empty array"""
    with patch("app.utils.parse_and_enumerate_moves") as mock_parse:
        mock_parse.side_effect = ValueError("Invalid move: xyz")
        response = await client.post(
            "/games/test123/moves/", 
            json={"moves": "xyz invalid"}
        )
        # Returns empty array on ValueError (line 124 in main.py)
        assert response.status_code == 201
        assert response.json() == []

@pytest.mark.anyio
async def test_add_moves_with_variant(client):
    """Test add_moves with chess variant"""
    with patch("app.utils.parse_and_enumerate_moves") as mock_parse, \
         patch("app.crud.add_moves", new_callable=AsyncMock) as mock_add:
        mock_parse.return_value = []
        mock_add.return_value = []
        
        response = await client.post(
            "/games/test123/moves/",
            json={
                "moves": "e4 e5 Nf3",
                "variant": "chess960"
            }
        )
        
        assert response.status_code == 201
        # Verify variant was passed to parser
        mock_parse.assert_called_once_with(
            "test123", 
            ["e4", "e5", "Nf3"], 
            "chess960",
            None
        )

@pytest.mark.anyio
async def test_add_moves_with_initial_fen(client):
    """Test add_moves with custom initial FEN"""
    with patch("app.utils.parse_and_enumerate_moves") as mock_parse, \
         patch("app.crud.add_moves", new_callable=AsyncMock) as mock_add:
        mock_parse.return_value = []
        mock_add.return_value = []
        
        custom_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        response = await client.post(
            "/games/test123/moves/",
            json={
                "moves": "e4 e5",
                "variant": "standard",
                "initial_fen": custom_fen
            }
        )
        
        assert response.status_code == 201
        # Verify initial_fen was passed to parser
        mock_parse.assert_called_once_with(
            "test123", 
            ["e4", "e5"], 
            "standard",
            custom_fen
        )

@pytest.mark.anyio
async def test_get_game_pgn(client):
    with patch("app.crud.get_game_pgn", new_callable=AsyncMock) as mock:
        mock.return_value = "1. e4 e5"
        response = await client.get("/games/test123/pgn")
        assert response.status_code == 200
        assert response.json()["pgn"] == "1. e4 e5"

@pytest.mark.anyio
async def test_get_game_pgn_not_found(client):
    with patch("app.crud.get_game_pgn", new_callable=AsyncMock) as mock:
        mock.return_value = None
        response = await client.get("/games/nonexistent/pgn")
        assert response.status_code == 404

# =============================================================================
# Player Endpoint Tests
# =============================================================================

@pytest.mark.anyio
async def test_create_players_batch(client):
    with patch("app.crud.create_players_batch", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = []
        response = await client.post("/players/batch", json=[])
        assert response.status_code == 201

@pytest.mark.anyio
async def test_create_player(client):
    with patch("app.crud.create_player", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = {
            "player_id": "test_player",
            "name": "Test Player"
        }
        payload = {
            "player_id": "test_player",
            "name": "Test Player"
        }
        response = await client.post("/players/", json=payload)
        assert response.status_code == 201
        assert response.json()["player_id"] == "test_player"

@pytest.mark.anyio
async def test_create_player_invalid_data(client):
    """Test player creation with missing required fields"""
    payload = {}  # Missing required fields
    response = await client.post("/players/", json=payload)
    assert response.status_code == 422


@pytest.mark.anyio
async def test_get_next_player_to_process(client):
    with patch("app.crud.get_next_player_to_process", new_callable=AsyncMock) as mock:
        mock.return_value = {
            "player_id": "test_player",
            "name": "Test",
            "depth": 1,
            "last_move_time": 123456
        }
        response = await client.get("/players/process/next")
        assert response.status_code == 200
        assert response.json()["player_id"] == "test_player"

@pytest.mark.anyio
async def test_get_next_player_to_process_not_found(client):
    with patch("app.crud.get_next_player_to_process", new_callable=AsyncMock) as mock:
        mock.return_value = None
        response = await client.get("/players/process/next")
        assert response.status_code == 404

@pytest.mark.anyio
async def test_update_player_fetched(client):
    with patch("app.crud.update_player_fetched_at", new_callable=AsyncMock) as mock:
        mock.return_value = None
        response = await client.put("/players/test_player/fetched")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

@pytest.mark.anyio
async def test_get_player(client):
    with patch("app.crud.get_player_by_lichess_id", new_callable=AsyncMock) as mock:
        mock.return_value = {"player_id": "test", "name": "Test Player"}
        response = await client.get("/players/test")
        assert response.status_code == 200

@pytest.mark.anyio
async def test_get_player_not_found(client):
    with patch("app.crud.get_player_by_lichess_id", new_callable=AsyncMock) as mock:
        mock.return_value = None
        response = await client.get("/players/nonexistent")
        assert response.status_code == 404

# =============================================================================
# Game-Player Link Tests
# =============================================================================

@pytest.mark.anyio
async def test_add_player_to_game(client):
    with patch("app.crud.add_player_to_game", new_callable=AsyncMock) as mock:
        mock.return_value = {
            "game_id": "test123",
            "player_id": "player1",
            "color": "white",
            "rating": 1500
        }
        payload = {
            "game_id": "test123",
            "player_id": "player1",
            "color": "white",
            "rating": 1500
        }
        response = await client.post("/games/test123/players/", json=payload)
        assert response.status_code == 201
        # Verify response fields
        data = response.json()
        assert data["game_id"] == "test123"
        assert data["player_id"] == "player1"
        assert data["color"] == "white"
        assert data["rating"] == 1500



@pytest.mark.anyio
async def test_add_players_batch(client):
    with patch("app.crud.add_players_to_games_batch", new_callable=AsyncMock) as mock:
        mock.return_value = []
        response = await client.post("/games/players/batch", json=[])
        assert response.status_code == 201

@pytest.mark.anyio
async def test_get_players_from_game(client):
    with patch("app.crud.get_players_from_game", new_callable=AsyncMock) as mock:
        mock.return_value = []
        response = await client.get("/games/test123/players")
        assert response.status_code == 200

# =============================================================================
# Analysis Endpoint Tests
# =============================================================================

@pytest.mark.anyio
async def test_upsert_game_metrics(client):
    with patch("app.crud.upsert_game_metrics", new_callable=AsyncMock) as mock:
        mock.return_value = {
            "id": 1,
            "game_id": "test123",
            "metrics": {"test": "data"}
        }
        response = await client.post("/games/test123/metrics", json={"test": "data"})
        assert response.status_code == 200

@pytest.mark.anyio
async def test_get_game_metrics(client):
    with patch("app.crud.get_game_metrics", new_callable=AsyncMock) as mock:
        mock.return_value = {
            "id": 1,
            "game_id": "test123",
            "metrics": {"test": "data"}
        }
        response = await client.get("/games/test123/metrics")
        assert response.status_code == 200
        assert response.json()["metrics"]["test"] == "data"

@pytest.mark.anyio
async def test_get_game_metrics_not_found(client):
    with patch("app.crud.get_game_metrics", new_callable=AsyncMock) as mock:
        mock.return_value = None
        response = await client.get("/games/nonexistent/metrics")
        assert response.status_code == 200  # Returns null, not 404
        assert response.json() is None

@pytest.mark.anyio
async def test_get_games_needing_analysis(client):
    with patch("app.crud.get_games_needing_analysis", new_callable=AsyncMock) as mock:
        mock.return_value = ["game1", "game2", "game3"]
        response = await client.post("/games/analysis/queue", json=["plugin1", "plugin2"])
        assert response.status_code == 200
        assert len(response.json()) == 3
        # Verify plugins were passed correctly
        mock.assert_called_once()
        call_args = mock.call_args[0]
        assert call_args[1] == ["plugin1", "plugin2"]

@pytest.mark.anyio
async def test_get_games_needing_analysis_with_limit(client):
    """Test analysis queue with custom limit parameter"""
    with patch("app.crud.get_games_needing_analysis", new_callable=AsyncMock) as mock:
        mock.return_value = ["game1", "game2"]
        
        response = await client.post(
            "/games/analysis/queue?limit=50",
            json=["stockfish", "opening_analyzer"]
        )
        
        assert response.status_code == 200
        assert len(response.json()) == 2
        
        # Verify correct arguments were passed (db, plugins, limit)
        mock.assert_called_once()
        call_args = mock.call_args[0]
        assert call_args[1] == ["stockfish", "opening_analyzer"]  # plugins
        assert call_args[2] == 50  # limit parameter


@pytest.mark.anyio
async def test_get_games_needing_analysis_empty(client):
    """Test analysis queue with no games needing analysis"""
    with patch("app.crud.get_games_needing_analysis", new_callable=AsyncMock) as mock:
        mock.return_value = []
        response = await client.post("/games/analysis/queue", json=["plugin1"])
        assert response.status_code == 200
        assert response.json() == []

@pytest.mark.anyio
async def test_get_games_needing_analysis_single_plugin(client):
    """Test analysis queue with single plugin"""
    with patch("app.crud.get_games_needing_analysis", new_callable=AsyncMock) as mock:
        mock.return_value = ["game1"]
        response = await client.post("/games/analysis/queue", json=["stockfish"])
        assert response.status_code == 200
        assert response.json() == ["game1"]
        # Verify single plugin was passed correctly
        mock.assert_called_once()
        assert mock.call_args[0][1] == ["stockfish"]

