import os
import json
import asyncio
import re
from google import genai
from typing import List, Dict, Any
from rich.progress import Progress

# Config: 20 Industries/Roles to ensure diversity
SEED_INDUSTRIES = [
    "AI/ML Engineering", "High-Scale Data Engineering", "Fintech Payment Architect",
    "SRE & Platform Engineering", "Cybersecurity Analyst", "Embedded Systems (C/C++)",
    "HealthTech Interoperability", "E-commerce Backend (Ruby/Node)", "Game Engine (Unity/C#)",
    "Cloud Solutions Architect (AWS)", "DevOps Manager", "Frontend Lead (React/Vue)",
    "Distributed Systems (Go/Rust)", "Database Administrator (SQL/NoSQL)", "Mobile Dev (Swift/Kotlin)",
    "Quantitative Finance Developer", "Blockchain/Web3 Architect", "SaaS Product Manager (Technical)",
    "Agile Scrum Master / Program Manager", "System Security Auditor"
]

class FineTuneDataGenerator:
    """
    Generates high-reasoning synthetic data for fine-tuning Gemma 4.
    Uses the new 'google-genai' SDK and the correct Gemma 4 26B model name.
    """
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemma-4-26b-a4b-it"

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """
        Robustly extracts JSON from LLM output, handling markdown blocks and unescaped characters.
        """
        match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
        if not match:
            match = re.search(r'(\{.*\})', text, re.DOTALL)
        
        if match:
            json_str = match.group(1)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                try:
                    cleaned = re.sub(r'(?<=[:\[,])\s*\n\s*(?=[{\["])', '', json_str)
                    return json.loads(cleaned)
                except:
                    return {"error": "Failed to parse JSON even after cleaning."}
        return {"error": "No JSON block found in response."}

    def generate_quadruplet(self, industry: str) -> Dict[str, str]:
        """
        Generates a (Resume, JD, Reasoning, Optimized Resume) quadruplet.
        """
        prompt = f"""Generate a high-quality synthetic training example for a resume expert AI.
Target Industry: {industry}

Requirements:
1. RAW RESUME: A realistic, slightly unoptimized resume (5-10 years experience).
2. JOB DESCRIPTION: A demanding JD from a top company (Anthropic, Google, Stripe).
3. ALIGNMENT REASONING: A detailed, step-by-step analysis of gaps and strengths (STAR method).
4. OPTIMIZED RESUME: A high-impact, perfectly aligned version of the resume.

Return the result as a JSON object with these exact keys: "instruction", "input", "output".
- "instruction": The JD.
- "input": The Raw Resume.
- "output": The Reasoning + The Optimized Resume.

IMPORTANT: Avoid using unescaped double quotes inside the values. Use single quotes for inner text or escape them correctly.
Ensure the "output" follows a professional, senior career consultant tone.
"""
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt
            )
            return self._extract_json(response.text)
        except Exception as e:
            return {"error": str(e)}

    async def run(self, count: int = 1000, output_file: str = "tmp/data/training_data.jsonl"):
        """
        Loops through industries and saves to JSONL incrementally.
        """
        print(f"Starting generation of {count} examples using {self.model_id}...")
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, "a") as f:
            with Progress() as progress:
                task = progress.add_task("[cyan]Generating data...", total=count)
                
                for i in range(count):
                    industry = SEED_INDUSTRIES[i % len(SEED_INDUSTRIES)]
                    data = await asyncio.to_thread(self.generate_quadruplet, industry)
                    
                    if "error" not in data:
                        f.write(json.dumps(data) + "\n")
                        f.flush()
                    else:
                        print(f"\nError during generation: {data['error']}")
                        if "429" in str(data['error']):
                            await asyncio.sleep(60)
                    
                    progress.update(task, advance=1)
                    await asyncio.sleep(2) # Moderate delay for Gemini Pro API limits

if __name__ == "__main__":
    import sys
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not found in environment.")
    else:
        # Default to 100, or take from command line
        count = 100
        if len(sys.argv) > 1:
            try:
                count = int(sys.argv[1])
            except ValueError:
                print(f"Invalid count provided: {sys.argv[1]}. Using default of 100.")
        
        generator = FineTuneDataGenerator(api_key)
        asyncio.run(generator.run(count=count))
