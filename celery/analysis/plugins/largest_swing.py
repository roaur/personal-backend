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
        best_mate_in = None
        
        # Initial position score
        info = engine.analyse(board, chess.engine.Limit(time=0.1))
        score_obj = info["score"].white()
        
        if score_obj.is_mate():
            raw_score = score_obj.score(mate_score=10000)
            prev_score = 10.0 if raw_score > 0 else -10.0
        else:
            prev_score = max(-10.0, min(10.0, score_obj.score() / 100.0))
        
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
            
            # Get score object
            score_obj = info["score"].white()
            
            # Normalize score
            current_mate_in = None
            if score_obj.is_mate():
                mate_moves = score_obj.mate()
                current_mate_in = mate_moves
                
                # Determine sign of mate using a large mate_score
                raw_score = score_obj.score(mate_score=10000)
                if raw_score > 0:
                    score_val = 10.0
                else:
                    score_val = -10.0
            else:
                # Centipawns to pawns
                score_val = score_obj.score() / 100.0
                score_val = max(-10.0, min(10.0, score_val))
            
            # Calculate swing (absolute difference)
            swing = abs(score_val - prev_score)
            
            if swing > largest_swing:
                largest_swing = swing
                swing_move = move_number
                # Capture move details
                best_move_san = next_node.san()
                best_move_uci = move.uci()
                best_mate_in = current_mate_in
            
            prev_score = score_val
            node = next_node
            
        return {
            "swing_eval": round(largest_swing, 2), # Round to 2 decimal places
            "ply": swing_move,
            "move_san": best_move_san if largest_swing > 0 else None,
            "move_uci": best_move_uci if largest_swing > 0 else None,
            "forced_mate_in": best_mate_in
        }
