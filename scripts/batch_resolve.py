import asyncio
import json
import os
import sys
import sqlite3

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from resumebuddy.infrastructure.adapters.scraper import BeautifulSoupScraperAdapter
from resumebuddy.infrastructure.adapters.repository import SQLiteJobRepository
from resumebuddy.domain.models import JobOpportunity

async def resolve_titles():
    scraper = BeautifulSoupScraperAdapter()
    job_repo = SQLiteJobRepository("jobs.db")
    
    urls = [
        "https://www.workingnomads.com/jobs/senior-python-ai-engineer-proxify-1566714",
        "https://www.workingnomads.com/jobs/senior-backend-developer-python-proxify-1566664",
        "https://www.workingnomads.com/jobs/senior-full-stack-developer-lemonio-1527145",
        "https://www.linkedin.com/jobs/view/4388530833/",
        "https://www.linkedin.com/jobs/view/4359872107/",
        "https://www.linkedin.com/jobs/view/4388530836/",
        "https://www.linkedin.com/jobs/view/4398773344/",
        "https://www.linkedin.com/jobs/view/4118836224/",
        "https://www.linkedin.com/jobs/view/4342095996/",
        "https://www.linkedin.com/jobs/view/4409866239/",
        "https://www.linkedin.com/jobs/view/4398460553/"
    ]

    print("Resolving metadata for 11 roles...")
    
    for i, url in enumerate(urls):
        print(f"[{i+1}/{len(urls)}] Scraping {url}...")
        try:
            data = await scraper.scrape_job(url)
            title = data.get('title', 'Unknown').split(' | ')[0].split(' - ')[0]
            
            # Save a placeholder with resolved title
            job_id = f"new-lead-{i}"
            if "linkedin" in url:
                job_id = f"li-{url.strip('/').split('/')[-1]}"
            
            job = JobOpportunity(
                id=job_id,
                name=title,
                score="?",
                priority=2,
                url=url,
                dir=f"tmp/prospects/{job_id}",
                status="Ready to Apply"
            )
            job_repo.save_job(job)
            print(f"  Resolved: {title}")
        except Exception as e:
            print(f"  Failed: {e}")

if __name__ == "__main__":
    asyncio.run(resolve_titles())
