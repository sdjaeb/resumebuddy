import httpx
from bs4 import BeautifulSoup
from typing import Dict, Any
from urllib.parse import urlparse
from resumebuddy.ports.scraper import IJobScraper

class BeautifulSoupScraperAdapter(IJobScraper):
    def __init__(self, user_agent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"):
        self.headers = {"User-Agent": user_agent}

    async def scrape_job(self, url: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(headers=self.headers, timeout=20.0, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            domain = urlparse(url).netloc
            
            if "greenhouse.io" in domain or "job-boards.greenhouse.io" in domain:
                return self._scrape_greenhouse(soup, url)
            elif "lever.co" in domain:
                return self._scrape_lever(soup, url)
            elif "ashbyhq.com" in domain:
                return self._scrape_ashby(soup, url)
            elif "myworkdayjobs.com" in domain:
                return await self._scrape_workday(url, client)
            else:
                return {
                    "title": soup.title.string if soup.title else "Unknown Title",
                    "description": soup.get_text(separator='\n', strip=True),
                    "posted_at": "Unknown",
                    "is_repost": False,
                    "url": url
                }

    def _scrape_greenhouse(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        title = soup.find('h1', class_='app-title')
        content = soup.find('div', id='content')
        return {
            "title": title.get_text(strip=True) if title else "Greenhouse Role",
            "description": content.get_text(separator='\n', strip=True) if content else soup.get_text(),
            "posted_at": "Check Metadata",
            "is_repost": False,
            "url": url
        }

    def _scrape_lever(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        title = soup.find('h2')
        content = soup.find('div', class_='content')
        return {
            "title": title.get_text(strip=True) if title else "Lever Role",
            "description": content.get_text(separator='\n', strip=True) if content else soup.get_text(),
            "posted_at": "Check Metadata",
            "is_repost": False,
            "url": url
        }

    def _scrape_ashby(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        return {
            "title": soup.title.string if soup.title else "Ashby Role",
            "description": soup.get_text(separator='\n', strip=True),
            "posted_at": "Unknown",
            "is_repost": False,
            "url": url
        }

    async def _scrape_workday(self, url: str, client: httpx.AsyncClient) -> Dict[str, Any]:
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.strip('/').split('/')
        if not path_parts or path_parts == ['']:
            return {"title": "Workday Role", "description": "Failed to parse Workday URL", "url": url}

        if len(path_parts[0]) == 5 and '-' in path_parts[0]:
            path_parts = path_parts[1:]
        
        if len(path_parts) < 2:
            return {"title": "Workday Role", "description": "Failed to parse Workday URL (site or job path missing)", "url": url}
        
        tenant = parsed_url.netloc.split('.')[0]
        site = path_parts[0]
        try:
            job_index = path_parts.index('job')
            job_path = '/'.join(path_parts[job_index:])
        except ValueError:
            job_path = '/'.join(path_parts[1:])
        
        api_url = f"https://{parsed_url.netloc}/wday/cxs/{tenant}/{site}/{job_path}"

        resp = await client.get(api_url, headers={"Accept": "application/json"})
        if resp.status_code == 403:
            return {"title": "Workday Role", "description": "Access Forbidden (403). Possible bot detection.", "url": url}
        if resp.status_code != 200:
            return {"title": "Workday Role", "description": f"Failed to fetch Workday API: {resp.status_code}", "url": url}

        try:
            full_data = resp.json()
            data = full_data.get('jobPostingInfo', {}) or full_data.get('jobPosting', {})
        except Exception as e:
            return {"title": "Workday Role", "description": f"Failed to parse Workday JSON: {e}", "url": url}

        description = data.get('jobDescription', '')
        soup = BeautifulSoup(description, 'html.parser')
        clean_description = soup.get_text(separator='\n', strip=True)
        
        return {
            "title": data.get('title', 'Workday Role'),
            "description": clean_description,
            "posted_at": data.get('postedOn', 'Unknown'),
            "is_repost": False,
            "url": url
        }
