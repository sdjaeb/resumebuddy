import os
import pytest
import json
from unittest.mock import MagicMock, patch, AsyncMock
from resumebuddy.infrastructure.adapters.data_generator import FineTuneDataGenerator

@pytest.fixture
def generator():
    with patch("google.genai.Client"):
        return FineTuneDataGenerator(api_key="test_key")

def test_extract_json_success(generator):
    text = "Here is some json: ```json\n{\"key\": \"val\"}\n```"
    res = generator._extract_json(text)
    assert res == {"key": "val"}

def test_extract_json_braces(generator):
    text = "{\"key\": \"val\"}"
    res = generator._extract_json(text)
    assert res == {"key": "val"}

def test_extract_json_error(generator):
    text = "no json here"
    res = generator._extract_json(text)
    assert "error" in res

def test_extract_json_malformed_clean(generator):
    # This string will cause JSONDecodeError but should be fixable by the regex (simulated)
    # Actually, let's just mock json.loads to trigger the paths
    with patch("json.loads") as mock_loads:
        mock_loads.side_effect = [json.JSONDecodeError("msg", "doc", 0), {"fixed": "key"}]
        res = generator._extract_json('{"bad": json}')
        assert res == {"fixed": "key"}

def test_extract_json_failed_clean(generator):
    with patch("json.loads") as mock_loads:
        mock_loads.side_effect = [json.JSONDecodeError("msg", "doc", 0), json.JSONDecodeError("msg", "doc", 0)]
        res = generator._extract_json('{"hopeless": json}')
        assert "error" in res
        assert "Failed to parse JSON even after cleaning" in res["error"]

@pytest.mark.asyncio
async def test_generate_quadruplet_success(generator):
    generator.client.models.generate_content = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '```json\n{"instruction": "JD", "input": "Resume", "output": "Reasoning"}\n```'
    generator.client.models.generate_content.return_value = mock_response
    
    res = generator.generate_quadruplet("AI")
    assert res["instruction"] == "JD"

@pytest.mark.asyncio
async def test_generate_quadruplet_exception(generator):
    generator.client.models.generate_content = MagicMock(side_effect=Exception("API Error"))
    res = generator.generate_quadruplet("AI")
    assert res["error"] == "API Error"

@pytest.mark.asyncio
async def test_run_success(generator, tmp_path):
    output_file = os.path.join(tmp_path, "test_data.jsonl")
    generator.generate_quadruplet = MagicMock(return_value={"instruction": "JD", "input": "R", "output": "Out"})
    
    await generator.run(count=2, output_file=output_file)
    
    assert os.path.exists(output_file)
    with open(output_file, "r") as f:
        lines = f.readlines()
        assert len(lines) == 2

@pytest.mark.asyncio
async def test_run_rate_limit(generator, tmp_path):
    output_file = os.path.join(tmp_path, "test_data_rl.jsonl")
    generator.generate_quadruplet = MagicMock(return_value={"error": "429 Rate Limit"})
    
    with patch("asyncio.sleep", AsyncMock()) as mock_sleep:
        await generator.run(count=1, output_file=output_file)
        mock_sleep.assert_called()

@pytest.mark.asyncio
async def test_run_unexpected_error(generator, tmp_path):
    output_file = os.path.join(tmp_path, "test_data_err.jsonl")
    generator.generate_quadruplet = MagicMock(return_value={"error": "Some other error"})
    
    with patch("asyncio.sleep", AsyncMock()):
        await generator.run(count=1, output_file=output_file)

@pytest.mark.asyncio
async def test_run_keyboard_interrupt(generator, tmp_path):
    output_file = os.path.join(tmp_path, "test_data_ki.jsonl")
    with patch("asyncio.to_thread", side_effect=KeyboardInterrupt):
        await generator.run(count=5, output_file=output_file)

@pytest.mark.asyncio
async def test_run_generic_exception(generator, tmp_path):
    output_file = os.path.join(tmp_path, "test_data_ex.jsonl")
    with patch("asyncio.to_thread", side_effect=Exception("Major Crash")):
        with patch("asyncio.sleep", AsyncMock()):
            await generator.run(count=1, output_file=output_file)
