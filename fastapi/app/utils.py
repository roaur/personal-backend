from datetime import datetime

import chess
# import chess.pgn

def json_serializer(json_to_post: dict) -> dict:
    if isinstance(json_to_post, datetime):
        return json_to_post.isoformat()

def parse_and_enumerate_moves(game_id: str, moves: list[str]) -> list[dict]:
    """
    Parses and enumerates a list of chess moves.
    """
    board = chess.Board()  # Create a new board instance
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
            raise ValueError(f"Invalid move '{move}' at move number {move_number}: {str(e)}")

    return move_data
