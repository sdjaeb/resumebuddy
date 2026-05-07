import asyncio
import os
import sys
import json
import hashlib
from typing import List

# Add src to path
sys.path.append(os.path.abspath("src"))

from resumebuddy.infrastructure.adapters.mlx_adapter import MLXAdapter
from resumebuddy.infrastructure.adapters.scraper import BeautifulSoupScraperAdapter
from resumebuddy.infrastructure.adapters.repository import SQLiteJobRepository, FileSystemProfileRepository
from resumebuddy.application.use_cases import ResumeBuddyUseCases
from resumebuddy.domain.models import JobOpportunity, UserProfile

# Remaining jobs from todo.md
urls = [
    "https://www.linkedin.com/jobs/view/4388530836/",
    "https://www.linkedin.com/jobs/view/4398773344/",
    "https://www.linkedin.com/jobs/view/4118836224/",
    "https://www.linkedin.com/jobs/view/4342095996/",
    "https://www.linkedin.com/jobs/view/4409866239/",
    "https://www.linkedin.com/jobs/view/4398460553/",
    "https://www.workingnomads.com/jobs/senior-python-ai-engineer-proxify-1566714",
    "https://www.workingnomads.com/jobs/senior-backend-developer-python-proxify-1566664",
    "https://www.workingnomads.com/jobs/senior-full-stack-developer-lemonio-1527145",
]

async def main():
    llm_provider = "mlx"
    # Using a smaller model for faster evaluation as requested (e2b tier if possible, but keeping gemma-2-27b as standard if already cached)
    # The user asked for gemma4:e4b or e2b. gemma-2-27b is roughly e4b.
    model_path = os.getenv("RESUMEBUDDY_MLX_MODEL", "mlx-community/gemma-2-27b-it-4bit")
    
    print(f"Using LLM Provider: {llm_provider} with model: {model_path}")
    
    llm_client = MLXAdapter(model_path=model_path)
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
    
    for url in urls:
        try:
            print(f"\n--- Processing {url} ---")
            
            # Check if already evaluated with a real score in DB
            # We need to map URL to ID. Static dashboard used custom IDs.
            # li-4388530836 etc.
            if "linkedin.com/jobs/view/" in url:
                job_id = "li-" + url.split("view/")[1].split("/")[0]
            else:
                job_id = hashlib.md5(url.encode()).hexdigest()[:10]
            
            existing = repo.get_job(job_id)
            if existing and existing.score != "?" and existing.score != "N/A":
                print(f"Already evaluated: {job_id} ({existing.name}) Score: {existing.score}")
                continue

            print(f"Scraping {url}...")
            try:
                jd_data = await scraper.scrape_job(url)
                company = jd_data.get("company") or url.split('/')[2]
                title = jd_data.get("title") or "Job Posting"
                description = jd_data.get("description", "")
            except Exception as e:
                print(f"Scraping failed: {e}")
                continue

            if not description or "403" in description:
                print(f"Skipping evaluation due to missing or blocked description.")
                continue

            print(f"Evaluating {title} at {company}...")
            evaluation = await use_cases.evaluate_role(resume_text, jd_data, profile=user_profile)
            
            # Update or Create Job
            job_dir = f"tmp/evals/{job_id}"
            os.makedirs(job_dir, exist_ok=True)
            
            with open(os.path.join(job_dir, "details.md"), "w") as f:
                f.write(f"# Evaluation for {title} at {company}\n\n")
                f.write(f"**Overall Score:** {evaluation.overall_score}\n\n")
                f.write(f"## Rationale\n{evaluation.rationale}\n\n")
            
            job_opp = JobOpportunity(
                id=job_id,
                name=f"{company} - {title}",
                score=evaluation.overall_score,
                priority=2,
                url=url,
                dir=job_dir,
                status="Ready to Apply"
            )
            repo.save_job(job_opp)
            print(f"Saved {job_opp.name} with score {job_opp.score}")

        except Exception as e:
            print(f"Error processing {url}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
