from analysis.base import AnalysisPlugin
import chess
import chess.engine
import chess.pgn

class LargestSwingPlugin(AnalysisPlugin):
    @property
    def name(self) -> str:
        return "largest_swing"

    def analyze(self, game: chess.pgn.Game, engine: chess.engine.SimpleEngine) -> dict:
        board = game.board()
        largest_swing = 0.0
        swing_move = 0
        best_move_san = None
        best_move_uci = None
        
        # Initial position score (usually 0.3 or similar, but let's start tracking from move 1)
        # Or we can analyze the initial position too.
        # Let's analyze initial position.
        info = engine.analyse(board, chess.engine.Limit(time=0.1))
        prev_score = info["score"].white().score(mate_score=10000)
        
        # Iterate through all moves
        node = game
        move_number = 0
        
        while not node.is_end():
            next_node = node.variation(0)
            move = next_node.move
            board.push(move)
            move_number += 1
            
            # Analyze position
            info = engine.analyse(board, chess.engine.Limit(time=0.5))
            score = info["score"].white().score(mate_score=10000)
            
            # Calculate swing (absolute difference)
            # We care about the magnitude of the change in evaluation.
            swing = abs(score - prev_score)
            
            # Convert centipawns to pawns for easier reading? 
            # Or keep in centipawns. Let's keep in centipawns (integer usually, but score() returns int).
            # Wait, score() returns int.
            
            if swing > largest_swing:
                largest_swing = swing
                swing_move = move_number
                # Capture move details
                # We need the SAN of the move *before* pushing it, or use board.san(move) *before* pushing.
                # But we already pushed it. 
                # Actually, board.push(move) was called above.
                # We can get SAN from the node? next_node.san() might work if read from PGN.
                # Or generate it from the board state *before* the push.
                # Let's use next_node.san() which is reliable for PGNs.
                best_move_san = next_node.san()
                best_move_uci = move.uci()
            
            prev_score = score
            node = next_node
            
        return {
            "swing_eval": largest_swing,
            "ply": swing_move,
            "move_san": best_move_san if largest_swing > 0 else None,
            "move_uci": best_move_uci if largest_swing > 0 else None
        }
