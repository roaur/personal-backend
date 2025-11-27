import pytest
import requests
import responses
from unittest.mock import patch
from worker.utils.lichess_utils import (
    RateLimitingAdapter,
    extract_players_from_game,
    format_match_core
)

class TestRateLimiting:
    @responses.activate
    def test_rate_limiting_adapter_retries(self):
        """
        Verify that the RateLimitingAdapter retries on 429 errors.
        """
        url = "https://lichess.org/api/account"
        
        # Mock 429 response then 200 response
        responses.add(responses.GET, url, status=429)
        responses.add(responses.GET, url, status=429)
        responses.add(responses.GET, url, status=200, json={"id": "testuser"})

        session = requests.Session()
        adapter = RateLimitingAdapter()
        session.mount("https://", adapter)

        # We patch time.sleep to avoid actually waiting during tests
        with patch("time.sleep") as mock_sleep:
            response = session.get(url)
            
            assert response.status_code == 200
            assert response.json() == {"id": "testuser"}
            
            # Verify that retries occurred (consumed 3 responses)
            assert len(responses.calls) == 3

    @responses.activate
    def test_rate_limiting_adapter_gives_up(self):
        """
        Verify that it eventually raises an error if 429s persist.
        """
        url = "https://lichess.org/api/account"
        
        # Mock persistent 429s
        responses.add(responses.GET, url, status=429)

        session = requests.Session()
        adapter = RateLimitingAdapter()
        session.mount("https://", adapter)

        with patch("time.sleep"):
            # Requests raises RetryError (ConnectionError) after max retries
            with pytest.raises(requests.exceptions.RetryError):
                session.get(url)

class TestDataParsing:
    def test_extract_players_from_game(self):
        game_data = {
            "players": {
                "white": {
                    "user": {"id": "white_player", "name": "White Player"},
                    "rating": 1500,
                    "ratingDiff": 10
                },
                "black": {
                    "user": {"id": "black_player", "name": "Black Player"},
                    "rating": 1600,
                    "ratingDiff": -5
                }
            }
        }
        
        white, black = extract_players_from_game(game_data)
        
        assert white["player_id"] == "white_player"
        assert white["name"] == "White Player"
        assert white["rating"] == 1500
        
        assert black["player_id"] == "black_player"
        assert black["name"] == "Black Player"
        assert black["rating"] == 1600

    def test_format_match_core(self):
        game_data = {
            "id": "game123",
            "rated": True,
            "variant": "standard",
            "speed": "blitz",
            "perf": "blitz",
            "createdAt": 1600000000000,
            "lastMoveAt": 1600000600000,
            "status": "mate",
            "winner": "white",
            "moves": "e4 e5",
            "clock": {
                "initial": 300,
                "increment": 3,
                "totalTime": 300
            }
        }
        
        formatted = format_match_core(game_data)
        
        assert formatted["game_id"] == "game123"
        assert formatted["rated"] is True
        assert formatted["variant"] == "standard"
        assert formatted["clock"]["initial"] == 300
