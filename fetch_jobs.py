import httpx
from bs4 import BeautifulSoup
import asyncio
from urllib.parse import urljoin

async def fetch(name, url, filters=None):
    print(f"--- {name} ({url}) ---")
    try:
        async with httpx.AsyncClient(headers={"User-Agent": "Mozilla/5.0"}, timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                print(f"Error: {resp.status_code}")
                return
            
            soup = BeautifulSoup(resp.content, 'html.parser')
            links = soup.find_all('a')
            found = False
            for link in links:
                text = link.get_text().strip()
                href = link.get('href')
                if not href:
                    continue
                
                href = urljoin(url, href)
                l_text = text.lower()
                
                # Role Keywords
                role_match = any(role in l_text for role in ["backend", "ml systems", "integration", "architect", "staff", "software", "data engineer"])
                # Language Filter (Anti-Java preference)
                java_match = "java" in l_text and "javascript" not in l_text
                
                if role_match and not java_match:
                    print(f"Role: {text} -> {href}")
                    found = True
            if not found:
                print("No matching (Non-Java) roles found on this page.")
    except Exception as e:
        print(f"Failed: {e}")

async def main():
    urls = [
        ("Kentik", "https://www.kentik.com/careers/"),
        ("Cohere", "https://cohere.com/jobs"),
        ("LivaNova", "https://careers.livanova.com/"),
        ("NVIDIA", "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite"),
        ("WeWorkRemotely", "https://weworkremotely.com/categories/remote-back-end-programming-jobs"),
        ("Remotive", "https://remotive.com/remote-jobs/software-dev"),
        ("RemoteOK", "https://remoteok.com/remote-backend-jobs"),
        ("Working Nomads", "https://www.workingnomads.com/jobs?category=development"),
    ]
    tasks = [fetch(name, url) for name, url in urls]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
