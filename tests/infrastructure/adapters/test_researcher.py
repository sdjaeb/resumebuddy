import os
import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from resumebuddy.infrastructure.adapters.researcher import ResearcherAdapter
from resumebuddy.ports.llm import ILLMClient

@pytest.fixture
def mock_llm():
    return AsyncMock(spec=ILLMClient)

@pytest.fixture
def researcher(mock_llm, tmp_path):
    kb_dir = os.path.join(tmp_path, "kb")
    return ResearcherAdapter(mock_llm, kb_dir=kb_dir)

@pytest.mark.asyncio
async def test_research_company_success(researcher, mock_llm):
    company = "TestCorp"
    mock_llm.complete_prompt.return_value = json.dumps({
        "news": [{"date": "2026", "title": "News"}],
        "layoffs": "None",
        "performance": {"stock": "Up"},
        "culture": "Great",
        "status": "Enterprise",
        "overall_sentiment": "Positive"
    })
    
    result = await researcher.research_company(company)
    assert result["status"] == "Enterprise"
    
    # Verify file was created
    kb_file = os.path.join(researcher.kb_dir, "testcorp.md")
    assert os.path.exists(kb_file)
    
    # Test get_company_intel
    intel = researcher.get_company_intel(company)
    assert "# Company Intel: TestCorp" in intel

@pytest.mark.asyncio
async def test_research_company_error(researcher, mock_llm):
    mock_llm.complete_prompt.return_value = "invalid json"
    result = await researcher.research_company("FailCorp")
    assert "error" in result

def test_get_company_intel_not_found(researcher):
    assert researcher.get_company_intel("MissingCorp") is None

def test_format_section_complex(researcher):
    # Test internal _save_to_kb formatting logic indirectly via researcher call if needed
    # or just test format_section if we expose it (currently private-ish but we can test via data)
    data = {
        "news": ["Simple Item"],
        "layoffs": [{"date": "today", "count": 10}],
        "performance": {"key": "val"},
        "culture": [],
        "status": "Test",
        "overall_sentiment": "Test"
    }
    researcher._save_to_kb("FormatTest", data)
    kb_file = os.path.join(researcher.kb_dir, "formattest.md")
    with open(kb_file, "r") as f:
        content = f.read()
        assert "| date | count |" in content
        assert "- Simple Item" in content
        assert "- **key**: val" in content
        assert "N/A" in content # For empty culture list
