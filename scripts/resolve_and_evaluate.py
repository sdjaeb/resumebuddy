import asyncio
import json
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from resumebuddy.infrastructure.adapters.scraper import BeautifulSoupScraperAdapter
from resumebuddy.infrastructure.adapters.ollama import OllamaAdapter
from resumebuddy.infrastructure.adapters.mlx_adapter import MLXAdapter
from resumebuddy.infrastructure.adapters.repository import SQLiteJobRepository, FileSystemProfileRepository
from resumebuddy.application.use_cases import ResumeBuddyUseCases
from resumebuddy.domain.models import JobOpportunity

async def main():
    scraper = BeautifulSoupScraperAdapter()
    
    # Use MLX for high-reasoning title extraction and evaluation
    llm_client = MLXAdapter(model_path="mlx-community/gemma-2-27b-it-4bit")
    use_cases = ResumeBuddyUseCases(llm_client)
    job_repo = SQLiteJobRepository("jobs.db")
    profile_repo = FileSystemProfileRepository()
    
    with open("resume.txt", "r") as f:
        resume_text = f.read()
    
    user_profile = profile_repo.load_profile("user_profile.json")

    # The 11 roles user provided (last 11 in jsonl)
    with open("prospective_jobs.jsonl", "r") as f:
        lines = f.readlines()
        new_roles = [json.loads(line) for line in lines[-11:]]

    print(f"Resolving and evaluating {len(new_roles)} roles...")

    for i, role in enumerate(new_roles):
        url = role['url']
        print(f"[{i+1}/{len(new_roles)}] Scraping {url}...")
        
        try:
            jd_data = await scraper.scrape_job(url)
            
            # Use LLM to extract clean Title and Company from scraped text
            # Especially for those LinkedIn "Job 12345" entries
            prompt = f"""Extract the Job Title and Company Name from this text.
URL: {url}
Scraped Title: {jd_data.get('title')}
Text: {jd_data.get('description')[:2000]}

Return ONLY a JSON object with keys "title" and "company".
"""
            extract_response = await llm_client.complete_prompt(prompt)
            # Find JSON
            import re
            match = re.search(r'\{.*\}', extract_response, re.DOTALL)
            if match:
                extracted = json.loads(match.group(0))
                clean_title = extracted.get("title", jd_data.get("title"))
                clean_company = extracted.get("company", role.get("company"))
            else:
                clean_title = jd_data.get("title")
                clean_company = role.get("company")

            print(f"  Resolved: {clean_title} at {clean_company}")

            # Now evaluate
            eval_result = await use_cases.evaluate_role(
                resume_text, 
                jd_data, 
                company_intel=None, 
                profile=user_profile
            )
            
            job_id = f"{clean_company.lower().replace(' ', '-')}-{i}"
            job = JobOpportunity(
                id=job_id,
                name=f"{clean_company} - {clean_title}",
                score=eval_result.overall_score,
                priority=2,
                url=url,
                dir=f"tmp/prospects/{job_id}",
                status="Ready to Apply"
            )
            job_repo.save_job(job)
            print(f"  Scored: {eval_result.overall_score}")

        except Exception as e:
            print(f"  Error processing {url}: {e}")

    print("All roles resolved and evaluated.")

if __name__ == "__main__":
    asyncio.run(main())
