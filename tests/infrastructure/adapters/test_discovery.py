import pytest
import respx
from httpx import Response
from resumebuddy.infrastructure.adapters.discovery import JobDiscoveryAdapter

@pytest.mark.asyncio
@respx.mock
async def test_discover_generic():
    adapter = JobDiscoveryAdapter()
    url = "https://example.com/careers"
    html = "<html><a href='/jobs/1'>Backend Engineer</a><a href='/jobs/2'>Manager</a><a href='/jobs/3'>Technical Manager</a><a>No Href</a></html>"
    respx.get(url).mock(return_value=Response(200, content=html))
    
    jobs = await adapter.discover_jobs("Example", url)
    assert len(jobs) == 1
    assert jobs[0]["title"] == "Backend Engineer"
    assert "https://example.com/jobs/1" == jobs[0]["url"]

@pytest.mark.asyncio
@respx.mock
async def test_discover_generic_error():
    adapter = JobDiscoveryAdapter()
    url = "https://example.com/careers"
    respx.get(url).mock(return_value=Response(500))
    jobs = await adapter.discover_jobs("Example", url)
    assert len(jobs) == 0

@pytest.mark.asyncio
@respx.mock
async def test_discover_generic_exception():
    adapter = JobDiscoveryAdapter()
    url = "https://example.com/careers"
    respx.get(url).mock(side_effect=Exception("Failed"))
    jobs = await adapter.discover_jobs("Example", url)
    assert len(jobs) == 0

@pytest.mark.asyncio
@respx.mock
async def test_discover_workday():
    adapter = JobDiscoveryAdapter()
    url = "https://test.wd5.myworkdayjobs.com/test"
    api_url = "https://test.wd5.myworkdayjobs.com/wday/cxs/test/test/jobs"
    
    respx.post(api_url).mock(return_value=Response(200, json={
        "jobPostings": [
            {"title": "Backend Architect", "externalPath": "/job/1"},
            {"title": "Software Manager", "externalPath": "/job/2"},
            {"title": "Technical Manager", "externalPath": "/job/3"},
            {"title": "No Path"}
        ]
    }))
    
    jobs = await adapter.discover_jobs("WorkdayTest", url)
    assert len(jobs) == 1
    assert jobs[0]["title"] == "Backend Architect"

@pytest.mark.asyncio
@respx.mock
async def test_discover_workday_en_us():
    adapter = JobDiscoveryAdapter()
    url = "https://test.wd5.myworkdayjobs.com/en-US/test"
    api_url = "https://test.wd5.myworkdayjobs.com/wday/cxs/test/test/jobs"
    respx.post(api_url).mock(return_value=Response(200, json={"jobPostings": []}))
    jobs = await adapter.discover_jobs("WorkdayTest", url)
    assert len(jobs) == 0

@pytest.mark.asyncio
@respx.mock
async def test_discover_workday_error():
    adapter = JobDiscoveryAdapter()
    url = "https://test.wd5.myworkdayjobs.com/test"
    api_url = "https://test.wd5.myworkdayjobs.com/wday/cxs/test/test/jobs"
    respx.post(api_url).mock(return_value=Response(500))
    jobs = await adapter.discover_jobs("WorkdayTest", url)
    assert len(jobs) == 0

@pytest.mark.asyncio
@respx.mock
async def test_discover_workday_exception():
    adapter = JobDiscoveryAdapter()
    url = "https://test.wd5.myworkdayjobs.com/test"
    api_url = "https://test.wd5.myworkdayjobs.com/wday/cxs/test/test/jobs"
    respx.post(api_url).mock(side_effect=Exception("Failed"))
    jobs = await adapter.discover_jobs("WorkdayTest", url)
    assert len(jobs) == 0

@pytest.mark.asyncio
@respx.mock
async def test_discover_generic_manager_skip():
    from resumebuddy.infrastructure.adapters.discovery import JobDiscoveryAdapter
    adapter = JobDiscoveryAdapter()
    url = "https://example.com/careers"
    html = "<html><a href='/jobs/2'>Backend Manager</a></html>"
    respx.get(url).mock(return_value=Response(200, content=html))
    jobs = await adapter.discover_jobs("Example", url)
    assert len(jobs) == 0
