from abc import ABC, abstractmethod
from typing import List, Dict, Any

class IJobDiscovery(ABC):
    @abstractmethod
    async def discover_jobs(self, name: str, url: str) -> List[Dict[str, Any]]:
        pass  # pragma: no cover

    @abstractmethod
    async def discover_agentic(self, query: str) -> List[Dict[str, Any]]:
        pass  # pragma: no cover
