import pytest
import chess
import chess.pgn
import chess.engine
import io
from analysis.plugins.largest_swing import LargestSwingPlugin
from unittest.mock import MagicMock

# Mock engine to return predictable scores
class MockEngine:
    def __init__(self, scores):
        self.scores = scores
        self.index = 0

    def analyse(self, board, limit):
        score = self.scores[self.index]
        self.index = (self.index + 1) % len(self.scores)
        
        # Mock info dictionary
        info = {
            "score": MagicMock()
        }
        # Mock score().white().score() chain
        info["score"].white.return_value.score.return_value = score
        return info

    def quit(self):
        pass

def test_largest_swing_plugin():
    plugin = LargestSwingPlugin()
    assert plugin.name == "largest_swing"

    # Create a dummy game with 3 moves
    pgn_text = "1. e4 e5 2. Nf3 Nc6 3. Bc4"
    pgn = io.StringIO(pgn_text)
    game = chess.pgn.read_game(pgn)

    # Mock scores: 
    # Initial: 30 (0.3)
    # 1. e4: 40 (0.4) -> Swing 10
    # 1... e5: 35 (0.35) -> Swing 5
    # 2. Nf3: 80 (0.8) -> Swing 45
    # 2... Nc6: 70 (0.7) -> Swing 10
    # 3. Bc4: 20 (0.2) -> Swing 50 (Largest!)
    
    scores = [30, 40, 35, 80, 70, 20] 
    mock_engine = MockEngine(scores)

    result = plugin.analyze(game, mock_engine)

    assert result["swing_eval"] == 50
    assert result["ply"] == 5 # 3. Bc4 is the 5th ply
    assert result["move_san"] == "Bc4"
    assert result["move_uci"] == "f1c4"
    
    # Let's verify the implementation logic in largest_swing.py
    # move_number starts at 0.
    # loop: move_number += 1.
    # So yes, it counts plies.
