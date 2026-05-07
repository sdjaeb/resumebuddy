import os
import json
import sys
import sqlite3

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from resumebuddy.infrastructure.adapters.repository import SQLiteJobRepository
from resumebuddy.domain.models import JobOpportunity

def main():
    repo = SQLiteJobRepository("jobs.db")
    
    new_jobs = [
        {
            "id": "openai-principal",
            "name": "OpenAI - Principal Software Engineer",
            "score": "A-",
            "priority": 2,
            "url": "https://www.linkedin.com/jobs/view/4387518407",
            "dir": "tmp/prospects/openai-principal",
            "status": "Ready to Apply",
            "company_grade": "A-",
            "company_mission": "OpenAI's mission is to ensure that artificial general intelligence (AGI) benefits all of humanity.",
            "signals": [
                {"name": "Prestige", "is_positive": True, "icon": "👑", "description": "Industry leader"},
                {"name": "Frontier AI", "is_positive": True, "icon": "🚀", "description": "Cutting edge R&D"},
                {"name": "High Pressure", "is_positive": False, "icon": "🔥", "description": "Known for intensity"}
            ]
        },
        {
            "id": "grafana-staff",
            "name": "Grafana Labs - Staff Backend Engineer",
            "score": "A-",
            "priority": 2,
            "url": "https://www.linkedin.com/jobs/view/4401361799",
            "dir": "tmp/prospects/grafana-staff",
            "status": "Ready to Apply",
            "company_grade": "A",
            "company_mission": "Grafana Labs provides an open and composable observability stack built around Grafana.",
            "signals": [
                {"name": "Remote-First", "is_positive": True, "icon": "🏠", "description": "Mature remote culture"},
                {"name": "Salary Match", "is_positive": True, "icon": "💰", "description": "High alignment with $175k+"},
                {"name": "Observability", "is_positive": True, "icon": "📊", "description": "Domain expertise match"}
            ]
        },
        {
            "id": "paramount-senior-ai",
            "name": "Paramount - Senior AI Products & Agents",
            "score": "B-",
            "priority": 2,
            "url": "https://www.linkedin.com/jobs/view/4410945020",
            "dir": "tmp/prospects/paramount-senior-ai",
            "status": "Ready to Apply",
            "company_grade": "C",
            "company_mission": "Paramount is a leading global media and entertainment company.",
            "signals": [
                {"name": "RAG Focus", "is_positive": True, "icon": "🤖", "description": "Strong technical alignment"},
                {"name": "M&A Risk", "is_positive": False, "icon": "⚠️", "description": "Skydance merger instability"},
                {"name": "Low Floor", "is_positive": False, "icon": "📉", "description": "$124k entry point"}
            ]
        },
        {
            "id": "planet-dds-conversion",
            "name": "Planet DDS - Senior Conversion Engineer",
            "score": "D",
            "priority": 3,
            "url": "https://pdds-buyer-llc.primepay-recruit.com/job/1006625/senior-conversion-engineer-ai-powered",
            "dir": "tmp/prospects/planet-dds-conversion",
            "status": "Declined",
            "company_grade": "D",
            "company_mission": "Planet DDS is the leader in cloud-based dental software solutions.",
            "signals": [
                {"name": "Shitshow", "is_positive": False, "icon": "💩", "description": "9/10 BS Score"},
                {"name": "ETL Heavy", "is_positive": False, "icon": "🧹", "description": "Repetitive data cleanup"},
                {"name": "Regression", "is_positive": False, "icon": "⏪", "description": "Not Staff/Architect scope"}
            ]
        },
        {
            "id": "insight-global-genai",
            "name": "Insight Global - GenAI Engineer",
            "score": "B",
            "priority": 2,
            "url": "https://www.linkedin.com/jobs/view/insight-global-genai",
            "dir": "tmp/prospects/insight-global-genai",
            "status": "Ready to Apply",
            "company_grade": "C",
            "company_mission": "Professional Healthcare Recruiter at Insight Global",
            "signals": [
                {"name": "Tech Alignment", "is_positive": True, "icon": "🛠️", "description": "Agentic workflows & RAG"},
                {"name": "Contract Risk", "is_positive": False, "icon": "📄", "description": "7-month contract-to-hire"},
                {"name": "Client Facing", "is_positive": False, "icon": "🤝", "description": "100% travel/forward-deployed risk"}
            ]
        }
    ]

    for job_data in new_jobs:
        job = JobOpportunity(
            id=job_data["id"],
            name=job_data["name"],
            score=job_data["score"],
            priority=job_data["priority"],
            url=job_data["url"],
            dir=job_data["dir"],
            status=job_data["status"],
            company_grade=job_data["company_grade"],
            company_mission=job_data["company_mission"],
            signals_json=json.dumps(job_data["signals"])
        )
        repo.save_job(job)
        print(f"Saved: {job.name}")

if __name__ == "__main__":
    main()
