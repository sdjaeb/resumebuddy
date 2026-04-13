import pytest
import respx
from httpx import Response
from resumebuddy.infrastructure.adapters.scraper import BeautifulSoupScraperAdapter

@pytest.mark.asyncio
@respx.mock
async def test_scrape_job_generic():
    adapter = BeautifulSoupScraperAdapter()
    url = "https://example.com/job/1"
    html = "<html><title>Test Job</title><body>Body text</body></html>"
    respx.get(url).mock(return_value=Response(200, content=html))
    
    res = await adapter.scrape_job(url)
    assert res["title"] == "Test Job"
    assert "Body text" in res["description"]

@pytest.mark.asyncio
@respx.mock
async def test_scrape_job_greenhouse():
    adapter = BeautifulSoupScraperAdapter()
    url = "https://boards.greenhouse.io/test/jobs/1"
    html = "<html><body><h1 class='app-title'>Greenhouse Job</h1><div id='content'>Content here</div></body></html>"
    respx.get(url).mock(return_value=Response(200, content=html))
    
    res = await adapter.scrape_job(url)
    assert res["title"] == "Greenhouse Job"
    assert "Content here" in res["description"]

@pytest.mark.asyncio
@respx.mock
async def test_scrape_job_greenhouse_fallback():
    adapter = BeautifulSoupScraperAdapter()
    url = "https://boards.greenhouse.io/test/jobs/1"
    html = "<html><body>Just some text</body></html>"
    respx.get(url).mock(return_value=Response(200, content=html))
    
    res = await adapter.scrape_job(url)
    assert res["title"] == "Greenhouse Role"

@pytest.mark.asyncio
@respx.mock
async def test_scrape_job_lever():
    adapter = BeautifulSoupScraperAdapter()
    url = "https://jobs.lever.co/test/1"
    html = "<html><body><h2>Lever Job</h2><div class='content'>Lever content</div></body></html>"
    respx.get(url).mock(return_value=Response(200, content=html))
    
    res = await adapter.scrape_job(url)
    assert res["title"] == "Lever Job"
    assert "Lever content" in res["description"]

@pytest.mark.asyncio
@respx.mock
async def test_scrape_job_lever_fallback():
    adapter = BeautifulSoupScraperAdapter()
    url = "https://jobs.lever.co/test/1"
    html = "<html><body>Just some text</body></html>"
    respx.get(url).mock(return_value=Response(200, content=html))
    
    res = await adapter.scrape_job(url)
    assert res["title"] == "Lever Role"

@pytest.mark.asyncio
@respx.mock
async def test_scrape_job_ashby():
    adapter = BeautifulSoupScraperAdapter()
    url = "https://jobs.ashbyhq.com/test/1"
    html = "<html><title>Ashby Job</title><body>Ashby content</body></html>"
    respx.get(url).mock(return_value=Response(200, content=html))
    
    res = await adapter.scrape_job(url)
    assert res["title"] == "Ashby Job"
    assert "Ashby content" in res["description"]

@pytest.mark.asyncio
@respx.mock
async def test_scrape_job_ashby_fallback():
    adapter = BeautifulSoupScraperAdapter()
    url = "https://jobs.ashbyhq.com/test/1"
    html = "<html><body>Ashby content</body></html>"
    respx.get(url).mock(return_value=Response(200, content=html))
    
    res = await adapter.scrape_job(url)
    assert res["title"] == "Ashby Role"

@pytest.mark.asyncio
@respx.mock
async def test_scrape_workday():
    adapter = BeautifulSoupScraperAdapter()
    url = "https://test.wd5.myworkdayjobs.com/test/job/Location/Title_ID"
    api_url = "https://test.wd5.myworkdayjobs.com/wday/cxs/test/test/job/Location/Title_ID"
    html = "<html><body>No match</body></html>"
    respx.get(url).mock(return_value=Response(200, content=html))
    respx.get(api_url).mock(return_value=Response(200, json={
        "jobPostingInfo": {
            "title": "Workday Job",
            "jobDescription": "<p>Description</p>",
            "postedOn": "Today"
        }
    }))
    
    res = await adapter.scrape_job(url)
    assert res["title"] == "Workday Job"
    assert "Description" in res["description"]

@pytest.mark.asyncio
@respx.mock
async def test_scrape_workday_no_job_path():
    adapter = BeautifulSoupScraperAdapter()
    url = "https://test.wd5.myworkdayjobs.com/test/Location/Title_ID"
    api_url = "https://test.wd5.myworkdayjobs.com/wday/cxs/test/test/Location/Title_ID"
    html = "<html><body>No match</body></html>"
    respx.get(url).mock(return_value=Response(200, content=html))
    respx.get(api_url).mock(return_value=Response(200, json={"jobPosting": {}}))
    
    res = await adapter.scrape_job(url)
    assert "Unknown" in res.get("posted_at", "Unknown")

@pytest.mark.asyncio
@respx.mock
async def test_scrape_workday_empty_path():
    adapter = BeautifulSoupScraperAdapter()
    url = "https://test.wd5.myworkdayjobs.com/"
    respx.get(url).mock(return_value=Response(200, content=""))
    res = await adapter.scrape_job(url)
    assert "Failed to parse Workday URL" in res["description"]

@pytest.mark.asyncio
@respx.mock
async def test_scrape_workday_short_path():
    adapter = BeautifulSoupScraperAdapter()
    url = "https://test.wd5.myworkdayjobs.com/en-US/"
    respx.get(url).mock(return_value=Response(200, content=""))
    res = await adapter.scrape_job(url)
    assert "Failed to parse Workday URL (site or job path missing)" in res["description"]

@pytest.mark.asyncio
@respx.mock
async def test_scrape_workday_403():
    adapter = BeautifulSoupScraperAdapter()
    url = "https://test.wd5.myworkdayjobs.com/test/job/Loc/ID"
    api_url = "https://test.wd5.myworkdayjobs.com/wday/cxs/test/test/job/Loc/ID"
    respx.get(url).mock(return_value=Response(200, content=""))
    respx.get(api_url).mock(return_value=Response(403))
    
    res = await adapter.scrape_job(url)
    assert "Access Forbidden (403)" in res["description"]

@pytest.mark.asyncio
@respx.mock
async def test_scrape_workday_500():
    adapter = BeautifulSoupScraperAdapter()
    url = "https://test.wd5.myworkdayjobs.com/test/job/Loc/ID"
    api_url = "https://test.wd5.myworkdayjobs.com/wday/cxs/test/test/job/Loc/ID"
    respx.get(url).mock(return_value=Response(200, content=""))
    respx.get(api_url).mock(return_value=Response(500))
    
    res = await adapter.scrape_job(url)
    assert "Failed to fetch Workday API" in res["description"]

@pytest.mark.asyncio
@respx.mock
async def test_scrape_workday_json_error():
    adapter = BeautifulSoupScraperAdapter()
    url = "https://test.wd5.myworkdayjobs.com/test/job/Loc/ID"
    api_url = "https://test.wd5.myworkdayjobs.com/wday/cxs/test/test/job/Loc/ID"
    respx.get(url).mock(return_value=Response(200, content=""))
    respx.get(api_url).mock(return_value=Response(200, text="Invalid JSON"))
    
    res = await adapter.scrape_job(url)
    assert "Failed to parse Workday JSON" in res["description"]

@pytest.mark.asyncio
@respx.mock
async def test_scrape_generic_fallback_no_title():
    adapter = BeautifulSoupScraperAdapter()
    url = "https://example.com"
    respx.get(url).mock(return_value=Response(200, content="<html><body>test</body></html>"))
    res = await adapter.scrape_job(url)
    assert res["title"] == "Unknown Title"

@pytest.mark.asyncio
@respx.mock
async def test_scrape_workday_no_job_string_in_path():
    from resumebuddy.infrastructure.adapters.scraper import BeautifulSoupScraperAdapter
    adapter = BeautifulSoupScraperAdapter()
    url = "https://test.wd5.myworkdayjobs.com/test/Location/Title_ID"
    api_url = "https://test.wd5.myworkdayjobs.com/wday/cxs/test/test/Location/Title_ID"
    respx.get(url).mock(return_value=Response(200, content="<html><body>No match</body></html>"))
    respx.get(api_url).mock(return_value=Response(200, json={
        "jobPostingInfo": {
            "title": "Workday Job",
            "jobDescription": "<p>Desc</p>",
            "postedOn": "Today"
        }
    }))
    
    res = await adapter.scrape_job(url)
    assert res["title"] == "Workday Job"
