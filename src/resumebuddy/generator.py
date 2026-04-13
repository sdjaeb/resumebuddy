from typing import Dict, Any, Optional
import json
from .ollama_client import OllamaClient

class Generator:
    def __init__(self, client: OllamaClient):
        self.client = client

    async def generate_cover_letter(self, resume_text: str, jd_text: str, alignment: Dict[str, Any], model: Optional[str] = None) -> str:
        prompt = f"""Write a highly targeted, professional cover letter for the following candidate and job.
Use the alignment data to highlight why they are a great fit, especially addressing any missing skills with tangential experience or a willingness to learn.
Apply the STAR (Situation, Task, Action, Result) method where possible to describe their impact.

Candidate Resume:
{resume_text}

Job Description:
{jd_text}

Alignment Data:
{json.dumps(alignment, indent=2)}

Return ONLY the cover letter text. Use a professional, confident, and direct tone.
"""
        return await self.client.complete_prompt(prompt, model=model)

    async def optimize_resume(self, resume_text: str, jd_text: str, alignment: Dict[str, Any]) -> str:
        prompt = f"""Optimize the following resume for the provided job description.
Focus on highlighting matching skills and achievements using the STAR method.
Ensure the resume remains truthful but emphasizes the most relevant experience for this specific role.

Candidate Resume:
{resume_text}

Job Description:
{jd_text}

Alignment Data:
{json.dumps(alignment, indent=2)}

Return ONLY the optimized resume text.
"""
        return await self.client.complete_prompt(prompt)
