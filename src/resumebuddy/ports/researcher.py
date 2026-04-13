from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class IResearcher(ABC):
    @abstractmethod
    async def research_company(self, company_name: str, model: Optional[str] = None) -> Dict[str, Any]:
        pass  # pragma: no cover

    @abstractmethod
    def get_company_intel(self, company_name: str) -> Optional[str]:
        pass  # pragma: no cover
