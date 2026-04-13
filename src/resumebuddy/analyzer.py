from typing import List, Dict, Optional, Any
import json
from .ollama_client import OllamaClient
from .models import UserProfile

class AlignmentResult(Dict):
    matching_skills: List[str]
    missing_skills: List[str]
    tangential_matches: Dict[str, str] # Missing skill -> Tangential experience
    alignment_summary: str

class Analyzer:
    def __init__(self, client: OllamaClient):
        self.client = client

    async def extract_requirements(self, jd_text: str) -> List[str]:
        prompt = f"""Extract a list of key skills, experiences, and requirements from the following job description. Return only a JSON list of strings.
JD:
{jd_text}
"""
        response = await self.client.complete_prompt(prompt)
        try:
            # Simple cleanup for potential markdown
            cleaned = response.strip().strip("```json").strip("```")
            return json.loads(cleaned)
        except:
            return []

    async def evaluate_role(self, resume_text: str, jd_data: Dict[str, Any], company_intel: Optional[str] = None, model: Optional[str] = None, profile: Optional[UserProfile] = None) -> Dict[str, Any]:
        """
        Career-Ops inspired A-F scoring system with 12 dimensions.
        Includes user-specific constraints: No Java preference, Remote/Madison location, and Clearance capability.
        """
        if not profile:
            profile = UserProfile()
            
        prompt = f"""Evaluate the resume against the job description using an A-F scoring system (A=Excellent, F=Poor).
Score the role based on 12 weighted dimensions:
1. Skills Match (Prefer {', '.join(profile.preferred_languages)}. {', '.join(profile.supporting_languages)} is acceptable but NOT as primary. Interest/willingness to learn {', '.join(profile.learning_interests)})
2. Experience Fit ({profile.role_preferences})
3. Growth Potential (Bonus points for roles offering experience in Data Engineering/Pipelines, AI Engineering, AI Coding Assistance, or Machine Learning)
4. Compensation (Min: ${profile.min_salary} hard floor. Target: ${profile.target_salary}+. If ${profile.min_salary}-${profile.target_salary}, evaluate based on growth in dimension 3)
5. Company Health (Analyze stock performance/trends and financial reports from provided intel to judge stability)
6. Culture Fit (from provided intel)
7. Commute/Remote Flex ({profile.location})
8. Networking Connections (Note: Candidate has recently applied to {', '.join(profile.recent_applications)})
9. Interview Preparation Needs
10. Long-term Career Alignment ({profile.industry_interests})
11. Job Age (How long has this been posted? Provided in metadata)
12. Repost Status (Is this a known repost? Provided in metadata)

Additional Candidate Constraints:
- Preferred Language: {', '.join(profile.preferred_languages)} (Supporting: {', '.join(profile.supporting_languages)}). Interest in {', '.join(profile.learning_interests)}.
- Role Type: {profile.role_preferences}
- Location: {profile.location}
- Compensation:
    - Min: ${profile.min_salary} (Hard floor)
    - Target: ${profile.target_salary}+
    - Current/Recent: {profile.current_contract_rate} (contract), ${profile.current_w2_salary} (W-2)
    - Exception: {profile.growth_exceptions}
- Industry Interests: {profile.industry_interests}
- Clearance: {profile.clearance}
- Company Weighting:
    - HIGH WEIGHT: Established organizations (stable stock/revenue).
    - MEDIUM-HIGH WEIGHT: Startups (note if startup; weighted slightly less than established, but higher than FAANG for agility).
    - MEDIUM WEIGHT: FAANG-type (Apple, Microsoft, Google, Netflix, Amazon, IBM, NVIDIA).
    - DISQUALIFIED: {', '.join(profile.disqualified_companies)}.

Resume:
{resume_text}

JD Content:
{jd_data.get('description', 'N/A')}

Metadata:
- Title: {jd_data.get('title', 'N/A')}
- Posted At: {jd_data.get('posted_at', 'Unknown')}
- Is Repost: {jd_data.get('is_repost', False)}

Company Intel (if any):
{company_intel or "No additional intel available."}

Return a JSON object with: "overall_score" (A-F), "dimension_scores" (Dict of score per dimension), "rationale" (summary).
"""
        response = await self.client.complete_prompt(prompt, model=model)
        try:
            cleaned = response.strip().strip("```json").strip("```")
            return json.loads(cleaned)
        except:
            return {"error": "Failed to parse A-F evaluation"}

    async def analyze_alignment(self, resume_text: str, jd_text: str) -> Dict[str, Any]:
        prompt = f"""Analyze the alignment between the provided resume and job description.
Identify:
1. Matching skills found on both.
2. Key missing skills required by the JD but absent from the resume.
3. For each missing skill, identify if there is tangential experience on the resume that could be relevant.
Return the result as a JSON object with keys: "matching_skills", "missing_skills", "tangential_matches" (dict), and "alignment_summary".

Resume:
{resume_text}

JD:
{jd_text}
"""
        response = await self.client.complete_prompt(prompt)
        try:
            cleaned = response.strip().strip("```json").strip("```")
            return json.loads(cleaned)
        except:
            return {"error": "Failed to parse alignment analysis"}
