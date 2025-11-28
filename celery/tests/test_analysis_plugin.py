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
        item = self.scores[self.index]
        self.index = (self.index + 1) % len(self.scores)
        
        if isinstance(item, tuple):
            score_val, is_mate, mate_moves = item
        else:
            score_val = item
            is_mate = False
            mate_moves = 0
        
        # Mock info dictionary
        info = {
            "score": MagicMock()
        }
        
        # Mock score object
        mock_score = MagicMock()
        mock_score.is_mate.return_value = is_mate
        
        # Handle score(mate_score=...)
        def score_side_effect(mate_score=None):
            if is_mate and mate_score is not None:
                # If it's a mate, return +/- mate_score based on sign of score_val (if provided) or just score_val
                # In our test data, we can use score_val to indicate the "large value"
                # But wait, we passed (0, True, 1). score_val is 0.
                # We need score_val to be consistent with mate sign.
                # Let's say if mate_moves > 0, return mate_score. If < 0, return -mate_score.
                if mate_moves > 0:
                    return mate_score
                elif mate_moves < 0:
                    return -mate_score
                else:
                    return mate_score # Default to positive for mate in 0?
            return score_val

        mock_score.score.side_effect = score_side_effect
        mock_score.mate.return_value = mate_moves
        
        info["score"].white.return_value = mock_score
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

    # Mock scores (in centipawns): 
    # Initial: 30 (0.3)
    # 1. e4: 40 (0.4) -> Swing 0.1
    # 1... e5: 35 (0.35) -> Swing 0.05
    # 2. Nf3: 80 (0.8) -> Swing 0.45
    # 2... Nc6: 70 (0.7) -> Swing 0.1
    # 3. Bc4: 20 (0.2) -> Swing 0.5 (Largest!)
    
    scores = [30, 40, 35, 80, 70, 20] 
    mock_engine = MockEngine(scores)

    result = plugin.analyze(game, mock_engine)

def test_largest_swing_plugin_with_mate():
    plugin = LargestSwingPlugin()
    
    # Create a dummy game
    pgn_text = "1. e4 e5 2. Qh5 Nc6 3. Bc4 Nf6 4. Qxf7#"
    pgn = io.StringIO(pgn_text)
    game = chess.pgn.read_game(pgn)
    
    # Mock scores
    # Initial: 0.3
    # 1. e4: 0.4
    # 1... e5: 0.3
    # 2. Qh5: 0.2 (Bad move usually, but let's say engine thinks so)
    # 2... Nc6: 0.3
    # 3. Bc4: 0.5
    # 3... Nf6: -10.0 (Blunder allowing mate!) -> Swing 10.5
    # 4. Qxf7#: 10.0 (Mate delivered)
    
    # Scores list (raw values/tuples to be processed by MockEngine)
    # We need to update MockEngine to handle "mate" instruction or just pass tuples
    # Let's pass tuples: (score_val, is_mate, mate_moves)
    
    scores = [
        (30, False, 0),   # Initial
        (40, False, 0),   # 1. e4
        (30, False, 0),   # 1... e5
        (20, False, 0),   # 2. Qh5
        (30, False, 0),   # 2... Nc6
        (50, False, 0),   # 3. Bc4
        (0, True, 1),    # 3... Nf6 (Mate in 1 for White, so score is positive)
                          # Wait, if Black moves 3... Nf6 allowing Qxf7#, then AFTER 3... Nf6, it is White to move and White has Mate in 1.
                          # So score is +Mate1.
                          # Previous score was 0.5. New score is Mate in 1 (+10.0). Swing is 9.5.
        (0, True, 0)      # 4. Qxf7# (Mate delivered). Score is +Mate0? Or just winning.
    ]
    
    mock_engine = MockEngine(scores)
    result = plugin.analyze(game, mock_engine)
    
    assert result["swing_eval"] == 9.5
    assert result["ply"] == 6 # 3... Nf6 is 6th ply
    assert result["move_san"] == "Nf6"
    assert result["forced_mate_in"] == 1
    
    # Let's verify the implementation logic in largest_swing.py
    # move_number starts at 0.
    # loop: move_number += 1.
    # So yes, it counts plies.
