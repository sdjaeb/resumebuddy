import asyncio
import typer
from rich import print
from rich.table import Table
from typing import Optional
import os
import json
from urllib.parse import urlparse
from .ollama_client import OllamaClient
from .analyzer import Analyzer
from .generator import Generator
from .researcher import Researcher
from .scraper import JobScraper
from .discovery import JobDiscovery, save_prospective_jobs
from .profile_manager import ProfileManager
from .models import UserProfile

app = typer.Typer(help="ResumeBuddy: Review, Tune, and Update Resumes.")

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
    researcher = Researcher(OllamaClient())
    intel = researcher.get_company_intel(company)
    if intel:
        print(Markdown(intel))
    else:
        print(f"[bold red]No intel found for {company}.[/bold red] Run 'research' first.")

@app.command()
def profile():
    """Interactively build and save a job search profile."""
    ProfileManager.interactive_build()

@app.command()
def research(
    company: str = typer.Argument(..., help="Company name to research"),
    model: Optional[str] = typer.Option(None, "--model", help="Model name to override (e.g., llama3.2:3b)")
):
    """Research a company's news, layoffs, and performance."""
    client = OllamaClient()
    researcher = Researcher(client)

    async def _run():
        print(f"[bold blue]Gathering intel on {company}...[/bold blue]")
        intel = await researcher.research_company(company, model=model)
        print(f"\n[bold green]Intel for {company}:[/bold green]")
        print(f"[bold]Status:[/bold] {intel.get('status')}")
        print(f"[bold]Layoffs:[/bold] {intel.get('layoffs')}")
        print(f"[bold]Sentiment:[/bold] {intel.get('overall_sentiment')}")

    asyncio.run(_run())

@app.command()
def fetch(
    limit: int = typer.Option(20, help="Max jobs to fetch per site")
):
    """Fetch new job listings and save to prospective_jobs.jsonl."""
    discovery = JobDiscovery()
    sites = [
        ("Kentik", "https://www.kentik.com/careers/"),
        ("Cohere", "https://cohere.com/jobs"),
        ("LivaNova", "https://careers.livanova.com/"),
        ("NVIDIA", "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite"),
        ("Intel", "https://intel.wd1.myworkdayjobs.com/External"),
        ("Sony", "https://sony.wd1.myworkdayjobs.com/Sony_Interactive_Entertainment_External_Career_Site"),
        ("AMD", "https://amd.wd1.myworkdayjobs.com/External"),
        ("Anthropic", "https://jobs.lever.co/anthropic"),
        ("OpenAI", "https://openai.com/careers/search"),
        ("Mozilla", "https://www.mozilla.org/en-US/careers/listings/"),
        ("WeWorkRemotely", "https://weworkremotely.com/categories/remote-back-end-programming-jobs"),
        ("Remotive", "https://remotive.com/remote-jobs/software-dev"),
        ("RemoteOK", "https://remoteok.com/remote-backend-jobs"),
        ("Working Nomads", "https://www.workingnomads.com/jobs?category=development"),
    ]

    async def _run():
        all_jobs = []
        for name, url in sites:
            print(f"[bold blue]Discovering jobs on {name}...[/bold blue]")
            jobs = await discovery.discover_jobs(name, url)
            print(f"  Found {len(jobs)} prospective roles.")
            all_jobs.extend(jobs)
        
        save_prospective_jobs(all_jobs)
        print(f"\n[bold green]Saved {len(all_jobs)} jobs to prospective_jobs.jsonl[/bold green]")

    asyncio.run(_run())

@app.command()
def evaluate(
    resume_path: str = typer.Option(..., "--resume", help="Path to resume"),
    jd_source: Optional[str] = typer.Option(None, "--jd", help="Path to JD file or a URL"),
    job_index: Optional[int] = typer.Option(None, "--index", help="Index of job in prospective_jobs.jsonl"),
    company: Optional[str] = typer.Option(None, "--company", help="Company name for intel"),
    model: Optional[str] = typer.Option(None, "--model", help="Model name to override (e.g., llama3.2:3b)")
):
    """A-F evaluation of a role based on Career-Ops scoring (12 dimensions)."""
    try:
        resume_text = load_file(resume_path)
    except FileNotFoundError as e:
        print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)

    client = OllamaClient()
    analyzer = Analyzer(client)
    researcher = Researcher(client)
    scraper = JobScraper()

    async def _run():
        target_url = jd_source
        company_name = company

        # If index is provided, load from JSONL
        if job_index is not None:
            if not os.path.exists("prospective_jobs.jsonl"):
                print("[bold red]Error:[/bold red] prospective_jobs.jsonl not found. Run 'fetch' first.")
                return
            
            with open("prospective_jobs.jsonl", "r") as f:
                lines = f.readlines()
                if 0 <= job_index < len(lines):
                    job_data = json.loads(lines[job_index])
                    target_url = job_data.get('url')
                    company_name = company_name or job_data.get('company')
                    print(f"[bold blue]Evaluating job {job_index}: {job_data.get('title')} at {company_name}[/bold blue]")
                else:
                    print(f"[bold red]Error:[/bold red] Index {job_index} out of range.")
                    return

        if not target_url:
            print("[bold red]Error:[/bold red] Must provide --jd or --index.")
            return

        # Handle JD Source (File or URL)
        if target_url.startswith("http"):
            print(f"[bold blue]Scraping job from URL:[/bold blue] {target_url}")
            jd_data = await scraper.scrape_job(target_url)
        else:
            print(f"[bold blue]Loading JD from file:[/bold blue] {target_url}")
            content = load_file(target_url)
            if target_url.endswith(".html"):
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(content, 'html.parser')
                # Try to find common content areas or just get all text
                content = soup.get_text(separator='\n', strip=True)
            jd_data = {"description": content, "title": "Local File", "posted_at": "Unknown", "is_repost": False}

        if not company_name and target_url.startswith("http"):
             # Infer company from domain if not provided
             parsed_url = urlparse(target_url)
             if "greenhouse.io" in parsed_url.netloc:
                 company_name = parsed_url.path.split('/')[1].capitalize()
             else:
                 domain_parts = parsed_url.netloc.split('.')
                 company_name = domain_parts[1].capitalize() if len(domain_parts) > 2 else domain_parts[0].capitalize()

        company_intel = None
        if company_name:
            print(f"[bold blue]Checking KB for {company_name} intel...[/bold blue]")
            company_intel = researcher.get_company_intel(company_name)
            if not company_intel:
                print(f"[yellow]No local intel found for {company_name}. Researching now...[/yellow]")
                await researcher.research_company(company_name, model=model)
                company_intel = researcher.get_company_intel(company_name)

        print(f"[bold blue]Evaluating role...[/bold blue]")
        user_profile = ProfileManager.load_profile()
        result = await analyzer.evaluate_role(resume_text, jd_data, company_intel, model=model, profile=user_profile)
        
        if "error" in result:
            print(f"[bold red]Error during evaluation:[/bold red] {result['error']}")
            return

        print(f"\n[bold green]Overall Score:[/bold green] [bold white on blue] {result.get('overall_score', 'N/A')} [/bold white on blue]")
        
        table = Table(title="Dimension Scores")
        table.add_column("Dimension", style="cyan")
        table.add_column("Score", style="magenta")
        
        dimension_scores = result.get("dimension_scores", {})
        if isinstance(dimension_scores, dict):
            for dim, score in dimension_scores.items():
                if isinstance(score, dict):
                    score_str = json.dumps(score)
                else:
                    score_str = str(score)
                table.add_row(str(dim), score_str)
        
        print(table)
        print(f"\n[bold white]Rationale:[/bold white]\n{result.get('rationale', 'No rationale provided.')}")

    asyncio.run(_run())

@app.command()
def cover_letter(
    resume_path: str = typer.Option(..., "--resume", help="Path to resume"),
    jd_source: str = typer.Option(..., "--jd", help="Path to JD file or a URL"),
    model: Optional[str] = typer.Option(None, "--model", help="Model name to override (e.g., llama3.2:3b)")
):
    """Generate a targeted cover letter."""
    try:
        resume_text = load_file(resume_path)
    except FileNotFoundError as e:
        print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)

    client = OllamaClient()
    analyzer = Analyzer(client)
    generator = Generator(client)
    scraper = JobScraper()

    async def _run():
        if jd_source.startswith("http"):
            print(f"[bold blue]Scraping job from URL:[/bold blue] {jd_source}")
            jd_data = await scraper.scrape_job(jd_source)
            jd_text = jd_data.get('description', '')
        else:
            print(f"[bold blue]Loading JD from file:[/bold blue] {jd_source}")
            jd_text = load_file(jd_source)

        print(f"[bold blue]Analyzing alignment...[/bold blue]")
        alignment = await analyzer.analyze_alignment(resume_text, jd_text)
        print(f"[bold blue]Generating cover letter...[/bold blue]")
        cover_letter_text = await generator.generate_cover_letter(resume_text, jd_text, alignment, model=model)
        print("\n[bold magenta]Targeted Cover Letter:[/bold magenta]\n")
        print(cover_letter_text)

    asyncio.run(_run())

if __name__ == "__main__":
    app()
