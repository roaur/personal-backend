import importlib
import pkgutil
import inspect
import os
from typing import List, Type
from common.analytics.base import BaseAnalytic

def discover_analytics(plugins_package: str = "common.analytics.plugins") -> List[Type[BaseAnalytic]]:
    """
    Discovers and returns a list of BaseAnalytic subclasses from the specified package.
    """
    discovered_analytics = []
    
    # Ensure the package exists
    try:
        package = importlib.import_module(plugins_package)
    except ImportError:
        # If the package doesn't exist, return empty list (or maybe log a warning)
        return []

    if not hasattr(package, "__path__"):
        return []

    for _, name, _ in pkgutil.iter_modules(package.__path__):
        full_name = f"{plugins_package}.{name}"
        module = importlib.import_module(full_name)
        
        for attribute_name in dir(module):
            attribute = getattr(module, attribute_name)
            
            if (inspect.isclass(attribute) and 
                issubclass(attribute, BaseAnalytic) and 
                attribute is not BaseAnalytic and
                attribute.__module__ == full_name): # Avoid importing base classes re-exported
                
                discovered_analytics.append(attribute)
                
    return discovered_analytics
