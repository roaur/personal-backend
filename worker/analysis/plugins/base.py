from abc import ABC, abstractmethod
from typing import Dict, Any, List

class AnalysisPlugin(ABC):
    """
    Base class for all analysis plugins.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name of the plugin."""
        pass

    @abstractmethod
    def process(self, game: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Processes a single game and returns a list of feature dictionaries.
        
        Args:
            game: The raw game dictionary from Lichess.
            
        Returns:
            A list of dicts, where each dict represents a feature:
            {
                "feature_name": str,
                "feature_value": str | int | float,
                "feature_type": "categorical" | "numerical"
            }
        """
        pass
