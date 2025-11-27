from datetime import datetime, timezone
from typing import Dict, Any, List
from worker.analysis.plugins.base import AnalysisPlugin

class TimeStatsPlugin(AnalysisPlugin):
    """
    Extracts time-based features from the game.
    """
    
    @property
    def name(self) -> str:
        return "time_stats"

    def process(self, game: Dict[str, Any]) -> List[Dict[str, Any]]:
        features = []
        
        # Game Creation Time
        created_at_ts = game.get('createdAt')
        if created_at_ts:
            dt = datetime.fromtimestamp(created_at_ts / 1000, tz=timezone.utc) # Lichess uses ms
            
            features.append({
                "feature_name": "day_of_week",
                "feature_value": dt.strftime("%A"),
                "feature_type": "categorical"
            })
            
            features.append({
                "feature_name": "hour_of_day",
                "feature_value": str(dt.hour),
                "feature_type": "numerical"
            })
            
        return features
