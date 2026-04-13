import pytest
import os
import json
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock, AsyncMock
from resumebuddy.infrastructure.cli.main import app

runner = CliRunner()

@pytest.fixture
def mock_deps():
    with patch("resumebuddy.infrastructure.cli.main.researcher") as res, \
         patch("resumebuddy.infrastructure.cli.main.profile_repo") as repo, \
         patch("resumebuddy.infrastructure.cli.main.discovery") as disc, \
         patch("resumebuddy.infrastructure.cli.main.scraper") as scrap, \
         patch("resumebuddy.infrastructure.cli.main.use_cases") as cases:
        yield {
            "researcher": res,
            "profile_repo": repo,
            "discovery": disc,
            "scraper": scrap,
            "use_cases": cases
        }

def test_view_command_found(mock_deps):
    mock_deps["researcher"].get_company_intel.return_value = "# Intel Data"
    result = runner.invoke(app, ["view", "Google"])
    assert result.exit_code == 0
    assert "Intel Data" in result.stdout

def test_view_command_not_found(mock_deps):
    mock_deps["researcher"].get_company_intel.return_value = None
    result = runner.invoke(app, ["view", "Unknown"])
    assert result.exit_code == 0
    assert "No intel found" in result.stdout

def test_profile_command(mock_deps, tmp_path):
    inputs = [
        "Py, Go", "Java", "Rust", "IC", "Remote", "100", "150", 
        "None", "Games", "Secret", "Oracle", "Toast"
    ]
    with patch("resumebuddy.infrastructure.cli.main.PROFILE_PATH", str(tmp_path / "user_profile.json")):
        result = runner.invoke(app, ["profile"], input="\n".join(inputs) + "\n")
        assert result.exit_code == 0
        assert "Profile saved" in result.stdout
        mock_deps["profile_repo"].save_profile.assert_called()

def test_research_command_success(mock_deps):
    mock_deps["researcher"].research_company = AsyncMock(return_value={"status": "Growth"})
    result = runner.invoke(app, ["research", "Apple"])
    assert result.exit_code == 0
    assert "Intel for Apple" in result.stdout

def test_research_command_error(mock_deps):
    mock_deps["researcher"].research_company = AsyncMock(return_value={"error": "Failed"})
    result = runner.invoke(app, ["research", "Apple"])
    assert result.exit_code == 0
    assert "Error: Failed" in result.stdout

def test_fetch_command(mock_deps, tmp_path):
    mock_deps["discovery"].discover_jobs = AsyncMock(return_value=[{"title": "Job", "url": "url"}])
    with patch("os.getcwd", return_value=str(tmp_path)):
        os.chdir(tmp_path)
        result = runner.invoke(app, ["fetch"])
        assert result.exit_code == 0
        assert "Saved 4 jobs" in result.stdout

def test_evaluate_command_file(mock_deps, tmp_path):
    resume = tmp_path / "resume.txt"
    resume.write_text("my resume")
    jd = tmp_path / "jd.txt"
    jd.write_text("job desc")
    
    mock_deps["use_cases"].evaluate_role = AsyncMock(return_value={"overall_score": "A", "rationale": "Good"})
    
    result = runner.invoke(app, ["evaluate", "--resume", str(resume), "--jd", str(jd)])
    assert result.exit_code == 0
    assert "Overall Score: A" in result.stdout

def test_evaluate_command_index(mock_deps, tmp_path):
    resume = tmp_path / "resume.txt"
    resume.write_text("my resume")
    pj = tmp_path / "prospective_jobs.jsonl"
    pj.write_text(json.dumps({"company": "NVIDIA", "url": "https://nvidia.com/job/1"}) + "\n")
    
    mock_deps["scraper"].scrape_job = AsyncMock(return_value={"description": "scraped"})
    mock_deps["use_cases"].evaluate_role = AsyncMock(return_value={"overall_score": "B"})
    
    with patch("os.path.exists", return_value=True):
        with patch("resumebuddy.infrastructure.cli.main.load_file", return_value="resume content"):
            os.chdir(tmp_path)
            result = runner.invoke(app, ["evaluate", "--resume", str(resume), "--index", "0"])
            assert result.exit_code == 0
            assert "Overall Score: B" in result.stdout

def test_cover_letter_command_file(mock_deps, tmp_path):
    resume = tmp_path / "resume.txt"
    resume.write_text("my resume")
    jd = tmp_path / "jd.txt"
    jd.write_text("job desc")
    
    mock_deps["use_cases"].analyze_alignment = AsyncMock(return_value={})
    mock_deps["use_cases"].generate_cover_letter = AsyncMock(return_value="My CV Content")
    
    result = runner.invoke(app, ["cover-letter", "--resume", str(resume), "--jd", str(jd)])
    assert result.exit_code == 0
    assert "Cover Letter:" in result.stdout
    assert "My CV Content" in result.stdout

def test_cover_letter_command_url(mock_deps, tmp_path):
    resume = tmp_path / "resume.txt"
    resume.write_text("my resume")
    url = "https://example.com/job"
    
    mock_deps["scraper"].scrape_job = AsyncMock(return_value={"description": "scraped"})
    mock_deps["use_cases"].analyze_alignment = AsyncMock(return_value={})
    mock_deps["use_cases"].generate_cover_letter = AsyncMock(return_value="URL CV")
    
    result = runner.invoke(app, ["cover-letter", "--resume", str(resume), "--jd", url])
    assert result.exit_code == 0
    assert "URL CV" in result.stdout
    mock_deps["scraper"].scrape_job.assert_called_with(url)

def test_load_file_error():
    from resumebuddy.infrastructure.cli.main import load_file
    with pytest.raises(FileNotFoundError):
        load_file("missing.txt")
