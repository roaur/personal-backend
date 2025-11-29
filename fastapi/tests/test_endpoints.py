import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime

# =============================================================================
# Game Endpoint Tests
# =============================================================================

@pytest.mark.anyio
async def test_create_game_batch(client):
    with patch("app.crud.create_games_batch", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = []
        response = await client.post("/games/batch", json=[])
        assert response.status_code == 201

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
