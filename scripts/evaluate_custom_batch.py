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

urls = [
    "https://www.linkedin.com/jobs/view/4359872107/",
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

local_jds = [
    ("IndusValley", "tmp/jd_indusvalley.txt")
]

async def main():
    llm_provider = os.getenv("RESUMEBUDDY_LLM_PROVIDER", "mlx").lower()
    model_path = os.getenv("RESUMEBUDDY_MLX_MODEL", "mlx-community/gemma-2-9b-it-4bit")
    
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
    
    existing_jobs_by_url = {j.url: j.id for j in repo.list_jobs()}

    jobs_to_process = [
        {"url": "https://www.linkedin.com/jobs/view/4408629516/", "source": "web"}, # Smartsheet
    ]

    for item in jobs_to_process:
        try:
            if item["source"] == "web":
                url = item["url"]
                print(f"Scraping {url}...")
                try:
                    jd_data = await scraper.scrape_job(url)
                    company = jd_data.get("company") or url.split('/')[2]
                    title = jd_data.get("title") or "Job Posting"
                    description = jd_data.get("description", "")
                except Exception as e:
                    print(f"Scraping failed for {url}: {e}")
                    jd_data = {"description": f"Scraping failed: {e}", "title": "Scrape Failure", "company": "Unknown"}
                    company = "Scrape Failure"
                    title = url
                    description = ""

            else:
                path = item["path"]
                print(f"Reading {path}...")
                with open(path, "r") as f:
                    description = f.read()
                jd_data = {
                    "description": description,
                    "title": item["name"],
                    "company": item["name"]
                }
                company = item["name"]
                title = "Job Description"
                url = path

            if not description or "403 Forbidden" in description or "403" in description:
                print(f"Skipping evaluation for {url} due to missing or blocked description.")
                evaluation_score = "N/A"
                rationale = "Description blocked or missing."
            else:
                print(f"Evaluating {title} at {company}...")
                evaluation = await use_cases.evaluate_role(resume_text, jd_data, profile=user_profile)
                evaluation_score = evaluation.overall_score
                rationale = evaluation.rationale
            
            # Create Job ID and Directory
            job_id = existing_jobs_by_url.get(url)
            if not job_id:
                # Create a readable ID from company and title
                clean_company = "".join(c for c in company if c.isalnum()).lower()
                clean_title = "".join(c for c in title if c.isalnum() or c == ' ').lower().replace(' ', '-')[:20]
                job_id = f"{clean_company}-{clean_title}"
            
            job_dir = f"tmp/prospects/{job_id}"
            os.makedirs(job_dir, exist_ok=True)
            
            # Save files for dashboard
            with open(os.path.join(job_dir, "details.md"), "w") as f:
                f.write(f"# Evaluation for {title} at {company}\n\n")
                f.write(f"**Overall Score:** {evaluation_score}\n\n")
                f.write(f"## Rationale\n{rationale}\n\n")
                if 'evaluation' in locals() and hasattr(evaluation, 'bs_detector'):
                    f.write(f"## BS Detector (Score: {evaluation.bs_detector.score}/10)\n")
                    f.write(f"**Analysis:** {evaluation.bs_detector.analysis}\n\n")
                    f.write("**Red Flags:**\n")
                    for flag in evaluation.bs_detector.red_flags:
                        f.write(f"- {flag}\n")
            
            with open(os.path.join(job_dir, "resume.txt"), "w") as f:
                f.write(resume_text)
                
            # Create cover letter if evaluation succeeded
            if evaluation_score != "N/A":
                print(f"Generating cover letter for {title}...")
                alignment = await use_cases.analyze_alignment(resume_text, description)
                cl = await use_cases.generate_cover_letter(resume_text, description, alignment)
                with open(os.path.join(job_dir, "cover_letter.txt"), "w") as f:
                    f.write(cl)
            else:
                with open(os.path.join(job_dir, "cover_letter.txt"), "w") as f:
                    f.write("Cover letter not generated due to evaluation failure.")

            # Save to repo
            job_opp = JobOpportunity(
                id=job_id,
                name=f"{company} - {title}",
                score=evaluation_score,
                priority=2,
                url=url,
                dir=job_dir,
                status="Ready to Apply",
                signals_json=json.dumps([s.model_dump() for s in evaluation.signals]) if 'evaluation' in locals() and hasattr(evaluation, 'signals') else None
            )
            repo.save_job(job_opp)
            print(f"Saved {job_opp.name} with score {job_opp.score}")

        except Exception as e:
            print(f"Error processing {item.get('url') or item.get('path')}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
