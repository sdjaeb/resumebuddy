import asyncio
import json
import re
from typing import List, Dict, Optional, Any, Type, TypeVar
from pydantic import BaseModel
from resumebuddy.ports.llm import ILLMClient
import mlx_lm
from mlx_lm.sample_utils import make_sampler

T = TypeVar("T", bound=BaseModel)

class MLXAdapter(ILLMClient):
    """
    Adapter for MLX-LM, optimized for Apple Silicon.
    """
    def __init__(self, model_path: str = "mlx-community/gemma-2-27b-it-4bit"):
        self.model_path = model_path
        self.model = None
        self.tokenizer = None

    def _ensure_model(self):
        if self.model is None:
            # We don't want to load it in the constructor as it might be heavy
            self.model, self.tokenizer = mlx_lm.load(self.model_path)

    async def generate_chat(self, messages: List[Dict[str, str]], stream: bool = False, model: Optional[str] = None) -> str:
        self._ensure_model()
        
        # Use the tokenizer's chat template if available
        if hasattr(self.tokenizer, "apply_chat_template"):
            prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        else:
            # Fallback for models without a chat template
            prompt = ""
            for msg in messages:
                role = msg["role"].upper()
                content = msg["content"]
                prompt += f"{role}: {content}\n"
            prompt += "ASSISTANT: "
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: mlx_lm.generate(
                self.model, 
                self.tokenizer, 
                prompt=prompt, 
                verbose=False, 
                max_tokens=2048
            )
        )
        return response

    async def complete_prompt(self, prompt: str, model: Optional[str] = None) -> str:
        messages = [{"role": "user", "content": prompt}]
        return await self.generate_chat(messages, model=model)

    async def complete_structured(self, prompt: str, response_model: Type[T], model: Optional[str] = None) -> T:
        schema = response_model.model_json_schema()
        structured_prompt = f"""{prompt}

CRITICAL: Return ONLY a valid JSON object matching this schema:
{json.dumps(schema, indent=2)}

JSON Output:"""
        
        response_text = await self.complete_prompt(structured_prompt, model=model)
        
        # Robust JSON extraction
        try:
            # Clean up the response text from common LLM quirks
            cleaned_text = response_text.strip()
            # Remove <bos>, <eos>, and other tags if present
            cleaned_text = re.sub(r'<[^>]+>', '', cleaned_text)
            
            # Try finding the first { and last }
            match = re.search(r'\{.*\}', cleaned_text, re.DOTALL)
            if match:
                json_str = match.group(0)
                
                # Fix common trailing commas before closing braces/brackets
                json_str = re.sub(r',\s*\}', '}', json_str)
                json_str = re.sub(r',\s*\]', ']', json_str)
                # Remove control characters that often break pydantic validation
                json_str = "".join(c for c in json_str if ord(c) >= 32 or c in "\n\r\t")
                
                try:
                    return response_model.model_validate_json(json_str)
                except Exception as e:
                    # If it fails, try one more time with a very aggressive cleanup
                    try:
                        import json as json_lib
                        parsed = json_lib.loads(json_str, strict=False)
                        return response_model.model_validate(parsed)
                    except:
                        raise ValueError(f"Found JSON block but it failed validation: {e}\nBlock: {json_str}")
            
            # Fallback to direct validation if no braces found
            return response_model.model_validate_json(cleaned_text)
        except Exception as e:
            raise ValueError(f"Failed to extract or validate JSON from MLX response: {e}\nResponse: {response_text}")
