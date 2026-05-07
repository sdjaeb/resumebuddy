import json
from typing import List, Dict, Optional, Any
from resumebuddy.ports.llm import ILLMClient
from resumebuddy.domain.models import (
    UserProfile, 
    RoleEvaluation, 
    AlignmentAnalysis, 
    InterviewPrep,
    BSDetector
)
from resumebuddy.application.safety import SafetyMiddleware

class ResumeBuddyUseCases:
    def __init__(self, llm_client: ILLMClient):
        self.llm_client = llm_client

    async def extract_requirements(self, jd_text: str) -> List[str]:
        prompt = f"""Extract a list of key skills, experiences, and requirements from the following job description.
JD:
{jd_text}
"""
        response = await self.llm_client.complete_prompt(prompt)
        try:
            cleaned = response.strip().strip("```json").strip("```")
            return json.loads(cleaned)
        except Exception:
            return []

    async def evaluate_role(self, resume_text: str, jd_data: Dict[str, Any], company_intel: Optional[str] = None, model: Optional[str] = None, profile: Optional[UserProfile] = None) -> RoleEvaluation:
        if not profile:
            profile = UserProfile()
            
        prompt = f"""Evaluate the resume against the job description using an A-F scoring system.
Analyze organizational risk and bait-and-switch potential in the bs_detector section.

USER PREFERENCES:
- Role/Management: {profile.role_preferences}
- Salary: {profile.min_salary} - {profile.target_salary}
- Stage: {profile.company_stage_preferences}
- Travel: {profile.travel_preference}
- Employment Type: {profile.employment_type_preference}
- Work-Life Balance: {profile.wlb_preference}

SCORING CRITERIA (Penalize if these conflict with User Preferences):
1. Skills Alignment: Technical match with preferred/supporting languages.
2. Role Fit & Seniority:
   - IC/Architect preference vs management.
   - DIRECT REPORTS: If the JD mentions managing people or direct reports, penalize the grade.
3. Lifestyle & Logistics:
   - TRAVEL: If travel is required, penalize the grade significantly.
   - WLB: Look for "high-pressure," "fast-paced," or "on-call heavy" keywords. 40hrs/week is the target.
   - EMPLOYMENT TYPE: Permanent is the gold standard; Contract roles start at a lower baseline grade.
4. Company Maturity & Stage:
   - Identify the specific stage: Seed, Series A, Series B, Series C, Late Stage (D+), or Enterprise.
   - Seed/Series A: High growth/equity potential but high "shitshow" risk.
   - Series B/C: Strategic scaling; usually the sweet spot for "Staff" level impact.
   - Late Stage/Enterprise: Stability and scale, but check for red tape or legacy silos.
   - Consultancy: Evaluate based on the "Billable Ratio" and technical practice maturity.
   - Align the detected stage with the User's Preference: {profile.company_stage_preferences}
5. BS Detector: Use organizational rot indicators.
   - CRITICAL (Consultancy): Look for signs of the "Billable Ratio" trap.
   - Penalize the score if high risk is detected.
6. Signals & Flags:
   - Identify specific "Good" and "Bad" signals/flags based on the JD and preferences.
   - For each signal, provide a name, is_positive boolean, a relevant emoji icon, and a short description.
   - Example Good signals: "40hr Week" (🧘), "Remote First" (🏠), "No Direct Reports" (👤), "Series B Sweet Spot" (🚀).
   - Example Bad signals: "High Travel" (✈️), "Management Heavy" (👔), "On-Call Heavy" (🚨), "Contract Role" (📄).

Resume:
{resume_text}

JD Content:
{jd_data.get('description', 'N/A')}

Metadata:
- Title: {jd_data.get('title', 'N/A')}

Company Intel:
{company_intel or "No additional intel available."}
"""
        return await self.llm_client.complete_structured(prompt, response_model=RoleEvaluation, model=model)

    async def analyze_bs(self, jd_text: str, recruiter_message: Optional[str] = None) -> BSDetector:
        prompt = f"""Analyze the provided job description and/or recruiter message for "shitshow" indicators, bait-and-switch tactics, and organizational rot.
        
JD:
{jd_text}

Recruiter Message:
{recruiter_message or "Not provided."}
"""
        return await self.llm_client.complete_structured(prompt, response_model=BSDetector)

    async def analyze_alignment(self, resume_text: str, jd_text: str) -> AlignmentAnalysis:
        prompt = f"""Analyze the alignment between the provided resume and job description.

Resume:
{resume_text}

JD:
{jd_text}
"""
        return await self.llm_client.complete_structured(prompt, response_model=AlignmentAnalysis)

    async def generate_cover_letter(self, resume_text: str, jd_text: str, alignment: AlignmentAnalysis, model: Optional[str] = None) -> str:
        prompt = f"""Write a highly targeted, professional cover letter.
Candidate Resume:
{resume_text}

Job Description:
{jd_text}

Alignment Data:
{alignment.model_dump_json(indent=2)}

Return ONLY the cover letter text.
"""
        raw_cv = await self.llm_client.complete_prompt(prompt, model=model)
        return SafetyMiddleware.scrub_text(raw_cv)

    async def optimize_resume(self, resume_text: str, jd_text: str, alignment: AlignmentAnalysis) -> str:
        prompt = f"""Optimize the following resume for the provided job description.

STRICT CONSTRAINTS:
1. DO NOT change or omit any Company Names.
2. DO NOT change or omit any Job Titles.
3. DO NOT change employment dates.
4. DO NOT use placeholders like "Previous Company A". 
5. MAINTAIN the historical integrity of the candidate's career.
6. TAILOR the resume by emphasizing relevant achievements in the bullet points and professional summary. Use the JD and Alignment Data to prioritize high-impact keywords and specific technologies.

Candidate Resume:
{resume_text}

Job Description:
{jd_text}

Alignment Data:
{alignment.model_dump_json(indent=2)}

Return ONLY the optimized resume text.
"""
        raw_resume = await self.llm_client.complete_prompt(prompt)
        return SafetyMiddleware.scrub_text(raw_resume)

    async def prepare_interview(self, resume_text: str, jd_text: str, company_intel: Optional[str] = None, model: Optional[str] = None) -> InterviewPrep:
        prompt = f"""Generate a comprehensive interview preparation guide based on the candidate's resume, the job description, and company intel.
        
Resume:
{resume_text}

Job Description:
{jd_text}

Company Intel:
{company_intel or "No additional intel available."}
"""
        return await self.llm_client.complete_structured(prompt, response_model=InterviewPrep, model=model)
