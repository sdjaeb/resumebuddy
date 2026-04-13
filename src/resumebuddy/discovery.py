import httpx
from bs4 import BeautifulSoup
import asyncio
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Any, Optional
import json
import os

class JobDiscovery:
    """
    Discovers job listings across various boards and career sites.
    """
    def __init__(self, user_agent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"):
        self.headers = {"User-Agent": user_agent}

    async def discover_jobs(self, name: str, url: str) -> List[Dict[str, Any]]:
        """
        Discovers jobs on a specific site/board.
        """
        domain = urlparse(url).netloc
        if "myworkdayjobs.com" in domain:
            return await self._discover_workday(name, url)
        else:
            return await self._discover_generic(name, url)

    async def _discover_generic(self, name: str, url: str) -> List[Dict[str, Any]]:
        jobs = []
        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=15.0, follow_redirects=True) as client:
                resp = await client.get(url)
                if resp.status_code == 403:
                    print(f"[bold red]Access Forbidden (403) on {name}.[/bold red] Possible bot detection.")
                    return []
                if resp.status_code != 200:
                    return []
                
                soup = BeautifulSoup(resp.content, 'html.parser')
                links = soup.find_all('a')
                for link in links:
                    text = link.get_text().strip()
                    href = link.get('href')
                    if not href: continue
                    
                    href = urljoin(url, href)
                    l_text = text.lower()
                    
                    # Basic Role Keywords
                    if any(role in l_text for role in ["backend", "ml systems", "integration", "architect", "staff", "software", "data engineer"]):
                        # Apply some initial preference filtering here if possible
                        # (e.g., avoid clearly management-only roles)
                        if "manager" in l_text and "technical" not in l_text and "architect" not in l_text:
                            continue
                        
                        jobs.append({
                            "company": name,
                            "title": text,
                            "url": href
                        })
        except Exception as e:
            print(f"Failed to discover on {name}: {e}")
        return jobs

    async def _discover_workday(self, name: str, url: str) -> List[Dict[str, Any]]:
        """
        Discovers jobs on Workday by calling its internal list API.
        """
        jobs = []
        try:
            parsed_url = urlparse(url)
            tenant = parsed_url.netloc.split('.')[0]
            # Pattern: https://{tenant}.wd5.myworkdayjobs.com/{site}
            site = parsed_url.path.strip('/').split('/')[0]
            if not site or site == 'en-US':
                 # Re-parse if locale was first
                 site = parsed_url.path.strip('/').split('/')[1] if len(parsed_url.path.strip('/').split('/')) > 1 else site

            api_url = f"https://{parsed_url.netloc}/wday/cxs/{tenant}/{site}/jobs"
            
            # Use some default facets or search if needed
            payload = {
                "appliedFacets": {},
                "limit": 20,
                "offset": 0,
                "searchText": ""
            }
            
            async with httpx.AsyncClient(headers=self.headers, timeout=15.0) as client:
                resp = await client.post(api_url, json=payload, headers={"Accept": "application/json"})
                if resp.status_code == 403:
                    print(f"[bold red]Access Forbidden (403) on {name} Workday API.[/bold red] Possible bot detection.")
                    return []
                if resp.status_code != 200:
                    return []
                
                data = resp.json()
                for job_data in data.get('jobPostings', []):
                    title = job_data.get('title', 'Unknown')
                    job_path = job_data.get('externalPath', '')
                    if not job_path: continue
                    
                    # Construct full URL: https://{netloc}/{site}{job_path}
                    # externalPath usually starts with /job/
                    full_url = f"https://{parsed_url.netloc}/{site}{job_path}"
                    
                    l_title = title.lower()
                    if any(role in l_title for role in ["backend", "ml systems", "integration", "architect", "staff", "software", "data engineer"]):
                        if "manager" in l_title and "technical" not in l_title and "architect" not in l_title:
                            continue
                            
                        jobs.append({
                            "company": name,
                            "title": title,
                            "url": full_url
                        })
        except Exception as e:
            print(f"Failed to discover Workday jobs for {name}: {e}")
        return jobs

def save_prospective_jobs(jobs: List[Dict[str, Any]], filename: str = "prospective_jobs.jsonl"):
    with open(filename, "a") as f:
        for job in jobs:
            f.write(json.dumps(job) + "\n")
