import pytest
from unittest.mock import AsyncMock
from resumebuddy.application.use_cases import ResumeBuddyUseCases
from resumebuddy.ports.llm import ILLMClient

@pytest.fixture
def mock_llm():
    return AsyncMock(spec=ILLMClient)

@pytest.fixture
def use_cases(mock_llm):
    return ResumeBuddyUseCases(mock_llm)

@pytest.mark.asyncio
async def test_extract_requirements(use_cases, mock_llm):
    mock_llm.complete_prompt.return_value = '["Python", "Go"]'
    reqs = await use_cases.extract_requirements("JD text")
    assert reqs == ["Python", "Go"]

@pytest.mark.asyncio
async def test_evaluate_role(use_cases, mock_llm):
    mock_llm.complete_prompt.return_value = '{"overall_score": "A", "rationale": "Great"}'
    res = await use_cases.evaluate_role("resume", {"title": "SWE"})
    assert res["overall_score"] == "A"

@pytest.mark.asyncio
async def test_analyze_alignment(use_cases, mock_llm):
    mock_llm.complete_prompt.return_value = '{"matching_skills": ["Python"]}'
    res = await use_cases.analyze_alignment("resume", "jd")
    assert res["matching_skills"] == ["Python"]

@pytest.mark.asyncio
async def test_generate_cover_letter(use_cases, mock_llm):
    mock_llm.complete_prompt.return_value = "Hello"
    cv = await use_cases.generate_cover_letter("resume", "jd", {})
    assert cv == "Hello"

@pytest.mark.asyncio
async def test_optimize_resume(use_cases, mock_llm):
    mock_llm.complete_prompt.return_value = "Optimized"
    res = await use_cases.optimize_resume("resume", "jd", {})
    assert res == "Optimized"

@pytest.mark.asyncio
async def test_extract_requirements_error(use_cases, mock_llm):
    mock_llm.complete_prompt.return_value = "invalid json"
    reqs = await use_cases.extract_requirements("JD text")
    assert reqs == []

@pytest.mark.asyncio
async def test_evaluate_role_error(use_cases, mock_llm):
    mock_llm.complete_prompt.return_value = "invalid json"
    res = await use_cases.evaluate_role("resume", {"title": "SWE"})
    assert "error" in res

@pytest.mark.asyncio
async def test_analyze_alignment_error(use_cases, mock_llm):
    mock_llm.complete_prompt.return_value = "invalid json"
    res = await use_cases.analyze_alignment("resume", "jd")
    assert "error" in res
