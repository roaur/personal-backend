from abc import ABC, abstractmethod
import chess
import chess.engine
import chess.pgn

class BaseAnalytic(ABC):
    """
    Abstract base class for analysis plugins.
    Plugins are pure analysis units that take a game and return a dictionary of results.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        The key used to store the results in the JSONB column.
        Must be unique.
        """
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """
        The version of the analytic logic.
        """
        pass

    @abstractmethod
    def analyze(self, game: chess.pgn.Game) -> dict:
        """
        Perform analysis on the game.
        
        Args:
            game: The parsed python-chess Game object.
            
        Returns:
            A dictionary of results.
        """
        pass

class EngineAnalytic(BaseAnalytic):
    """
    Base class for analytics that require a chess engine.
    """
    
    @abstractmethod
    def analyze(self, game: chess.pgn.Game, engine: chess.engine.SimpleEngine) -> dict:
        """
        Perform analysis on the game using an engine.
        
        Args:
            game: The parsed python-chess Game object.
            engine: The initialized Stockfish engine.
            
        Returns:
            A dictionary of results.
        """
        pass
