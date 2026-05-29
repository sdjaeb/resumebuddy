import os
import sys
import sqlite3
import hashlib

# Add src to path
sys.path.append(os.path.abspath("src"))

from resumebuddy.infrastructure.adapters.repository import SQLiteJobRepository
from resumebuddy.domain.models import JobOpportunity

# Embedded data from index.html (the "prospects" array)
static_prospects = [
    # TIER 1 & TOP TARGETS
    {"id": "nvisia", "name": "nvisia (Adaptive Principal Architect)", "score": "A-", "priority": 1, "url": "https://www.nvisia.com/who-we-are/careers-in-technology", "dir": "tmp/prospects/nvisia", "status": "Final Round Invite Incoming", "signals_json": "[{\"name\": \"AI Focused\", \"description\": \"Focus on bespoke AI engagements.\"}, {\"name\": \"Accelerated\", \"description\": \"Signed clients driving immediate need.\"}]"},
    {"id": "hannah-itc", "name": "McKinsey (Staff Backend Engineer)", "score": "A", "priority": 1, "url": "mailto:Hannah.Xu@ITCcorp.com", "dir": "tmp/prospects/hannah-itc", "status": "Presented to Client", "signals_json": "[{\"name\": \"Tier 1 Prestige\", \"description\": \"McKinsey brand credential.\"}, {\"name\": \"Target $100/hr\", \"description\": \"$208k TC potential.\"}]"},
    {"id": "mlb-ai-engineer", "name": "MLB (Project Newman - AI Engineer)", "score": "A", "priority": 1, "url": "N/A", "dir": "tmp/prospects/mlb-ai-engineer", "status": "Qualifying", "signals_json": "[{\"name\": \"Project Newman\", \"description\": \"Custom Go multi-agent platform.\"}, {\"name\": \"No Frameworks\", \"description\": \"Avoids LangChain; values fundamental principles.\"}, {\"name\": \"RAG Optimization\", \"description\": \"Focus on embedding/KB alignment.\"}]"},
    {"id": "shutterfly-principal-swe", "name": "Shutterfly (Principal SWE)", "score": "A-", "priority": 1, "url": "https://shutterflycareers.ttcportals.com/jobs/17325169-principal-software-engineer", "dir": "tmp/prospects/shutterfly-principal-swe", "status": "Form Requested", "signals_json": "[{\"name\": \"Principal Title\", \"description\": \"Exact title match for career goals.\"}, {\"name\": \"Modernization\", \"description\": \"Architectural simplification of legacy substrates.\"}]"},
    {"id": "openai-senior-staff-b2b", "name": "OpenAI (Senior Staff SWE, B2B)", "score": "Strategic", "priority": 1, "url": "https://openai.com/careers/search/", "dir": "tmp/prospects/openai-senior-staff-b2b", "status": "Ready to Apply", "signals_json": "[{\"name\": \"Enterprise Scale\", \"description\": \"Focus on ChatGPT Enterprise substrates.\"}, {\"name\": \"Seniority Match\", \"description\": \"20-year history match.\"}]"},
    {"id": "openai-staff-data-eng", "name": "OpenAI (Staff Data Engineer)", "score": "A", "priority": 1, "url": "https://openai.com/careers/search/", "dir": "tmp/prospects/openai-staff-data-eng", "status": "Ready to Apply"},
    {"id": "openai-ai-deployment-codex", "name": "OpenAI (AI Deployment, Codex)", "score": "A", "priority": 1, "url": "https://openai.com/careers/search/", "dir": "tmp/prospects/openai-ai-deployment-codex", "status": "Ready to Apply"},
    {"id": "nvidia-dgx-cloud-staff", "name": "NVIDIA (Staff Full Stack, DGX Cloud)", "score": "A+", "priority": 1, "url": "https://nvidia.wd5.myworkdayjobs.com/en-US/NVIDIAExternalCareerSite/job/Senior-Full-Stack-Software-Engineer---DGX-Cloud_JR1985160", "dir": "tmp/prospects/nvidia-dgx-cloud-staff", "status": "Applied (5/17/2026)"},
    {"id": "nvidia-nim-sdk-staff", "name": "NVIDIA (Staff SWE, NIM SDK)", "score": "A", "priority": 1, "url": "https://nvidia.wd5.myworkdayjobs.com/en-US/NVIDIAExternalCareerSite/job/Senior-Software-Engineer---NIM-Platform-SDK-and-Framework_JR1984360", "dir": "tmp/prospects/nvidia-nim-sdk-staff", "status": "Ready to Apply"},
    {"id": "nvidia-rl-infra-staff", "name": "NVIDIA (Staff SWE, RL Infra)", "score": "A", "priority": 1, "url": "https://nvidia.wd5.myworkdayjobs.com/en-US/NVIDIAExternalCareerSite/job/Senior-Software-Engineer--RL-Post-Training-Frameworks_JR1984870", "dir": "tmp/prospects/nvidia-rl-infra-staff", "status": "Ready to Apply"},
    {"id": "nvidia-mods-principal", "name": "NVIDIA (Principal SWE, MODS)", "score": "Strategic", "priority": 1, "url": "https://nvidia.wd5.myworkdayjobs.com/en-US/NVIDIAExternalCareerSite/job/Principal-System-Software-Engineer---Data-Center-MODS_JR1983960", "dir": "tmp/prospects/nvidia-mods-principal", "status": "Ready to Apply"},
    {"id": "airbnb-data-authoring", "name": "Airbnb (Senior SWE, Data Authoring)", "score": "A", "priority": 1, "url": "https://careers.airbnb.com/positions/7094964/", "dir": "tmp/prospects/airbnb-data-authoring", "status": "Ready to Apply"},
    {"id": "netflix-ntech", "name": "Netflix (L5, Ntech Engineering)", "score": "Strategic", "priority": 1, "url": "https://explore.jobs.netflix.net/careers/job/790315937004", "dir": "tmp/prospects/netflix-ntech", "status": "Ready to Apply"},
    {"id": "netflix-experimentation", "name": "Netflix (L5, Experimentation)", "score": "Strategic", "priority": 1, "url": "https://explore.jobs.netflix.net/careers/job/790315090936", "dir": "tmp/prospects/netflix-experimentation", "status": "Ready to Apply"},
    {"id": "netflix-analysis", "name": "Netflix (L5, Analysis)", "score": "Strategic", "priority": 1, "url": "https://explore.jobs.netflix.net/careers/job/790315091079", "dir": "tmp/prospects/netflix-analysis", "status": "Ready to Apply"},
    
    # TIER 2 & OTHER ACTIVE
    {"id": "bigcommerce-lead", "name": "BigCommerce (Lead SWE)", "score": "A-", "priority": 2, "url": "https://bigcommerce.wd12.myworkdayjobs.com/Commerce/job/United-States---Remote/Lead-Software-Engineer_JR102268", "dir": "tmp/prospects/bigcommerce-lead", "status": "Ready to Apply"},
    {"id": "exact-sciences-safety", "name": "Exact Sciences (Lead AI Safety)", "score": "A+", "priority": 2, "url": "https://exactsciences.wd1.myworkdayjobs.com/", "dir": "tmp/prospects/exact-sciences-safety", "status": "Ready to Apply"},
    {"id": "smartsheet-applied-ai", "name": "Smartsheet (Applied AI)", "score": "A", "priority": 2, "url": "https://www.linkedin.com/jobs/view/4408629516/", "dir": "tmp/prospects/smartsheet-applied-ai", "status": "Ready to Apply"},
    {"id": "parspec-ai-search", "name": "Parspec (Staff SE AI Search)", "score": "A-", "priority": 2, "url": "https://www.linkedin.com/jobs/view/4402549136/", "dir": "tmp/prospects/parspec-ai-search", "status": "Ready to Apply"},
    {"id": "cresta", "name": "Cresta (Sr Backend AI)", "score": "B+", "priority": 2, "url": "https://www.linkedin.com/jobs/view/4408389248/", "dir": "tmp/prospects/cresta", "status": "Ready to Apply"},
    
    # APPLIED / IN PROGRESS
    {"id": "openai-principal", "name": "OpenAI - Principal Software Engineer", "score": "Strategic", "priority": 2, "url": "N/A", "dir": "tmp/prospects/openai", "status": "Applied (5/6/2026)"},
    {"id": "github-staff", "name": "GitHub (Staff SWE Deploys)", "score": "B", "priority": 2, "url": "https://www.linkedin.com/jobs/view/4388530833/", "dir": "tmp/prospects/github-staff", "status": "Applied"},
    {"id": "figma-ai-platform", "name": "Figma (AI Platforms)", "score": "A+", "priority": 2, "url": "https://www.figma.com/careers/", "dir": "tmp/prospects/figma-ai-platform", "status": "Applied"},
    {"id": "figma-data", "name": "Figma (Data Platform)", "score": "A-", "priority": 2, "url": "https://figma.com/careers", "dir": "tmp/prospects/figma", "status": "Applied"},
    {"id": "webflow-ai", "name": "Webflow (Applied AI)", "score": "A+", "priority": 2, "url": "https://job-boards.greenhouse.io/webflow/jobs/7271678", "dir": "tmp/prospects/webflow/applied_ai", "status": "Applied"},
    {"id": "spoton", "name": "SpotOn (Staff AI)", "score": "A+", "priority": 2, "url": "https://www.linkedin.com/jobs/view/4378033728", "dir": "tmp/prospects/spoton", "status": "Applied"},
    {"id": "mozilla-0to1", "name": "Mozilla (0to1 Engineer)", "score": "A+", "priority": 2, "url": "https://www.mozilla.org/en-US/careers/listings/?gh_jid=6394444", "dir": "tmp/prospects/mozilla-0to1", "status": "Applied"},
    {"id": "netflix-data", "name": "Netflix (Data/Feature Infra)", "score": "A-", "priority": 2, "url": "https://www.linkedin.com/jobs/view/4118836224/", "dir": "tmp/prospects/netflix-data", "status": "Applied"},
    {"id": "roblox-reliability", "name": "Roblox (Principal AI/ML Reliability)", "score": "A", "priority": 2, "url": "https://www.linkedin.com/jobs/view/4359872107/", "dir": "tmp/prospects/roblox-reliability", "status": "Applied"},
    
    # HISTORICAL / REJECTED
    {"id": "manju-edify", "name": "Edify (Data Engineer)", "score": "F", "priority": 4, "url": "N/A", "dir": "tmp/prospects/manju-c", "status": "Rejected"},
    {"id": "kinimatic", "name": "Kinimatic", "score": "N/A", "priority": 4, "url": "https://kinimatic.com/", "dir": "tmp/prospects/kinimatic", "status": "Rejected"},
    {"id": "manifest", "name": "Manifest", "score": "N/A", "priority": 4, "url": "https://manifest.eco/", "dir": "tmp/prospects/manifest", "status": "Rejected"},
    {"id": "summit", "name": "Summit", "score": "N/A", "priority": 4, "url": "https://summitcreditunion.com/careers", "dir": "tmp/prospects/summit", "status": "Rejected"},
    {"id": "ccap", "name": "CCAP (SE IV)", "score": "N/A", "priority": 4, "url": "https://www.wicourts.gov/about/jobs/index.htm", "dir": "tmp/prospects/ccap", "status": "Rejected"},
    {"id": "walmart-onsite", "name": "Walmart (On-site CA)", "score": "N/A", "priority": 4, "url": "https://walmart.com/careers", "dir": "tmp/prospects/walmart-onsite", "status": "Rejected"}
]

def main():
    repo = SQLiteJobRepository("jobs.db")
    existing_jobs = {j.id: j for j in repo.list_jobs()}
    
    print(f"Consolidating {len(static_prospects)} static jobs into SQLite...")
    
    # Track which jobs were seen in static list
    static_ids = set()
    
    for sp in static_prospects:
        job_id = sp["id"]
        static_ids.add(job_id)
        
        # New job or Update metadata
        new_job = JobOpportunity(
            id=job_id,
            name=sp["name"],
            score=sp["score"],
            priority=sp["priority"],
            url=sp["url"],
            dir=sp["dir"],
            status=sp["status"], # FORCE static status to fix the "funky" dashboard
            signals_json=sp.get("signals_json")
        )
        repo.save_job(new_job)
        print(f" Syncing job: {job_id} -> {new_job.status}")

    print("Sync complete.")

if __name__ == "__main__":
    main()
