import pytest
from worker.analysis.plugin_manager import PluginManager
from worker.analysis.plugins.time_stats import TimeStatsPlugin

def test_plugin_discovery():
    manager = PluginManager()
    # Should at least find TimeStatsPlugin
    assert len(manager.plugins) >= 1
    names = [p.name for p in manager.plugins]
    assert "time_stats" in names

def test_time_stats_plugin():
    plugin = TimeStatsPlugin()
    # Mock game data (timestamp for 2023-01-01 12:00:00 UTC)
    # 1672574400000
    # Actually let's use a fixed timestamp
    # Sunday, January 1, 2023 12:00:00 PM GMT
    game = {"createdAt": 1672574400000} 
    
    features = plugin.process(game)
    
    day_feature = next(f for f in features if f["feature_name"] == "day_of_week")
    assert day_feature["feature_value"] == "Sunday"
    
    hour_feature = next(f for f in features if f["feature_name"] == "hour_of_day")
    assert hour_feature["feature_value"] == "12"

def test_plugin_manager_run_all():
    manager = PluginManager()
    game = {"createdAt": 1672574400000}
    
    results = manager.run_all(game)
    assert len(results) >= 2
    assert any(f["feature_name"] == "day_of_week" for f in results)
