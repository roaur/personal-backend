from common.analytics.base import BaseAnalytic
import chess.pgn

class MoveCountAnalytic(BaseAnalytic):
    @property
    def name(self) -> str:
        return "move_count"

    @property
    def version(self) -> str:
        return "1.0.0"

    def analyze(self, game: chess.pgn.Game) -> dict:
        node = game
        count = 0
        while node.next():
            node = node.next()
            count += 1
        return {"move_count": count}
