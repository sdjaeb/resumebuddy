import uvicorn
from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os

from resumebuddy.infrastructure.adapters.ollama import OllamaAdapter
from resumebuddy.infrastructure.adapters.mlx_adapter import MLXAdapter
from resumebuddy.infrastructure.adapters.repository import SQLiteJobRepository
from resumebuddy.application.use_cases import ResumeBuddyUseCases
from resumebuddy.application.docx_generator import DocxGenerator
from resumebuddy.domain.models import AlignmentAnalysis, JobOpportunity

app = FastAPI(title="Resumebuddy Live Bridge")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

LLM_PROVIDER = os.getenv("RESUMEBUDDY_LLM_PROVIDER", "mlx").lower()

if LLM_PROVIDER == "mlx":
    model_path = os.getenv("RESUMEBUDDY_MLX_MODEL", "mlx-community/gemma-2-9b-it-4bit")
    llm_client = MLXAdapter(model_path=model_path)
else:
    llm_client = OllamaAdapter()

use_cases = ResumeBuddyUseCases(llm_client)
job_repo = SQLiteJobRepository("jobs.db")

# --- Company Intel Logic (Shared with generate_dashboard.py) ---
COMPANY_MAPPING = {
    "Roblox": "roblox.md",
    "Exact Sciences": "exact_sciences.md",
    "Abbott": "exact_sciences.md",
    "nvisia": "nvisia.md",
    "Smartsheet": "smartsheet.md",
    "Wellington": "wellington_management.md",
    "Global Investment": "wellington_management.md",
    "Figma": "figma.md",
    "Webflow": "webflow.md",
    "Parspec": "parspec.md",
    "AI Search": "parspec.md",
    "Netflix": "netflix.md",
    "GitHub": "github.md",
    "Coinbase": "coinbase.md",
    "Zillow": "zillow.md",
    "Proxify": "proxify.md",
    "Cresta": "cresta.md",
    "Immuta": "immuta.md",
    "Together AI": "together_ai.md",
    "Wolters Kluwer": "wolters_kluwer.md",
    "INDUSVALLEY": "indusvalley.md",
    "Shipt": "shipt.md",
    "EngagedMD": "engagedmd.md",
    "Lemon.io": "lemon_io.md",
    "FranklinCovey": "franklincovey.md",
    "YO HR": "working_nomads.md",
    "Working Nomads": "working_nomads.md",
    "Archetype AI": "archetype_ai.md",
    "onXmaps": "onxmaps.md",
    "SpotOn": "spoton.md",
    "Mozilla": "mozilla.md",
    "AllSpice": "allspice.md",
    "Summit": "summit.md",
    "CCAP": "ccap.md",
    "Kinimatic": "kinimatic.md",
    "Walmart": "walmart.md",
    "Nxt Level": "nxt_level.md",
    "Yahoo": "yahoo.md",
    "Plaid": "plaid.md",
    "Oak Tree": "oak_tree_software.md",
    "Nuclearn": "nuclearn.md",
    "Eleventh Hour": "eleventh_hour_games.md",
    "FreeWill": "freewill.md",
    "Manifest": "manifest.md",
    "Insight Global": "insight_global.md",
    "Ladders": "ladders.md",
    "Plura": "plura.md",
    "Paramount": "paramount.md",
    "OpenAI": "openai.md",
    "Grafana Labs": "grafana_labs.md",
    "Planet DDS": "planet_dds.md"
}

def _load_intel(filename: str):
    path = os.path.join("knowledge-base", "companies", filename)
    if os.path.exists(path):
        with open(path, 'r') as f:
            content = f.read()
            grade = "N/A"
            for line in content.split('\n'):
                if "Maturity Grade:" in line or "Grade:" in line:
                    parts = line.split(":")
                    if len(parts) > 1:
                        grade = parts[1].strip().split(' ')[0]
            
            mission = ""
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if "## 1. The Mission" in line or "## Mission" in line:
                    if i + 1 < len(lines): mission = lines[i+1].strip()
                    break
            
            return grade, mission[:150] + "..." if len(mission) > 150 else mission
    return "N/A", ""

def get_job_intel(job_name: str):
    for key, filename in COMPANY_MAPPING.items():
        if key.lower() in job_name.lower():
            return _load_intel(filename)
    return "N/A", ""

# --- API Models ---
class ChatRequest(BaseModel):
    prompt: str
    context: Optional[str] = None

class ActionRequest(BaseModel):
    action: str
    job_id: str
    dir_path: str
    content: Optional[str] = None
    instructions: Optional[str] = None

class CouncilRequest(BaseModel):
    job_id: str
    dir_path: str

class StatusUpdate(BaseModel):
    status: str

@app.get("/jobs", response_model=List[JobOpportunity])
async def get_jobs():
    jobs = job_repo.list_jobs()
    for job in jobs:
        grade, mission = get_job_intel(job.name)
        job.company_grade = grade
        job.company_mission = mission
    return jobs

@app.put("/jobs/{job_id}/status")
async def update_job_status(job_id: str, update: StatusUpdate):
    job_repo.update_status(job_id, update.status)
    return {"status": "success"}

@app.post("/chat")
async def chat(request: ChatRequest):
    system_prompt = """You are Stephen Jaeb's specialized Career Agent. 
Your goal is to provide the EXACT text Stephen should use in a job application.
1. NEVER say 'As an AI' or 'I am an AI'.
2. ANSWER AS STEPHEN in the first person (I, me, my).
3. BE CONCISE. Limit answers to under 150 words.
4. NO PREAMBLE. Do not say 'Here is your answer' or 'Based on your profile'. Go straight to the response.
5. FOCUS on the specific job and company context provided.
6. Target the answer for a high-level Staff/Principal role."""
    
    full_prompt = f"{system_prompt}\n\nContext: {request.context}\n\nQuestion: {request.prompt}"
    response = await llm_client.complete_prompt(full_prompt)
    return {"response": response.strip()}

@app.post("/council")
async def invoke_council(request: CouncilRequest):
    details_path = os.path.join(request.dir_path, "details.md")
    if not os.path.exists(details_path):
        return {"response": "Error: details.md not found in " + request.dir_path}
        
    with open(details_path, "r") as f:
        job_details = f.read()
        
    prompt = f"""Run a 3-advisor mini-council (Contrarian, Expansionist, Chairman) for this role.
    
Job Context:
{job_details}

Provide:
1. Contrarian View (Risks)
2. Expansionist View (Upside)
3. Chairman's Verdict (Strategic Recommendation)

Return the results in a clean Markdown format.
"""
    response = await llm_client.complete_prompt(prompt)
    
    eval_path = os.path.join(request.dir_path, "evaluation.md")
    with open(eval_path, "w") as f:
        f.write(f"# LLM Council Deep-Dive\n\n{response}")
        
    return {"response": "Council verdict generated.", "verdict": response}

@app.post("/action")
async def perform_action(request: ActionRequest):
    if not os.path.exists(request.dir_path):
        return {"error": f"Directory not found: {request.dir_path}"}

    resume_path = os.path.join(request.dir_path, "resume.txt")
    
    if request.action == "docx_resume":
        content = request.content
        if not content:
            if not os.path.exists(resume_path):
                return {"error": f"resume.txt not found in {request.dir_path}"}
            with open(resume_path, "r") as f: content = f.read()
        
        out_path = os.path.join(request.dir_path, "resume.docx")
        DocxGenerator.generate_resume(content, out_path)
        return {"response": f"DOCX Resume generated at {out_path}"}

    if request.action == "docx_cv":
        content = request.content
        if not content:
            cv_path = os.path.join(request.dir_path, "cover_letter.txt")
            if not os.path.exists(cv_path):
                return {"error": "cover_letter.txt not found"}
            with open(cv_path, "r") as f: content = f.read()
            
        out_path = os.path.join(request.dir_path, "cover_letter.docx")
        DocxGenerator.generate_resume(content, out_path)
        return {"response": f"DOCX Cover Letter generated at {out_path}"}

    if not os.path.exists(resume_path):
        return {"error": f"resume.txt not found in {request.dir_path}"}
    with open(resume_path, "r") as f: resume_text = f.read()
        
    jd_context = f"Role: {request.job_id} in {request.dir_path}"
    details_path = os.path.join(request.dir_path, "details.md")
    if os.path.exists(details_path):
        with open(details_path, "r") as f:
            jd_context = f.read()
    
    if request.action == "cover_letter":
        alignment = AlignmentAnalysis(
            matching_skills=[], missing_skills=[], tangential_matches={}, alignment_summary="Regenerated via Live Bridge"
        )
        result = await use_cases.generate_cover_letter(resume_text, jd_context, alignment)
        with open(os.path.join(request.dir_path, "cover_letter.txt"), "w") as f:
            f.write(result)
        job_repo.update_content(request.job_id, cv=result)
        return {"response": "Cover letter regenerated and saved.", "content": result}

    return {"error": "Unknown action"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
