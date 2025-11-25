from datetime import datetime

import chess
# import chess.pgn

def json_serializer(json_to_post: dict) -> dict:
    if isinstance(json_to_post, datetime):
        return json_to_post.isoformat()

def parse_and_enumerate_moves(game_id: str, moves: list[str], variant: str = "standard", initial_fen: str = None) -> list[dict]:
    """
    Parses and enumerates a list of chess moves.
    """
    if initial_fen and initial_fen != "start":
        board = chess.Board(initial_fen, chess960=(variant == "chess960"))
    else:
        board = chess.Board()
    
    move_data = []

    for move_number, move in enumerate(moves, start=1):
        try:
            board.push_san(move)  # Push the move to the board (validates the move)
            move_data.append({
                "game_id": game_id,
                "move_number": move_number,
                "move": move,
            })
        except ValueError as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error parsing moves for game {game_id}: {e}")
            logger.error(f"Variant: {variant}, Initial FEN: {initial_fen}")
            logger.error(f"Moves: {moves}")
            raise ValueError(f"Invalid move '{move}' at move number {move_number}: {str(e)}")

    return move_data
