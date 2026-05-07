from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

class ILLMClient(ABC):
    @abstractmethod
    async def generate_chat(self, messages: List[Dict[str, str]], stream: bool = False, model: Optional[str] = None) -> str:
        pass  # pragma: no cover

    @abstractmethod
    async def complete_prompt(self, prompt: str, model: Optional[str] = None) -> str:
        pass  # pragma: no cover

    @abstractmethod
    async def complete_structured(self, prompt: str, response_model: Type[T], model: Optional[str] = None) -> T:
        pass  # pragma: no cover
