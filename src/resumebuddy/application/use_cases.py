import json
from typing import List, Dict, Optional, Any
from resumebuddy.ports.llm import ILLMClient
from resumebuddy.domain.models import UserProfile

class ResumeBuddyUseCases:
    def __init__(self, llm_client: ILLMClient):
        self.llm_client = llm_client

    async def extract_requirements(self, jd_text: str) -> List[str]:
        prompt = f"""Extract a list of key skills, experiences, and requirements from the following job description. Return only a JSON list of strings.
JD:
{jd_text}
"""
        response = await self.llm_client.complete_prompt(prompt)
        try:
            cleaned = response.strip().strip("```json").strip("```")
            return json.loads(cleaned)
        except Exception:
            return []

    async def evaluate_role(self, resume_text: str, jd_data: Dict[str, Any], company_intel: Optional[str] = None, model: Optional[str] = None, profile: Optional[UserProfile] = None) -> Dict[str, Any]:
        if not profile:
            profile = UserProfile()
            
        prompt = f"""Evaluate the resume against the job description using an A-F scoring system.
Resume:
{resume_text}

JD Content:
{jd_data.get('description', 'N/A')}

Metadata:
- Title: {jd_data.get('title', 'N/A')}

Company Intel:
{company_intel or "No additional intel available."}

Return a JSON object with: "overall_score" (A-F), "dimension_scores" (Dict of score per dimension), "rationale" (summary).
"""
        response = await self.llm_client.complete_prompt(prompt, model=model)
        try:
            cleaned = response.strip().strip("```json").strip("```")
            return json.loads(cleaned)
        except Exception:
            return {"error": "Failed to parse A-F evaluation"}

    async def analyze_alignment(self, resume_text: str, jd_text: str) -> Dict[str, Any]:
        prompt = f"""Analyze the alignment between the provided resume and job description.
Return a JSON object with keys: "matching_skills", "missing_skills", "tangential_matches" (dict), and "alignment_summary".

Resume:
{resume_text}

JD:
{jd_text}
"""
        response = await self.llm_client.complete_prompt(prompt)
        try:
            cleaned = response.strip().strip("```json").strip("```")
            return json.loads(cleaned)
        except Exception:
            return {"error": "Failed to parse alignment analysis"}

    async def generate_cover_letter(self, resume_text: str, jd_text: str, alignment: Dict[str, Any], model: Optional[str] = None) -> str:
        prompt = f"""Write a highly targeted, professional cover letter.
Candidate Resume:
{resume_text}

Job Description:
{jd_text}

Alignment Data:
{json.dumps(alignment, indent=2)}

Return ONLY the cover letter text.
"""
        return await self.llm_client.complete_prompt(prompt, model=model)

    async def optimize_resume(self, resume_text: str, jd_text: str, alignment: Dict[str, Any]) -> str:
        prompt = f"""Optimize the following resume for the provided job description.
Candidate Resume:
{resume_text}

Job Description:
{jd_text}

Alignment Data:
{json.dumps(alignment, indent=2)}

Return ONLY the optimized resume text.
"""
        return await self.llm_client.complete_prompt(prompt)
