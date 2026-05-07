import asyncio
import typer
from rich import print
from typing import Optional
import os
import json

from resumebuddy.infrastructure.adapters.ollama import OllamaAdapter
from resumebuddy.infrastructure.adapters.mlx_adapter import MLXAdapter
from resumebuddy.infrastructure.adapters.scraper import BeautifulSoupScraperAdapter
from resumebuddy.infrastructure.adapters.discovery import JobDiscoveryAdapter
from resumebuddy.infrastructure.adapters.researcher import ResearcherAdapter
from resumebuddy.infrastructure.adapters.repository import FileSystemProfileRepository, SQLiteJobRepository
from resumebuddy.application.use_cases import ResumeBuddyUseCases
from resumebuddy.application.docx_generator import DocxGenerator
from resumebuddy.domain.models import UserProfile, JobOpportunity

app = typer.Typer(help="ResumeBuddy: Review, Tune, and Update Resumes.")

# Dependency Injection Setup
LLM_PROVIDER = os.getenv("RESUMEBUDDY_LLM_PROVIDER", "mlx").lower()

if LLM_PROVIDER == "mlx":
    model_path = os.getenv("RESUMEBUDDY_MLX_MODEL", "mlx-community/gemma-2-27b-it-4bit")
    llm_client = MLXAdapter(model_path=model_path)
else:
    llm_client = OllamaAdapter()

scraper = BeautifulSoupScraperAdapter()
discovery = JobDiscoveryAdapter(llm_client=llm_client)
researcher = ResearcherAdapter(llm_client)
profile_repo = FileSystemProfileRepository()
job_repo = SQLiteJobRepository("jobs.db")
use_cases = ResumeBuddyUseCases(llm_client)

PROFILE_PATH = "user_profile.json"

def load_file(path: str) -> str:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, "r") as f:
        return f.read()

@app.command()
def docx(
    input_path: str = typer.Argument(..., help="Path to the plain text resume"),
    output_path: Optional[str] = typer.Option(None, "--output", "-o", help="Output path for the .docx file")
):
    """Generate a formatted .docx resume from a text file (Overwrites existing)."""
    if not output_path:
        # Default to same name but .docx
        base = os.path.splitext(input_path)[0]
        output_path = base + ".docx"
            
    text = load_file(input_path)
    DocxGenerator.generate_resume(text, output_path)
    print(f"[bold green]Resume generated (overwritten if existed):[/bold green] {output_path}")

@app.command()
def docx_cv(
    input_path: str = typer.Option("cover_letter.txt", "--input", "-i", help="Path to the plain text cover letter"),
    output_path: Optional[str] = typer.Option(None, "--output", "-o", help="Output path for the .docx file")
):
    """Generate a formatted .docx cover letter from a text file (Overwrites existing)."""
    if not output_path:
        base = os.path.splitext(input_path)[0]
        output_path = base + ".docx"
            
    text = load_file(input_path)
    DocxGenerator.generate_resume(text, output_path)
    print(f"[bold green]Cover Letter generated (overwritten if existed):[/bold green] {output_path}")

@app.command()
def view(
    company: str = typer.Argument(..., help="Company name to view intel for")
):
    """View company intel from the Knowledge Base as a wiki."""
    from rich.markdown import Markdown
    intel = researcher.get_company_intel(company)
    if intel:
        print(Markdown(intel))
    else:
        print(f"[bold red]No intel found for {company}.[/bold red] Run 'research' first.")

@app.command()
def profile():
    """Interactively build and save a job search profile."""
    print("[bold blue]Job Search Profile Builder[/bold blue]")
    print("Press Enter to accept the sensible default for any field.\n")
    
    default_profile = UserProfile()
    
    def prompt_list(field_name: str, default_list: list) -> list:
        val = typer.prompt(f"{field_name} (comma-separated)", default=", ".join(default_list))
        return [x.strip() for x in val.split(",") if x.strip()]

    preferred_languages = prompt_list("Preferred Languages", default_profile.preferred_languages)
    supporting_languages = prompt_list("Supporting Languages", default_profile.supporting_languages)
    learning_interests = prompt_list("Learning Interests", default_profile.learning_interests)
    role_preferences = typer.prompt("Role Preferences", default=default_profile.role_preferences)
    location = typer.prompt("Location", default=default_profile.location)
    min_salary = typer.prompt("Min Salary", type=int, default=default_profile.min_salary)
    target_salary = typer.prompt("Target Salary", type=int, default=default_profile.target_salary)
    growth_exceptions = typer.prompt("Growth Exceptions", default=default_profile.growth_exceptions)
    company_stage_preferences = typer.prompt("Company Stage Preferences", default=default_profile.company_stage_preferences)
    travel_preference = typer.prompt("Travel Preference", default=default_profile.travel_preference)
    employment_type_preference = typer.prompt("Employment Type Preference", default=default_profile.employment_type_preference)
    wlb_preference = typer.prompt("WLB Preference", default=default_profile.wlb_preference)
    industry_interests = typer.prompt("Industry Interests", default=default_profile.industry_interests)
    clearance = typer.prompt("Clearance", default=default_profile.clearance)
    disqualified_companies = prompt_list("Disqualified Companies", default_profile.disqualified_companies)
    recent_applications = prompt_list("Recent Applications", default_profile.recent_applications)

    new_profile = UserProfile(
        preferred_languages=preferred_languages,
        supporting_languages=supporting_languages,
        learning_interests=learning_interests,
        role_preferences=role_preferences,
        location=location,
        min_salary=min_salary,
        target_salary=target_salary,
        growth_exceptions=growth_exceptions,
        company_stage_preferences=company_stage_preferences,
        travel_preference=travel_preference,
        employment_type_preference=employment_type_preference,
        wlb_preference=wlb_preference,
        industry_interests=industry_interests,
        clearance=clearance,
        disqualified_companies=disqualified_companies,
        recent_applications=recent_applications
    )
    
    profile_repo.save_profile(new_profile, PROFILE_PATH)
    print(f"[bold green]Profile saved to {PROFILE_PATH}[/bold green]")

@app.command()
def research(
    company: str = typer.Argument(..., help="Company name to research"),
    model: Optional[str] = typer.Option(None, "--model", help="Model name to override")
):
    """Research a company's news, layoffs, and performance."""
    async def _run():
        print(f"[bold blue]Gathering intel on {company}...[/bold blue]")
        intel = await researcher.research_company(company, model=model)
        if "error" in intel:
            print(f"[bold red]Error:[/bold red] {intel['error']}")
            return
        print(f"\n[bold green]Intel for {company}:[/bold green]")
        print(f"[bold]Status:[/bold] {intel.get('status')}")
        print(f"[bold]Layoffs:[/bold] {intel.get('layoffs')}")
        print(f"[bold]Sentiment:[/bold] {intel.get('overall_sentiment')}")

    asyncio.run(_run())

@app.command()
def fetch(
    agentic: bool = typer.Option(False, "--agentic", help="Use AI-powered search to find jobs on dynamic boards"),
    query: Optional[str] = typer.Option(None, "--query", help="Query for agentic discovery (e.g. 'Staff Backend AI Remote')")
):
    """Fetch new job listings and save to prospective_jobs.jsonl."""
    sites = [
        ("Kentik", "https://www.kentik.com/careers/"),
        ("NVIDIA", "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite"),
        ("Mozilla", "https://www.mozilla.org/en-US/careers/listings/"),
        ("Working Nomads", "https://www.workingnomads.com/jobs?category=development"),
    ]

    async def _run():
        all_jobs = []
        
        if agentic:
            search_query = query or "Staff Backend AI Engineer Remote US"
            print(f"[bold blue]Performing agentic discovery for: '{search_query}'...[/bold blue]")
            jobs = await discovery.discover_agentic(search_query)
            print(f"  Found {len(jobs)} prospective roles via AI search.")
            all_jobs.extend(jobs)
        else:
            for name, url in sites:
                print(f"[bold blue]Discovering jobs on {name}...[/bold blue]")
                jobs = await discovery.discover_jobs(name, url)
                print(f"  Found {len(jobs)} prospective roles.")
                all_jobs.extend(jobs)
        
        if all_jobs:
            with open("prospective_jobs.jsonl", "a") as f:
                for job in all_jobs:
                    f.write(json.dumps(job) + "\n")
            print(f"\n[bold green]Saved {len(all_jobs)} jobs to prospective_jobs.jsonl[/bold green]")
        else:
            print("[bold yellow]No new jobs found.[/bold yellow]")

    asyncio.run(_run())

@app.command()
def track(
    id: str = typer.Argument(..., help="Unique ID for the job"),
    name: str = typer.Argument(..., help="Display name for the job"),
    url: str = typer.Argument(..., help="URL of the job listing"),
    score: str = typer.Option("?", "--score", help="Alignment score"),
    priority: int = typer.Option(2, "--priority", help="Tier/Priority (1-3)"),
    status: str = typer.Option("Ready to Apply", "--status", help="Current status"),
    dir: Optional[str] = typer.Option(None, "--dir", help="Directory for kits")
):
    """Manually add a job to the SQLite tracker."""
    job = JobOpportunity(
        id=id,
        name=name,
        score=score,
        priority=priority,
        url=url,
        dir=dir or f"tmp/prospects/{id}",
        status=status
    )
    job_repo.save_job(job)
    print(f"[bold green]Job tracked:[/bold green] {name} ({id})")

@app.command()
def tailor(
    resume_path: str = typer.Option(..., "--resume", help="Path to resume"),
    jd_source: str = typer.Option(..., "--jd", help="Path to JD file or a URL"),
    output: str = typer.Option("tailored_resume.txt", "--output", help="Output path")
):
    """Generate an optimized, tailored resume for a specific role."""
    async def _run():
        resume_text = load_file(resume_path)
        if jd_source.startswith("http"):
            jd_data = await scraper.scrape_job(jd_source)
            jd_text = jd_data.get('description', '')
        else:
            jd_text = load_file(jd_source)

        alignment = await use_cases.analyze_alignment(resume_text, jd_text)
        optimized = await use_cases.optimize_resume(resume_text, jd_text, alignment)
        
        with open(output, "w") as f:
            f.write(optimized)
        print(f"[bold green]Tailored resume saved to {output}[/bold green]")

    asyncio.run(_run())

@app.command()
def kit(
    company: str = typer.Argument(..., help="Company name"),
    resume_path: str = typer.Option(..., "--resume", help="Path to base resume"),
    jd_source: str = typer.Option(..., "--jd", help="Path to JD file or a URL"),
    job_id: Optional[str] = typer.Option(None, "--id", help="Job ID in SQLite to update")
):
    """Generate a full career kit (Tailored Resume + Cover Letter) and update tracking."""
    async def _run():
        target_dir = f"tmp/prospects/{company.lower().replace(' ', '_')}"
        os.makedirs(target_dir, exist_ok=True)
        
        resume_text = load_file(resume_path)
        if jd_source.startswith("http"):
            jd_data = await scraper.scrape_job(jd_source)
            jd_text = jd_data.get('description', '')
        else:
            jd_text = load_file(jd_source)

        print(f"[bold blue]Generating kit for {company}...[/bold blue]")
        
        # 1. Alignment & Evaluation
        company_intel = researcher.get_company_intel(company)
        evaluation = await use_cases.evaluate_role(resume_text, jd_data, company_intel)
        with open(os.path.join(target_dir, "details.md"), "w") as f:
            f.write(f"# Evaluation: {company}\n\n## Score: {evaluation.overall_score}\n\n## Rationale\n{evaluation.rationale}")

        # 2. Alignment Analysis for optimization
        alignment = await use_cases.analyze_alignment(resume_text, jd_text)
        
        # 3. Tailored Resume
        optimized = await use_cases.optimize_resume(resume_text, jd_text, alignment)
        with open(os.path.join(target_dir, "resume.txt"), "w") as f:
            f.write(optimized)
            
        # 4. Cover Letter
        cv = await use_cases.generate_cover_letter(resume_text, jd_text, alignment)
        with open(os.path.join(target_dir, "cover_letter.txt"), "w") as f:
            f.write(cv)

        # 5. Update SQLite
        if job_id:
            job_repo.update_status(job_id, "Ready to Apply")
            # We should also update the dir in SQLite if we had that method, 
            # for now let's just use the job_repo to ensure status is set.
            with sqlite3.connect("jobs.db") as conn:
                conn.execute("UPDATE jobs SET dir = ?, score = ? WHERE id = ?", (target_dir, evaluation.overall_score, job_id))

        print(f"[bold green]Kit generated in {target_dir}[/bold green]")

    asyncio.run(_run())

@app.command()
def evaluate(
    resume_path: str = typer.Option(..., "--resume", help="Path to resume"),
    jd_source: Optional[str] = typer.Option(None, "--jd", help="Path to JD file or a URL"),
    job_index: Optional[int] = typer.Option(None, "--index", help="Index of job in prospective_jobs.jsonl"),
    company: Optional[str] = typer.Option(None, "--company", help="Company name for intel"),
    model: Optional[str] = typer.Option(None, "--model", help="Model name to override"),
    save: bool = typer.Option(False, "--save", help="Save the result to the SQLite tracker")
):
    """A-F evaluation of a role based on Career-Ops scoring."""
    async def _run():
        resume_text = load_file(resume_path)
        target_url = jd_source
        company_name = company

        if job_index is not None:
            with open("prospective_jobs.jsonl", "r") as f:
                lines = f.readlines()
                job_data = json.loads(lines[job_index])
                target_url = job_data.get('url')
                company_name = company_name or job_data.get('company')

        if target_url and target_url.startswith("http"):
            jd_data = await scraper.scrape_job(target_url)
        else:
            content = load_file(target_url) if target_url else "No JD provided."
            jd_data = {"description": content, "title": "Local", "posted_at": "Unknown", "is_repost": False}

        company_intel = researcher.get_company_intel(company_name) if company_name else None
        user_profile = profile_repo.load_profile(PROFILE_PATH)
        
        result = await use_cases.evaluate_role(resume_text, jd_data, company_intel, model=model, profile=user_profile)
        
        print(f"\n[bold green]Overall Score:[/bold green] {result.overall_score}")
        print(f"[bold white]Rationale:[/bold white]\n{result.rationale}")

        if save and company_name:
            job_id = company_name.lower().replace(" ", "-")
            job = JobOpportunity(
                id=job_id,
                name=f"{company_name} ({jd_data.get('title', 'Unknown')})",
                score=result.overall_score,
                priority=2, # Default to Tier 2
                url=target_url if (target_url and target_url.startswith("http")) else "",
                dir=f"tmp/prospects/{job_id}",
                status="Ready to Apply",
                resume_content=resume_text,
                details_content=result.rationale,
                signals_json=json.dumps([s.model_dump() for s in result.signals])
            )
            job_repo.save_job(job)
            print(f"[bold blue]Result saved to tracker as {job_id}[/bold blue]")

    asyncio.run(_run())

@app.command()
def cover_letter(
    resume_path: str = typer.Option(..., "--resume", help="Path to resume"),
    jd_source: str = typer.Option(..., "--jd", help="Path to JD file or a URL"),
    model: Optional[str] = typer.Option(None, "--model", help="Model name to override")
):
    """Generate a targeted cover letter."""
    async def _run():
        resume_text = load_file(resume_path)
        if jd_source.startswith("http"):
            jd_data = await scraper.scrape_job(jd_source)
            jd_text = jd_data.get('description', '')
        else:
            jd_text = load_file(jd_source)

        alignment = await use_cases.analyze_alignment(resume_text, jd_text)
        cv = await use_cases.generate_cover_letter(resume_text, jd_text, alignment, model=model)
        print(f"\n[bold magenta]Cover Letter:[/bold magenta]\n{cv}")

    asyncio.run(_run())

@app.command()
def prep(
    company: str = typer.Argument(..., help="Company name for the interview"),
    resume_path: str = typer.Option(..., "--resume", help="Path to your resume"),
    jd_source: Optional[str] = typer.Option(None, "--jd", help="Path to JD file or a URL"),
    model: Optional[str] = typer.Option(None, "--model", help="Model name to override")
):
    """Generate a strategic interview preparation guide."""
    async def _run():
        print(f"[bold blue]Preparing for your interview with {company}...[/bold blue]")
        resume_text = load_file(resume_path)
        
        jd_text = ""
        if jd_source:
            if jd_source.startswith("http"):
                jd_data = await scraper.scrape_job(jd_source)
                jd_text = jd_data.get('description', '')
                # Save JD to knowledge base
                kb_path = f"knowledge-base/companies/{company.lower().replace(' ', '_')}.md"
                if not os.path.exists(kb_path):
                    with open(kb_path, "w") as f:
                        f.write(f"# Company Intel: {company}\n\n## Job Description\n{jd_text}\n")
            else:
                jd_text = load_file(jd_source)

        company_intel = researcher.get_company_intel(company)
        
        prep_data = await use_cases.prepare_interview(resume_text, jd_text, company_intel, model=model)
        
        if "error" in prep_data:
            print(f"[bold red]Error:[/bold red] {prep_data['error']}")
            return

        print(f"\n[bold green]Interview Strategy for {company}[/bold green]")
        print(f"\n[bold cyan]Intro Statement:[/bold cyan]\n{prep_data.get('intro_statement')}")
        
        print(f"\n[bold cyan]STAR Items:[/bold cyan]")
        for item in prep_data.get('star_items', []):
            print(f"- [bold]{item.get('alignment')}[/bold]")
            print(f"  S/T: {item.get('situation')} / {item.get('task')}")
            print(f"  A/R: {item.get('action')} / {item.get('result')}")

        print(f"\n[bold cyan]Suggested Questions:[/bold cyan]")
        for q in prep_data.get('suggested_questions', []):
            print(f"- {q}")

        print(f"\n[bold cyan]Technical Refreshers:[/bold cyan]")
        for t in prep_data.get('technical_refreshers', []):
            print(f"- {t}")

        print(f"\n[bold yellow]Salary Strategy:[/bold yellow]\n{prep_data.get('salary_strategy')}")

    asyncio.run(_run())

if __name__ == "__main__":  # pragma: no cover
    app()
