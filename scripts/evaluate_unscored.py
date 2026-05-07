import asyncio
import os
import sys
import json
from typing import Optional

# Add src to path
sys.path.append(os.path.abspath("src"))

from resumebuddy.infrastructure.adapters.mlx_adapter import MLXAdapter
from resumebuddy.infrastructure.adapters.researcher import ResearcherAdapter
from resumebuddy.infrastructure.adapters.scraper import BeautifulSoupScraperAdapter
from resumebuddy.infrastructure.adapters.repository import SQLiteJobRepository, FileSystemProfileRepository
from resumebuddy.application.use_cases import ResumeBuddyUseCases
from resumebuddy.domain.models import JobOpportunity

async def main():
    # Use MLX for stable local execution
    model_path = os.getenv("RESUMEBUDDY_MLX_MODEL", "mlx-community/gemma-2-9b-it-4bit")
    llm_client = MLXAdapter(model_path=model_path)
    researcher = ResearcherAdapter(llm_client)
    scraper = BeautifulSoupScraperAdapter()
    repo = SQLiteJobRepository("jobs.db")
    profile_repo = FileSystemProfileRepository()
    use_cases = ResumeBuddyUseCases(llm_client)
    
    # Load resume and profile
    if not os.path.exists("resume.txt"):
        print("Error: resume.txt not found")
        return
    with open("resume.txt", "r") as f:
        resume_text = f.read()
    
    user_profile = profile_repo.load_profile("user_profile.json")
    
    # Find jobs with '?' score
    unscored_jobs = [j for j in repo.list_jobs() if j.score == "?"]
    
    if not unscored_jobs:
        print("No unscored jobs ('?') found in database.")
        return

    print(f"Found {len(unscored_jobs)} unscored jobs. Starting evaluation...")

    for job in unscored_jobs:
        try:
            print(f"\n--- Evaluating {job.name} ({job.id}) ---")
            
            # 1. Scrape if description is missing or we need fresh data
            jd_data = {"description": "", "title": job.name, "company": job.name.split(" hiring ")[0] if " hiring " in job.name else job.name}
            if job.url and job.url.startswith("http"):
                print(f" Scraping {job.url}...")
                try:
                    jd_data = await scraper.scrape_job(job.url)
                except Exception as e:
                    print(f" Scraping failed: {e}")
            
            if not jd_data.get("description"):
                print(f" Skipping {job.id}: No description available.")
                continue

            # 2. Company Research (Metrics/Culture)
            company_name = jd_data.get("company", job.name)
            print(f" Researching {company_name}...")
            intel_data = await researcher.research_company(company_name)
            intel_text = researcher.get_company_intel(company_name)

            # 3. Evaluate
            print(f" Running evaluation with phi4...")
            evaluation = await use_cases.evaluate_role(
                resume_text, 
                jd_data, 
                company_intel=intel_text, 
                profile=user_profile
            )
            
            # 4. Save
            job.score = evaluation.overall_score
            job.status = "Evaluated"
            
            # Save evaluation details to file
            os.makedirs(job.dir, exist_ok=True)
            with open(os.path.join(job.dir, "evaluation.md"), "w") as f:
                f.write(f"# Evaluation for {job.name}\n\n")
                f.write(f"**Score:** {job.score}\n\n")
                f.write(f"## Rationale\n{evaluation.rationale}\n\n")
                if intel_text:
                    f.write(f"## Company Intel\n{intel_text}\n")
            
            repo.save_job(job)
            print(f" Saved: {job.name} -> {job.score}")

        except Exception as e:
            print(f" Error evaluating {job.id}: {e}")

    print("\nEvaluation batch complete.")

if __name__ == "__main__":
    asyncio.run(main())
