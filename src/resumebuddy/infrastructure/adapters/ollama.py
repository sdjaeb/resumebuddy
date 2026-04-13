import httpx
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from resumebuddy.ports.llm import ILLMClient

class OllamaResponse(BaseModel):
    model: str
    created_at: str
    message: Dict[str, str]
    done: bool
    total_duration: Optional[int] = None
    load_duration: Optional[int] = None
    prompt_eval_count: Optional[int] = None
    eval_count: Optional[int] = None

class OllamaAdapter(ILLMClient):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "gemma4:e4b"):
        self.base_url = base_url
        self.model = model

    async def generate_chat(self, messages: List[Dict[str, str]], stream: bool = False, model: Optional[str] = None) -> str:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": model or self.model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": 0.2,
            }
        }

        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["message"]["content"]

    async def complete_prompt(self, prompt: str, model: Optional[str] = None) -> str:
        messages = [{"role": "user", "content": prompt}]
        return await self.generate_chat(messages, model=model)
