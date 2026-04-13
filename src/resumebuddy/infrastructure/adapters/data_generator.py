import os
import json
import asyncio
import re
import time
import sys
from google import genai
from typing import Dict, Any
from rich.console import Console
from rich.progress import (
    Progress,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    MofNCompleteColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

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
                except Exception:
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
        Loops through industries and saves to JSONL incrementally with enhanced progress tracking.
        """
        console = Console()
        console.print(f"[bold blue]🚀 Starting generation of {count} examples using {self.model_id}...[/bold blue]")
        console.print("[yellow]Press Ctrl+C to stop (Graceful exit after current item, or double-tap to kill).[/yellow]\n")
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Statistics tracking
        start_time = time.time()
        success_count = 0
        failure_count = 0
        durations = []
        stop_requested = False

        pg = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            TextColumn("•"),
            TimeElapsedColumn(),
            TextColumn("•"),
            TimeRemainingColumn(),
            TextColumn("{task.fields[status]}"),
            console=console,
        )

        with pg:
            task = pg.add_task("[cyan]Generating Data", total=count, status="")
            
            for i in range(count):
                if stop_requested:
                    break

                industry = SEED_INDUSTRIES[i % len(SEED_INDUSTRIES)]
                item_start = time.time()
                
                try:
                    pg.update(task, status=f"[bold blue](Current: {industry})[/bold blue]")
                    data = await asyncio.to_thread(self.generate_quadruplet, industry)
                    item_duration = time.time() - item_start
                    
                    if "error" not in data:
                        with open(output_file, "a") as f:
                            f.write(json.dumps(data) + "\n")
                            f.flush()
                        success_count += 1
                        durations.append(item_duration)
                        pg.update(task, advance=1, status=f"[green]Last: {item_duration:.1f}s[/green]")
                    else:
                        error_msg = str(data['error'])
                        failure_count += 1
                        if "429" in error_msg:
                            pg.update(task, status="[bold red]⚠️ Rate Limit Hit! Waiting 60s...[/bold red]")
                            await asyncio.sleep(60)
                        else:
                            pg.update(task, status=f"[red]❌ Error: {error_msg[:30]}...[/red]")
                            await asyncio.sleep(2)
                
                except KeyboardInterrupt:
                    pg.update(task, status="[bold yellow]🛑 Stopping after current item...[/bold yellow]")
                    stop_requested = True
                except Exception as e:
                    failure_count += 1
                    pg.update(task, status=f"[red]❌ Unexpected: {str(e)[:30]}...[/red]")
                    await asyncio.sleep(2)

        # Final Summary
        total_duration = time.time() - start_time
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        console.print("\n[bold green]🏁 Generation Session Complete![/bold green]")
        console.print(f"• [bold]Total Time:[/bold] {total_duration/60:.1f} minutes")
        console.print(f"• [bold]Items Generated:[/bold] {success_count} / {count}")
        console.print(f"• [bold]Average Time per Item:[/bold] {avg_duration:.1f} seconds")
        console.print(f"• [bold]Failures Encountered:[/bold] {failure_count}")
        console.print(f"• [bold]Output File:[/bold] {output_file}\n")

if __name__ == "__main__":  # pragma: no cover
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not found in environment.")
    else:
        # Default to 100, or take from command line
        gen_count = 100
        if len(sys.argv) > 1:
            try:
                gen_count = int(sys.argv[1])
            except ValueError:
                print(f"Invalid count provided: {sys.argv[1]}. Using default of 100.")
        
        gen_instance = FineTuneDataGenerator(api_key)
        asyncio.run(gen_instance.run(count=gen_count))
