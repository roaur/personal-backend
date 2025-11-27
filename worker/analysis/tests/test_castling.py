import pytest
from worker.analysis.plugins.castling import CastlingPlugin

def test_castling_plugin():
    plugin = CastlingPlugin()
    
    # Simple PGN where white castles kingside and black queenside
    # 1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. O-O d6 5. d3 Nf6 6. Nc3 O-O
    pgn = "1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. O-O d6 5. d3 Nf6 6. Nc3 O-O"
    
    game = {"pgn": pgn}
    features = plugin.process(game)
    
    white_castling = next(f for f in features if f["feature_name"] == "white_castling")
    assert white_castling["feature_value"] == "Kingside"
    
    black_castling = next(f for f in features if f["feature_name"] == "black_castling")
    assert black_castling["feature_value"] == "Kingside"

def test_no_castling():
    plugin = CastlingPlugin()
    pgn = "1. e4 e5 2. Nf3 Nc6"
    game = {"pgn": pgn}
    features = plugin.process(game)
    
    white_castling = next(f for f in features if f["feature_name"] == "white_castling")
    assert white_castling["feature_value"] == "None"
