from abc import ABC, abstractmethod
from typing import Dict, Any

class IJobScraper(ABC):
    @abstractmethod
    async def scrape_job(self, url: str) -> Dict[str, Any]:
        pass  # pragma: no cover
