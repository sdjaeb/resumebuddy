import asyncio
import typer
from rich import print
from typing import Optional
import os
import json

from resumebuddy.infrastructure.adapters.ollama import OllamaAdapter
from resumebuddy.infrastructure.adapters.scraper import BeautifulSoupScraperAdapter
from resumebuddy.infrastructure.adapters.discovery import JobDiscoveryAdapter
from resumebuddy.infrastructure.adapters.researcher import ResearcherAdapter
from resumebuddy.infrastructure.adapters.repository import FileSystemProfileRepository
from resumebuddy.application.use_cases import ResumeBuddyUseCases
from resumebuddy.domain.models import UserProfile

app = typer.Typer(help="ResumeBuddy: Review, Tune, and Update Resumes.")

# Dependency Injection Setup
llm_client = OllamaAdapter()
scraper = BeautifulSoupScraperAdapter()
discovery = JobDiscoveryAdapter()
researcher = ResearcherAdapter(llm_client)
profile_repo = FileSystemProfileRepository()
use_cases = ResumeBuddyUseCases(llm_client)

PROFILE_PATH = "user_profile.json"

def load_file(path: str) -> str:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, "r") as f:
        return f.read()

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
def fetch():
    """Fetch new job listings and save to prospective_jobs.jsonl."""
    sites = [
        ("Kentik", "https://www.kentik.com/careers/"),
        ("NVIDIA", "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite"),
        ("Mozilla", "https://www.mozilla.org/en-US/careers/listings/"),
        ("Working Nomads", "https://www.workingnomads.com/jobs?category=development"),
    ]

    async def _run():
        all_jobs = []
        for name, url in sites:
            print(f"[bold blue]Discovering jobs on {name}...[/bold blue]")
            jobs = await discovery.discover_jobs(name, url)
            print(f"  Found {len(jobs)} prospective roles.")
            all_jobs.extend(jobs)
        
        with open("prospective_jobs.jsonl", "a") as f:
            for job in all_jobs:
                f.write(json.dumps(job) + "\n")
        print(f"\n[bold green]Saved {len(all_jobs)} jobs to prospective_jobs.jsonl[/bold green]")

    asyncio.run(_run())

@app.command()
def evaluate(
    resume_path: str = typer.Option(..., "--resume", help="Path to resume"),
    jd_source: Optional[str] = typer.Option(None, "--jd", help="Path to JD file or a URL"),
    job_index: Optional[int] = typer.Option(None, "--index", help="Index of job in prospective_jobs.jsonl"),
    company: Optional[str] = typer.Option(None, "--company", help="Company name for intel"),
    model: Optional[str] = typer.Option(None, "--model", help="Model name to override")
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

        if target_url.startswith("http"):
            jd_data = await scraper.scrape_job(target_url)
        else:
            jd_data = {"description": load_file(target_url), "title": "Local", "posted_at": "Unknown", "is_repost": False}

        company_intel = researcher.get_company_intel(company_name) if company_name else None
        user_profile = profile_repo.load_profile(PROFILE_PATH)
        
        result = await use_cases.evaluate_role(resume_text, jd_data, company_intel, model=model, profile=user_profile)
        
        print(f"\n[bold green]Overall Score:[/bold green] {result.get('overall_score', 'N/A')}")
        print(f"[bold white]Rationale:[/bold white]\n{result.get('rationale', 'N/A')}")

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

if __name__ == "__main__":  # pragma: no cover
    app()
