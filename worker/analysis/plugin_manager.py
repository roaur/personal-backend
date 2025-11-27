import importlib
import inspect
import os
import pkgutil
import logging
from typing import List, Dict, Any, Type
from worker.analysis.plugins.base import AnalysisPlugin

logger = logging.getLogger(__name__)

class PluginManager:
    """
    Discovers and manages analysis plugins.
    """
    def __init__(self, plugin_package: str = "worker.analysis.plugins"):
        self.plugin_package = plugin_package
        self.plugins: List[AnalysisPlugin] = []
        self._discover_plugins()

    def _discover_plugins(self):
        """
        Dynamically finds and instantiates all AnalysisPlugin subclasses 
        in the plugin package.
        """
        self.plugins = []
        
        # Import the package to locate it on the filesystem
        try:
            package = importlib.import_module(self.plugin_package)
        except ImportError as e:
            logger.error(f"Could not import plugin package {self.plugin_package}: {e}")
            return

        # Walk through all modules in the package
        for _, name, _ in pkgutil.iter_modules(package.__path__):
            full_name = f"{self.plugin_package}.{name}"
            try:
                module = importlib.import_module(full_name)
                
                # Find all classes in the module
                for attribute_name in dir(module):
                    attribute = getattr(module, attribute_name)
                    
                    if (isinstance(attribute, type) and 
                        issubclass(attribute, AnalysisPlugin) and 
                        attribute is not AnalysisPlugin):
                        
                        # Instantiate and add
                        try:
                            plugin_instance = attribute()
                            self.plugins.append(plugin_instance)
                            logger.info(f"Loaded plugin: {plugin_instance.name}")
                        except Exception as e:
                            logger.error(f"Failed to instantiate plugin {attribute_name}: {e}")
                            
            except Exception as e:
                logger.error(f"Failed to import module {full_name}: {e}")

    def run_all(self, game: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Runs all loaded plugins on the game and aggregates results.
        """
        all_features = []
        for plugin in self.plugins:
            try:
                features = plugin.process(game)
                all_features.extend(features)
            except Exception as e:
                logger.error(f"Plugin {plugin.name} failed: {e}")
        return all_features
