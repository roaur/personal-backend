import chess.pgn
import io
from typing import Dict, Any, List
from worker.analysis.plugins.base import AnalysisPlugin

class CastlingPlugin(AnalysisPlugin):
    """
    Analyzes the game to see which side castled.
    """
    
    @property
    def name(self) -> str:
        return "castling"

    def process(self, game: Dict[str, Any]) -> List[Dict[str, Any]]:
        features = []
        pgn_text = game.get('pgn')
        
        if not pgn_text:
            return features

        try:
            # Parse PGN
            pgn = chess.pgn.read_game(io.StringIO(pgn_text))
            board = pgn.board()
            
            white_castled = "None"
            black_castled = "None"

            # Iterate through moves to find castling
            for move in pgn.mainline_moves():
                if board.is_castling(move):
                    if board.turn == chess.WHITE:
                        if board.is_kingside_castling(move):
                            white_castled = "Kingside"
                        else:
                            white_castled = "Queenside"
                    else:
                        if board.is_kingside_castling(move):
                            black_castled = "Kingside"
                        else:
                            black_castled = "Queenside"
                board.push(move)

            features.append({
                "feature_name": "white_castling",
                "feature_value": white_castled,
                "feature_type": "categorical"
            })
            
            features.append({
                "feature_name": "black_castling",
                "feature_value": black_castled,
                "feature_type": "categorical"
            })

        except Exception as e:
            # Log error but don't crash
            print(f"Error parsing PGN: {e}")
            
        return features
