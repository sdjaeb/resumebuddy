import pytest
import respx
from httpx import Response
from resumebuddy.infrastructure.adapters.ollama import OllamaAdapter

@pytest.mark.asyncio
@respx.mock
async def test_ollama_generate_chat():
    adapter = OllamaAdapter(base_url="http://localhost:11434")
    route = respx.post("http://localhost:11434/api/chat").mock(return_value=Response(200, json={"message": {"content": "Hello"}}))
    
    res = await adapter.generate_chat([{"role": "user", "content": "hi"}])
    assert res == "Hello"
    assert route.called

@pytest.mark.asyncio
@respx.mock
async def test_ollama_complete_prompt():
    adapter = OllamaAdapter(base_url="http://localhost:11434")
    respx.post("http://localhost:11434/api/chat").mock(return_value=Response(200, json={"message": {"content": "World"}}))
    
    res = await adapter.complete_prompt("hi")
    assert res == "World"
