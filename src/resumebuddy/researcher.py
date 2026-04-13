import os
import asyncio
from typing import Dict, Any, List, Optional
from .ollama_client import OllamaClient

class Researcher:
    """
    Ingests and summarizes company-specific intel (layoffs, performance, culture).
    Stores results in a Karpathy-style knowledge base.
    """
    def __init__(self, client: OllamaClient, kb_dir: str = "knowledge-base/companies"):
        self.client = client
        self.kb_dir = kb_dir
        os.makedirs(self.kb_dir, exist_ok=True)

    async def research_company(self, company_name: str, model: Optional[str] = None) -> Dict[str, Any]:
        """
        Gathers real-world highlights for a company using the LLM's internal knowledge.
        """
        from datetime import datetime
        now = datetime.now()
        current_date = now.strftime("%B %Y")
        twelve_months_ago = now.replace(year=now.year - 1).strftime("%B %Y")

        prompt = f"""Research the company: {company_name}.
Provide a comprehensive summary of the LAST 12 MONTHS (relative to {current_date}).
Break down the data into the following categories:
1. Quarterly News & Headlines: List the key news items for each quarter in the last year.
2. Layoff History: List specific dates and numbers of impacted employees if known.
3. Financial Performance: Stock trends, funding rounds, or revenue reports.
4. Culture Sentiment: "Good to work for" trends from Glassdoor/Reddit/Blind.
5. Growth Status: Is it a startup, scale-up, or enterprise?

IMPORTANT: Return ONLY a valid JSON object. No other text. 
The current date is {current_date}. If your internal knowledge base does not extend to 2026, provide the most recent available historical data (e.g., from 2024 or 2025) and state the timeframe clearly within each section. DO NOT use placeholders like "Information unavailable."

The JSON must have these keys: "news", "layoffs", "performance", "culture", "status", "overall_sentiment".
"""
        response = await self.client.complete_prompt(prompt, model=model)
        try:
            import json
            data = json.loads(response.strip().strip("```json").strip("```"))
            
            # Save to Karpathy-style KB
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
                # If list of dicts, try to make a table or bullet points
                if isinstance(val[0], dict):
                    keys = val[0].keys()
                    header = "| " + " | ".join(keys) + " |"
                    sep = "| " + " | ".join(["---"] * len(keys)) + " |"
                    rows = []
                    for item in val:
                        rows.append("| " + " | ".join(str(item.get(k, "")) for k in keys) + " |")
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
        
        print(f"Knowledge Base updated for {company_name}: {filepath}")

    def get_company_intel(self, company_name: str) -> Optional[str]:
        filename = f"{company_name.lower().replace(' ', '_')}.md"
        filepath = os.path.join(self.kb_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                return f.read()
        return None
