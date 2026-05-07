import asyncio
import os
import json
from typing import Optional, List, Dict, Any
from mcp.server import Server
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server.stdio import stdio_server

from resumebuddy.infrastructure.adapters.repository import SQLiteJobRepository, FileSystemProfileRepository
from resumebuddy.infrastructure.adapters.scraper import BeautifulSoupScraperAdapter
from resumebuddy.infrastructure.adapters.researcher import ResearcherAdapter
from resumebuddy.infrastructure.adapters.ollama import OllamaAdapter # Default, though we might not use it much in MCP

# Initialize repositories
job_repo = SQLiteJobRepository("jobs.db")
profile_repo = FileSystemProfileRepository()
scraper = BeautifulSoupScraperAdapter()
# We still need a researcher/LLM for some internal operations if called, 
# but primarily we want to expose raw data to Gemini.
llm_client = OllamaAdapter() 
researcher = ResearcherAdapter(llm_client)

server = Server("resumebuddy")

@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available tools for resume and job management."""
    return [
        types.Tool(
            name="get_resume",
            description="Fetch the content of a resume file.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the resume.txt file", "default": "resume.txt"}
                }
            }
        ),
        types.Tool(
            name="scrape_job",
            description="Scrape job details from a URL.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL of the job listing"}
                },
                "required": ["url"]
            }
        ),
        types.Tool(
            name="list_jobs",
            description="List all jobs tracked in the SQLite database.",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="save_job",
            description="Save or update a job in the SQLite database.",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "score": {"type": "string"},
                    "priority": {"type": "integer"},
                    "url": {"type": "string"},
                    "dir": {"type": "string"},
                    "status": {"type": "string"}
                },
                "required": ["id", "name", "score", "priority", "url", "status"]
            }
        ),
        types.Tool(
            name="update_job_status",
            description="Update the status of a tracked job.",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {"type": "string"},
                    "status": {"type": "string", "enum": ["Ready to Apply", "Applied", "Interview Scheduled", "Accepted", "Rejected"]}
                },
                "required": ["job_id", "status"]
            }
        ),
        types.Tool(
            name="generate_kit",
            description="Generate a tailored resume and cover letter for a job.",
            inputSchema={
                "type": "object",
                "properties": {
                    "company": {"type": "string"},
                    "jd_url": {"type": "string"},
                    "job_id": {"type": "string"}
                },
                "required": ["company", "jd_url"]
            }
        ),
        types.Tool(
            name="get_company_intel",
            description="Fetch saved intel for a company from the knowledge base.",
            inputSchema={
                "type": "object",
                "properties": {
                    "company": {"type": "string"}
                },
                "required": ["company"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: Dict[str, Any]
) -> List[types.TextContent]:
    """Handle tool execution requests."""
    if name == "get_resume":
        path = arguments.get("path", "resume.txt")
        if not os.path.exists(path):
            return [types.TextContent(type="text", text=f"Error: {path} not found.")]
        with open(path, "r") as f:
            return [types.TextContent(type="text", text=f.read())]

    elif name == "scrape_job":
        url = arguments["url"]
        try:
            data = await scraper.scrape_job(url)
            return [types.TextContent(type="text", text=json.dumps(data, indent=2))]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error scraping job: {str(e)}")]

    elif name == "list_jobs":
        jobs = job_repo.list_jobs()
        return [types.TextContent(type="text", text=json.dumps([j.model_dump() for j in jobs], indent=2))]

    elif name == "save_job":
        from resumebuddy.domain.models import JobOpportunity
        job = JobOpportunity(
            id=arguments["id"],
            name=arguments["name"],
            score=arguments["score"],
            priority=arguments["priority"],
            url=arguments["url"],
            dir=arguments.get("dir", f"tmp/prospects/{arguments['id']}"),
            status=arguments["status"]
        )
        job_repo.save_job(job)
        return [types.TextContent(type="text", text=f"Job {job.name} saved successfully.")]

    elif name == "update_job_status":
        job_id = arguments["job_id"]
        status = arguments["status"]
        job_repo.update_status(job_id, status)
        return [types.TextContent(type="text", text=f"Status for job {job_id} updated to {status}.")]

    elif name == "generate_kit":
        company = arguments["company"]
        jd_url = arguments["jd_url"]
        job_id = arguments.get("job_id")
        
        target_dir = f"tmp/prospects/{company.lower().replace(' ', '_')}"
        os.makedirs(target_dir, exist_ok=True)
        
        with open("resume.txt", "r") as f:
            resume_text = f.read()
            
        jd_data = await scraper.scrape_job(jd_url)
        jd_text = jd_data.get('description', '')
        
        # We'll use the LLM to generate the kit
        from resumebuddy.application.use_cases import ResumeBuddyUseCases
        use_cases = ResumeBuddyUseCases(llm_client)
        
        # Alignment & Evaluation
        evaluation = await use_cases.evaluate_role(resume_text, jd_data)
        with open(os.path.join(target_dir, "details.md"), "w") as f:
            f.write(f"# Evaluation: {company}\n\n## Score: {evaluation.overall_score}\n\n## Rationale\n{evaluation.rationale}")

        alignment = await use_cases.analyze_alignment(resume_text, jd_text)
        
        # Resume
        optimized = await use_cases.optimize_resume(resume_text, jd_text, alignment)
        with open(os.path.join(target_dir, "resume.txt"), "w") as f:
            f.write(optimized)
            
        # Cover Letter
        cv = await use_cases.generate_cover_letter(resume_text, jd_text, alignment)
        with open(os.path.join(target_dir, "cover_letter.txt"), "w") as f:
            f.write(cv)

        if job_id:
            job_repo.update_status(job_id, "Ready to Apply")
            with sqlite3.connect("jobs.db") as conn:
                conn.execute("UPDATE jobs SET dir = ?, score = ? WHERE id = ?", (target_dir, evaluation.overall_score, job_id))

        return [types.TextContent(type="text", text=f"Kit generated successfully in {target_dir}. Score: {evaluation.overall_score}")]

    elif name == "get_company_intel":
        company = arguments["company"]
        intel = researcher.get_company_intel(company)
        if intel:
            return [types.TextContent(type="text", text=intel)]
        return [types.TextContent(type="text", text=f"No intel found for {company}.")]

    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    # Run the server using stdin/stdout streams
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="resumebuddy",
                server_version="0.1.0",
                capabilities=types.ServerCapabilities(
                    tools=types.ToolsCapability(listChanged=False)
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
