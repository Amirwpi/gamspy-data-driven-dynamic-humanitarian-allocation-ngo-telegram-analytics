
import logging
from abc import ABC
from pathlib import Path
from typing import Dict, Any

class BaseComponent(ABC):
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger = None):
        self.config = config
        self.logger = logger or logging.getLogger(self.__class__.__name__)
    
    def log_info(self, message: str) -> None:
        self.logger.info(message)
    
    def log_warning(self, message: str) -> None:
        self.logger.warning(message)
    
    def log_error(self, message: str) -> None:
        self.logger.error(message)
    
    def log_debug(self, message: str) -> None:
        self.logger.debug(message)
    
    def get_config_value(self, *keys: str, default: Any = None) -> Any:
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
