import os
import json
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from resumebuddy.infrastructure.adapters.repository import SQLiteJobRepository
from resumebuddy.domain.models import JobOpportunity

def main():
    repo = SQLiteJobRepository("jobs.db")
    
    turing_job = JobOpportunity(
        id="turing-genai",
        name="Turing - Software Engineer (GenAI)",
        score="B+",
        priority=2,
        url="https://work.turing.com/job/home?jobId=65062&jobToken=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqb2JJZCI6NjUwNjIsInVzZXJJZCI6MTM4NSwidXNlclJvbGUiOiJUQV9TT1VSQ0VEIiwiaWF0IjoxNzczODQzMTE2fQ.GHsDKyZYVUIkN5Oi32lzDi8dxmzcE-4pvNDrcAv15tM",
        dir="tmp/prospects/turing-genai",
        status="Ready to Apply",
        company_grade="B",
        company_mission="Turing is a data-science-driven deep jobs platform that helps companies spin up their engineering teams in the cloud at the push of a button.",
        signals_json=json.dumps([
            {"name": "Tech Match", "is_positive": True, "icon": "🛠️", "description": "RAG, FastAPI, and Data Pipelines"},
            {"name": "AI Safety", "is_positive": True, "icon": "🛡️", "description": "Explicit focus on model evaluation/risk"},
            {"name": "Remote Conflict", "is_positive": False, "icon": "📍", "description": "DM says NYC Onsite; Platform says Fully Remote"}
        ])
    )
    repo.save_job(turing_job)
    print("Saved Turing role.")

if __name__ == "__main__":
    main()
