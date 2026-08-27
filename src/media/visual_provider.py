from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from pathlib import Path
from src.utils.logger import logger

class ProviderHealthManager:
    """Circuit breaker pattern to disable providers experiencing persistent network errors."""

    def __init__(self, failure_threshold: int = 2):
        self.failure_threshold = failure_threshold
        self.health_state: Dict[str, Dict[str, Any]] = {}

    def register_provider(self, name: str):
        if name not in self.health_state:
            self.health_state[name] = {"available": True, "failures": 0}

    def is_available(self, name: str) -> bool:
        self.register_provider(name)
        return self.health_state[name]["available"]

    def record_success(self, name: str):
        self.register_provider(name)
        self.health_state[name]["failures"] = 0
        self.health_state[name]["available"] = True

    def record_failure(self, name: str, reason: str = ""):
        self.register_provider(name)
        state = self.health_state[name]
        state["failures"] += 1
        logger.warning(f"Visual Provider '{name}' failure #{state['failures']} ({reason})")
        
        if state["failures"] >= self.failure_threshold:
            state["available"] = False
            logger.error(f"Visual Provider '{name}' REACHED FAILURE THRESHOLD ({self.failure_threshold}). Disabling for current run!")

class VisualProvider(ABC):
    """Abstract Base Class for Visual Providers."""

    def __init__(self, name: str, health_manager: ProviderHealthManager):
        self.name = name
        self.health_manager = health_manager
        self.health_manager.register_provider(name)

    @property
    def is_available(self) -> bool:
        return self.health_manager.is_available(self.name)

    @abstractmethod
    def search_and_download(self, query: str, output_path: Path) -> Optional[Dict[str, Any]]:
        """Search media for query and download to output_path. Returns asset metadata dict or None."""
        pass
