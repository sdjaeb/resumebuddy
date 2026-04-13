from pydantic import BaseModel, Field
from typing import List

class UserProfile(BaseModel):
    preferred_languages: List[str] = Field(default_factory=lambda: ["Python", "Node", "Ruby", "C#"])
    supporting_languages: List[str] = Field(default_factory=lambda: ["Java"])
    learning_interests: List[str] = Field(default_factory=lambda: ["Rust", "Go"])
    role_preferences: str = Field(default="Strong preference for IC, Architect, or high-level Technical roles. Avoid roles focused on 'People Management' or 'Direct Reports'.")
    location: str = Field(default="Madison, WI (Remote or Hybrid/On-site in Madison ONLY). Open to overseas companies with US Central Timezone flexibility.")
    min_salary: int = Field(default=130000, description="Hard floor")
    target_salary: int = Field(default=145000)
    current_contract_rate: str = Field(default="$77/hr")
    current_w2_salary: int = Field(default=160000)
    growth_exceptions: str = Field(default="Will consider lower pay ($130k range) if the role provides substantial growth in Data Pipelines, AI, or ML.")
    industry_interests: str = Field(default="Sports (Fantasy/Analytics) and Video Games are preferred interests, but candidate is open to all industries.")
    clearance: str = Field(default="Candidate can obtain Secret or above clearance.")
    disqualified_companies: List[str] = Field(default_factory=lambda: ["Oracle", "Tesla", "SpaceX"])
    recent_applications: List[str] = Field(default_factory=lambda: ["Toast", "Future", "Yahoo", "Docker", "Atlassian"])
