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
    {"id": "roblox-reliability", "name": "Roblox (Principal AI/ML Reliability)", "score": "A", "priority": 1, "url": "https://www.linkedin.com/jobs/view/4359872107/", "dir": "tmp/prospects/roblox-reliability", "status": "Applied"},
    {"id": "archetype-ai", "name": "Archetype AI (Staff SWE)", "score": "A", "priority": 1, "url": "https://www.linkedin.com/jobs/view/4368780244/", "dir": "tmp/prospects/archetype-ai", "status": "Ready to Apply"},
    {"id": "onxmaps", "name": "onXmaps (Staff AI)", "score": "A", "priority": 1, "url": "https://www.onxmaps.com/careers", "dir": "tmp/prospects/onxmaps", "status": "Applied"},
    {"id": "coinbase-staff-ml", "name": "Coinbase (Staff ML Infra)", "score": "A", "priority": 1, "url": "https://www.coinbase.com/careers/positions/6253457", "dir": "tmp/prospects/coinbase-staff-ml", "status": "Ready to Apply"},
    {"id": "nxtlevel-agentic-ai", "name": "Nxt Level #3671 (Agentic AI)", "score": "A+", "priority": 1, "url": "https://nxtlevel.io/openjobs/", "dir": "tmp/prospects/nxtlevel-agentic-ai", "status": "Ready to Apply"},
    {"id": "nxtlevel-genai-workflows", "name": "Nxt Level #3706 (GenAI Workflows)", "score": "A+", "priority": 1, "url": "https://nxtlevel.io/openjobs/", "dir": "tmp/prospects/nxtlevel-genai-workflows", "status": "Ready to Apply"},
    {"id": "wellington-management", "name": "Wellington Management (Principal)", "score": "A+", "priority": 1, "url": "https://www.linkedin.com/jobs/view/4398000651/", "dir": "tmp/prospects/wellington-management", "status": "Ready to Apply"},
    {"id": "mozilla-0to1", "name": "Mozilla (0to1 Engineer)", "score": "A+", "priority": 1, "url": "https://www.mozilla.org/en-US/careers/listings/?gh_jid=6394444", "dir": "tmp/prospects/mozilla-0to1", "status": "Applied"},
    {"id": "spoton", "name": "SpotOn (Staff AI)", "score": "A+", "priority": 1, "url": "https://www.linkedin.com/jobs/view/4378033728", "dir": "tmp/prospects/spoton", "status": "Applied"},
    {"id": "webflow-ai", "name": "Webflow (Applied AI)", "score": "A+", "priority": 1, "url": "https://job-boards.greenhouse.io/webflow/jobs/7271678", "dir": "tmp/prospects/webflow/applied_ai", "status": "Applied"},
    {"id": "figma-ai-platform", "name": "Figma (AI Platforms)", "score": "A+", "priority": 1, "url": "https://www.figma.com/careers/", "dir": "tmp/prospects/figma-ai-platform", "status": "Applied"},
    {"id": "parspec-ai-search", "name": "Parspec (Staff SE AI Search)", "score": "A-", "priority": 1, "url": "https://www.linkedin.com/jobs/view/4402549136/", "dir": "tmp/prospects/parspec-ai-search", "status": "Ready to Apply"},
    {"id": "figma-data", "name": "Figma (Data Platform)", "score": "A-", "priority": 1, "url": "https://figma.com/careers", "dir": "tmp/prospects/figma", "status": "Applied"},

    {"id": "cresta", "name": "Cresta (Sr Backend AI)", "score": "B+", "priority": 1, "url": "https://www.linkedin.com/jobs/view/4408389248/", "dir": "tmp/prospects/cresta", "status": "Ready to Apply"},
    {"id": "github-actions", "name": "GitHub (Senior SWE, Actions)", "score": "Strategic", "priority": 2, "url": "https://www.linkedin.com/jobs/view/4388530836/", "dir": "tmp/prospects/github-actions", "status": "Ready to Apply", "signals_json": "[{\"name\": \"Prestige Anchor\", \"is_positive\": true, \"icon\": \"⚓\", \"description\": \"GitHub/Microsoft brand is a career-defining credential.\"}, {\"name\": \"Scale Challenge\", \"is_positive\": true, \"icon\": \"📈\", \"description\": \"Opportunity to harden global-scale distributed systems.\"}, {\"name\": \"On-Call Burden\", \"is_positive\": false, \"icon\": \"🚨\", \"description\": \"24/7 rotating on-call is a high WLB penalty.\"}, {\"name\": \"Title Friction\", \"is_positive\": false, \"icon\": \"🏷️\", \"description\": \"Senior SWE title for a 20-year Lead Architect.\"}]"},
    {"id": "franklincovey-senior", "name": "FranklinCovey (Senior SWE)", "score": "B-", "priority": 2, "url": "https://www.linkedin.com/jobs/view/4398773344/", "dir": "tmp/prospects/franklincovey-senior", "status": "Ready to Apply"},
    {"id": "oaktree-ai", "name": "Oak Tree Software (AI Engineer)", "score": "C-", "priority": 3, "url": "https://www.linkedin.com/jobs/view/4409866239/", "dir": "tmp/prospects/oaktree-ai", "status": "Ready to Apply"},
    {"id": "yohr-govtech", "name": "YO HR (GovTech AI Lead)", "score": "B", "priority": 2, "url": "https://www.linkedin.com/jobs/view/4398460553/", "dir": "tmp/prospects/yohr-govtech", "status": "Ready to Apply", "signals_json": "[{\"name\": \"High Comp Whale\", \"is_positive\": true, \"icon\": \"🐋\", \"description\": \"Salary ceiling of $600k listed.\"}, {\"name\": \"GovCloud Mandate\", \"is_positive\": true, \"icon\": \"🛡️\", \"description\": \"Direct match for AI Safety and Compliance expertise.\"}, {\"name\": \"Recruiter Mystery\", \"is_positive\": false, \"icon\": \"🕵️\", \"description\": \"Recruiter-led post; actual client is undisclosed.\"}]"},
    {"id": "nxt-level", "name": "Nxt Level (Staff Data AI)", "score": "A", "priority": 2, "url": "https://www.linkedin.com/jobs/view/4409814544", "dir": "tmp/prospects/nxt-level", "status": "Ready to Apply"},
    {"id": "freewill", "name": "FreeWill (Lead AI-Native)", "score": "A-", "priority": 2, "url": "https://www.linkedin.com/jobs/view/4400596437", "dir": "tmp/custom/freewill", "status": "Ready to Apply"},
    {"id": "netflix-data", "name": "Netflix (Data/Feature Infra)", "score": "A-", "priority": 1, "url": "https://www.linkedin.com/jobs/view/4118836224/", "dir": "tmp/prospects/netflix-data", "status": "Ready to Apply", "signals_json": "[{\"name\": \"Total Whale\", \"is_positive\": true, \"icon\": \"🐋\", \"description\": \"Netflix compensation tier (up to $750k).\"}, {\"name\": \"Local Nexus\", \"is_positive\": true, \"icon\": \"🏠\", \"description\": \"McFarland, WI location signal suggests home-game recruiter.\"}, {\"name\": \"Scale Gap\", \"is_positive\": false, \"icon\": \"📈\", \"description\": \"May face L6 Staff gap in Netflix ecosystem.\"}]"},
    {"id": "github-staff", "name": "GitHub (Staff SWE Deploys)", "score": "B", "priority": 1, "url": "https://www.linkedin.com/jobs/view/4388530833/", "dir": "tmp/prospects/github-staff", "status": "Ready to Apply", "signals_json": "[{\"name\": \"Title Preservation\", \"is_positive\": true, \"icon\": \"🏷️\", \"description\": \"Staff-level role preserves your architectural leverage.\"}, {\"name\": \"Platform Core\", \"is_positive\": true, \"icon\": \"🏗️\", \"description\": \"Owning the systems that ship GitHub.com.\"}]"},
    {"id": "zillow-data", "name": "Zillow (Senior Big Data)", "score": "B", "priority": 2, "url": "https://www.linkedin.com/jobs/view/4342095996/", "dir": "tmp/prospects/zillow-data", "status": "Ready to Apply"},
    {"id": "nuclearn", "name": "Nuclearn (AI Infra)", "score": "B+", "priority": 2, "url": "https://www.nuclearn.ai/careers", "dir": "tmp/prospects/nuclearn", "status": "Applied"},
    {"id": "eleventh-hour", "name": "Eleventh Hour Games (Tools)", "score": "B+", "priority": 2, "url": "https://www.linkedin.com/jobs/view/4388575371", "dir": "tmp/prospects/eleventh-hour-games", "status": "Ready to Apply"},
    {"id": "immuta-staff", "name": "Immuta (Staff Data Engineer)", "score": "B+", "priority": 2, "url": "https://www.immuta.com/careers/jobs/?gh_jid=6253457", "dir": "tmp/prospects/immuta-staff", "status": "Ready to Apply"},
    {"id": "yahoo-senior", "name": "Yahoo (Senior SWE)", "score": "B+", "priority": 2, "url": "https://www.linkedin.com/jobs/view/4359872107/", "dir": "tmp/prospects/yahoo-senior", "status": "Ready to Apply"},
    {"id": "plura-ai", "name": "Plura (Real-Time AI)", "score": "A-", "priority": 2, "url": "https://plura.ai/careers", "dir": "tmp/prospects/Plura", "status": "Ready to Apply", "signals_json": "[{\"name\": \"Concurrency\", \"is_positive\": true, \"icon\": \"⚡\", \"description\": \"Sub-second response engine challenges.\"}, {\"name\": \"Memory-Aware\", \"is_positive\": true, \"icon\": \"🧠\", \"description\": \"Focus on AI memory and real-time WebSocket orchestration.\"}]"},
    {"id": "together-ai", "name": "Together AI (Systems)", "score": "B-", "priority": 2, "url": "https://www.together.ai/careers", "dir": "tmp/prospects/together_ai", "status": "Ready to Apply"},
    {"id": "proxify-ai", "name": "Proxify (Senior AI Engineer)", "score": "B", "priority": 2, "url": "https://www.workingnomads.com/jobs/senior-python-ai-engineer-proxify-1566714", "dir": "tmp/prospects/proxify-ai", "status": "Ready to Apply"},
    {"id": "proxify-python", "name": "Proxify (Senior Backend Python)", "score": "B", "priority": 2, "url": "https://www.workingnomads.com/jobs/senior-backend-developer-python-proxify-1566664", "dir": "tmp/prospects/proxify-python", "status": "Ready to Apply"},
    {"id": "lemon-io-fullstack", "name": "Lemon.io (Senior Full-stack)", "score": "B-", "priority": 2, "url": "https://www.workingnomads.com/jobs/senior-full-stack-developer-lemonio-1527145", "dir": "tmp/prospects/lemon-io-fullstack", "status": "Ready to Apply"},
    {"id": "mozilla-senior", "name": "Mozilla (Senior Data Engineer)", "score": "B", "priority": 3, "url": "https://www.mozilla.org/en-US/careers/position/gh/7728023/", "dir": "tmp/custom", "status": "Applied"},
    {"id": "wolters-kluwer", "name": "Wolters Kluwer (AI Agents)", "score": "B", "priority": 3, "url": "https://www.linkedin.com/jobs/view/4316637878", "dir": "tmp/prospects/wolters-kluwer", "status": "Ready to Apply"},
    {"id": "indusvalley-gov", "name": "INDUSVALLEY (Data Governance Lead)", "score": "B", "priority": 3, "url": "mailto:rami@indusvalley.com", "dir": "tmp/prospects/indusvalley-gov", "status": "Ready to Apply"},
    {"id": "nvisia", "name": "nvisia (Technical Principal)", "score": "A-", "priority": 3, "url": "https://www.nvisia.com/who-we-are/careers-in-technology", "dir": "tmp/prospects/nvisia", "status": "Interview Scheduled", "signals_json": "[{\"name\": \"AI Focused\", \"is_positive\": true, \"icon\": \"🤖\", \"description\": \"Nearly all work is AI/ML focused.\"}, {\"name\": \"Remote Friendly\", \"is_positive\": true, \"icon\": \"🏠\", \"description\": \"98% remote with manageable regional travel.\"}, {\"name\": \"Mentor Role\", \"is_positive\": true, \"icon\": \"👨‍🏫\", \"description\": \"Opportunity to mentor others without direct reports.\"}, {\"name\": \"Solutioning Focus\", \"is_positive\": false, \"icon\": \"📝\", \"description\": \"Fair bit of solutioning/specs vs hands-on coding.\"}]"},
    {"id": "smartsheet-applied-ai", "name": "Smartsheet (Applied AI)", "score": "A", "priority": 1, "url": "https://www.linkedin.com/jobs/view/4408629516/", "dir": "tmp/prospects/smartsheet-applied-ai", "status": "Ready to Apply", "signals_json": "[{\"name\": \"Platform Fit\", \"is_positive\": true, \"icon\": \"🏗️\", \"description\": \"Direct match for building 'Golden Path' APIs and internal platforms.\"}, {\"name\": \"Trust/Safety Match\", \"is_positive\": true, \"icon\": \"🛡️\", \"description\": \"Strong alignment with your focus on AI Safety and Observability.\"}, {\"name\": \"K8s Gap\", \"is_positive\": false, \"icon\": \"☸️\", \"description\": \"JD prefers EKS; your background is Fargate/Serverless.\"}, {\"name\": \"Salary Upside\", \"is_positive\": true, \"icon\": \"💰\", \"description\": \"Potential range up to $245k.\"}]"},
    {"id": "insight-global-genai", "name": "Insight Global (GenAI Lead)", "score": "B-", "priority": 2, "url": "mailto:derek.yardley@insightglobal.com", "dir": "tmp/prospects/insight-global-genai", "status": "Ready to Apply"},
    {"id": "ladders-healthcare-staff", "name": "Ladders (Healthcare Staff Data Eng)", "score": "C+", "priority": 3, "url": "https://www.linkedin.com/jobs/view/4407771032/", "dir": "tmp/prospects/ladders-healthcare-staff", "status": "Ready to Apply"},
    {"id": "allspice-backend", "name": "AllSpice (Senior Backend)", "score": "B", "priority": 2, "url": "https://jobs.ashbyhq.com/allspice/9d46d986-a00c-4f4c-b77a-4b7e14761f23", "dir": "tmp/prospects/allspice-backend", "status": "Ready to Apply", "signals_json": "[{\"name\": \"Founding Impact\", \"is_positive\": true, \"icon\": \"🏗️\", \"description\": \"Opportunity to define the CI/CD standard for the hardware industry.\"}, {\"name\": \"High Autonomy\", \"is_positive\": true, \"icon\": \"🗽\", \"description\": \"Series A environment with significant independence.\"}, {\"name\": \"Deployment Load\", \"is_positive\": false, \"icon\": \"🛠️\", \"description\": \"'Forward Deployed' means high client-facing/custom script burden.\"}, {\"name\": \"Series A Risk\", \"is_positive\": false, \"icon\": \"⚠️\", \"description\": \"Typical startup volatility vs. your preference for stability.\"}]"},
    {"id": "exact-sciences-safety", "name": "Exact Sciences (Lead AI Safety)", "score": "A+", "priority": 1, "url": "https://exactsciences.wd1.myworkdayjobs.com/en-US/Exact_Sciences/job/US---WI---Madison/Lead-AI-Safety-and-Enablement-Engineer_R25-11767", "dir": "tmp/prospects/exact-sciences-safety", "status": "Ready to Apply", "signals_json": "[{\"name\": \"The Unicorn\", \"is_positive\": true, \"icon\": \"🦄\", \"description\": \"Perfect intersection of Build, MLOps, and Governance.\"}, {\"name\": \"Madison Home Game\", \"is_positive\": true, \"icon\": \"🏠\", \"description\": \"Local on-site role with top-tier compensation.\"}, {\"name\": \"Harness Architect\", \"is_positive\": true, \"icon\": \"🛡️\", \"description\": \"Matches your specialization in technical AI Safety controls.\"}]"},
    {"id": "abbott-scientific", "name": "Abbott (Scientific Data Engineer)", "score": "B+", "priority": 3, "url": "https://exactsciences.wd1.myworkdayjobs.com/en-US/Exact_Sciences/job/US---CA---San-Diego/Senior-Scientific-Data-Engineer_R26-12627", "dir": "tmp/prospects/abbott", "status": "Applied"},
    {"id": "shipt", "name": "Shipt (Core Integrations)", "score": "B-", "priority": 3, "url": "https://www.linkedin.com/jobs/view/4400684521", "dir": "tmp/prospects/shipt", "status": "Ready to Apply"},
    {"id": "engaged-md", "name": "EngagedMD (Staff SWE)", "score": "C+", "priority": 3, "url": "https://www.linkedin.com/jobs/view/4369678878", "dir": "tmp/prospects/engaged-md", "status": "Ready to Apply"},
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
    
    for sp in static_prospects:
        job_id = sp["id"]
        
        if job_id in existing_jobs:
            # Update metadata but preserve content AND STATUS
            existing = existing_jobs[job_id]
            updated_job = JobOpportunity(
                id=job_id,
                name=sp["name"],
                score=sp["score"],
                priority=sp["priority"],
                url=sp["url"],
                dir=sp["dir"],
                status=existing.status or sp["status"], # Prefer DB status
                resume_content=existing.resume_content,
                cover_letter_content=existing.cover_letter_content,
                details_content=existing.details_content,
                signals_json=sp.get("signals_json") or existing.signals_json
            )
            repo.save_job(updated_job)
            print(f" Updated metadata for existing job: {job_id} (Preserved status: {updated_job.status})")
        else:
            # New job from static
            new_job = JobOpportunity(
                id=job_id,
                name=sp["name"],
                score=sp["score"],
                priority=sp["priority"],
                url=sp["url"],
                dir=sp["dir"],
                status=sp["status"],
                signals_json=sp.get("signals_json")
            )
            repo.save_job(new_job)
            print(f" Added new job to DB: {job_id}")

    print("Sync complete.")

if __name__ == "__main__":
    main()
