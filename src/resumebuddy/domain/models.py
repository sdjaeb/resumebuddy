from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class UserProfile(BaseModel):
    preferred_languages: List[str] = Field(default_factory=lambda: ["Python", "Node", "Ruby", "C#"])
    supporting_languages: List[str] = Field(default_factory=lambda: ["Java"])
    learning_interests: List[str] = Field(default_factory=lambda: ["Rust", "Go"])
    role_preferences: str = Field(default="Strong preference for IC, Architect, or high-level Technical roles. Avoid roles focused on 'People Management' or 'Direct Reports'.")
    location: str = Field(default="Madison, WI (Remote or Hybrid/On-site in Madison ONLY). Open to overseas companies with US Central Timezone flexibility.")
    min_salary: int = Field(default=135000, description="Hard floor for standard roles; Mid-$130s for high-growth AI/ML roles with exceptional benefits.")
    target_salary: int = Field(default=145000)
    current_contract_rate: str = Field(default="$77/hr")
    current_w2_salary: int = Field(default=160000)
    growth_exceptions: str = Field(default="Will consider lower pay ($130k range) if the role provides substantial growth in Data Pipelines, AI, or ML.")
    industry_interests: str = Field(default="Sports (Fantasy/Analytics) and Video Games are preferred interests, but candidate is open to all industries.")
    clearance: str = Field(default="Candidate can obtain Secret or above clearance.")
    disqualified_companies: List[str] = Field(default_factory=lambda: ["Oracle", "Tesla", "SpaceX"])
    recent_applications: List[str] = Field(default_factory=lambda: ["Toast", "Future", "Yahoo", "Docker", "Atlassian"])
    company_stage_preferences: str = Field(default="Prefers Series A/B for growth or high-prestige Enterprise for stability. Wary of mid-sized firms with organizational rot.")
    travel_preference: str = Field(default="No travel preferred. High penalty for required travel.")
    employment_type_preference: str = Field(default="Permanent preferred over Contract.")
    wlb_preference: str = Field(default="Prefers roles close to 40 hrs/week. High penalty for 'always-on' or 'crunch' cultures.")

class STARItem(BaseModel):
    situation: str
    task: str
    action: str
    result: str
    alignment: str

class BSDetector(BaseModel):
    score: int = Field(ge=0, le=10)
    red_flags: List[str]
    analysis: str

class EvaluationSignal(BaseModel):
    name: str
    is_positive: bool
    icon: str = Field(description="Emoji icon for the signal (e.g. 🏠, ✈️, 💰, 🧘)")
    description: str

class RoleEvaluation(BaseModel):
    overall_score: str = Field(description="A-F grade")
    company_stage: str = Field(description="Detected company stage (e.g. Enterprise, Series A, Series B, Startup, Consultancy)")
    dimension_scores: Dict[str, str]
    rationale: str
    bs_detector: BSDetector
    signals: List[EvaluationSignal] = Field(default_factory=list)

class AlignmentAnalysis(BaseModel):
    matching_skills: List[str]
    missing_skills: List[str]
    tangential_matches: Dict[str, str]
    alignment_summary: str

class InterviewPrep(BaseModel):
    company: str
    role: str
    intro_statement: str
    star_items: List[STARItem]
    suggested_questions: List[str]
    technical_refreshers: List[str]
    salary_strategy: str

class JobOpportunity(BaseModel):
    id: str
    name: str
    score: str
    priority: int
    url: str
    dir: str
    status: str
    resume_content: Optional[str] = None
    cover_letter_content: Optional[str] = None
    details_content: Optional[str] = None
    signals_json: Optional[str] = Field(None, description="JSON string of evaluation signals")
    company_grade: Optional[str] = None
    company_mission: Optional[str] = None
