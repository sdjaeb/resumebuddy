import os
import json
from typing import Dict, Any, Optional
from datetime import datetime
from resumebuddy.ports.researcher import IResearcher
from resumebuddy.ports.llm import ILLMClient

class ResearcherAdapter(IResearcher):
    def __init__(self, client: ILLMClient, kb_dir: str = "knowledge-base/companies"):
        self.client = client
        self.kb_dir = kb_dir
        os.makedirs(self.kb_dir, exist_ok=True)

    async def research_company(self, company_name: str, model: Optional[str] = None) -> Dict[str, Any]:
        now = datetime.now()
        current_date = now.strftime("%B %Y")

        prompt = f"""Research the company: {company_name}.
Provide a comprehensive summary of the LAST 12 MONTHS (relative to {current_date}).
The JSON must have these keys: "news", "layoffs", "performance", "culture", "status", "overall_sentiment".
IMPORTANT: Return ONLY a valid JSON object. No other text.
"""
        response = await self.client.complete_prompt(prompt, model=model)
        try:
            data = json.loads(response.strip().strip("```json").strip("```"))
            self._save_to_kb(company_name, data)
            return data
        except:
            return {"error": f"Failed to research {company_name}"}

    def _save_to_kb(self, company_name: str, data: Dict[str, Any]):
        filename = f"{company_name.lower().replace(' ', '_')}.md"
        filepath = os.path.join(self.kb_dir, filename)
        
        def format_section(val):
            if isinstance(val, list):
                if not val: return "N/A"
                if isinstance(val[0], dict):
                    keys = val[0].keys()
                    header = "| " + " | ".join(keys) + " |"
                    sep = "| " + " | ".join(["---"] * len(keys)) + " |"
                    rows = ["| " + " | ".join(str(item.get(k, "")) for k in keys) + " |" for item in val]
                    return "\n".join([header, sep] + rows)
                return "\n".join([f"- {item}" for item in val])
            elif isinstance(val, dict):
                return "\n".join([f"- **{k}**: {v}" for k, v in val.items()])
            return str(val)

        with open(filepath, "w") as f:
            f.write(f"# Company Intel: {company_name}\n\n")
            f.write(f"## News Highlights\n{format_section(data.get('news'))}\n\n")
            f.write(f"## Layoffs & Hiring\n{format_section(data.get('layoffs'))}\n\n")
            f.write(f"## Performance\n{format_section(data.get('performance'))}\n\n")
            f.write(f"## Culture\n{format_section(data.get('culture'))}\n\n")
            f.write(f"## Status\n{data.get('status', 'N/A')}\n\n")
            f.write(f"## Sentiment\n**{data.get('overall_sentiment', 'N/A')}**\n")

    def get_company_intel(self, company_name: str) -> Optional[str]:
        filename = f"{company_name.lower().replace(' ', '_')}.md"
        filepath = os.path.join(self.kb_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                return f.read()
        return None
