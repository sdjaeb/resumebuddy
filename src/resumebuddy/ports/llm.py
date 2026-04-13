from abc import ABC, abstractmethod
from typing import List, Dict, Optional

class ILLMClient(ABC):
    @abstractmethod
    async def generate_chat(self, messages: List[Dict[str, str]], stream: bool = False, model: Optional[str] = None) -> str:
        pass  # pragma: no cover

    @abstractmethod
    async def complete_prompt(self, prompt: str, model: Optional[str] = None) -> str:
        pass  # pragma: no cover
