import asyncio
import json
from rich import print
from resumebuddy.infrastructure.adapters.ollama import OllamaAdapter
from resumebuddy.application.use_cases import ResumeBuddyUseCases
from resumebuddy.domain.models import RoleEvaluation

# GOLDEN DATASET: A fixed Resume and JD with an expected score.
# This proves we can quantify and track model performance.
GOLDEN_RESUME = """
STEPHEN JAEB
Staff Architect & AI Strategist with 20+ years of experience.
Expert in Python, Polars, Pydantic, AWS.
Lead Architect at Symetra.
"""

GOLDEN_JD = """
Senior Data Engineer at Mozilla.
Requires 4+ years of experience in Python, SQL, and data pipelines.
Focus on user privacy and AI integration.
"""

EXPECTED_OVERALL_SCORE = "A"

async def run_evaluation():
    llm_client = OllamaAdapter()
    use_cases = ResumeBuddyUseCases(llm_client)
    
    print("[bold blue]Starting Systematic Model Evaluation...[/bold blue]")
    
    # 1. Run the evaluation
    result: RoleEvaluation = await use_cases.evaluate_role(
        resume_text=GOLDEN_RESUME,
        jd_data={"description": GOLDEN_JD, "title": "Senior Data Engineer"},
    )
    
    print(f"\n[bold green]Evaluation Result:[/bold green]")
    print(f"Overall Score: {result.overall_score}")
    print(f"BS Score: {result.bs_detector.score}/10")
    print(f"Rationale: {result.rationale[:100]}...")
    
    # 2. Check for "Drift" (Simple version: score mismatch)
    if result.overall_score != EXPECTED_OVERALL_SCORE:
        print(f"\n[bold red]ALERT: Semantic Drift Detected![/bold red]")
        print(f"Expected: {EXPECTED_OVERALL_SCORE}, Received: {result.overall_score}")
    else:
        print(f"\n[bold green]SUCCESS: Model performance is stable.[/bold green]")

if __name__ == "__main__":
    asyncio.run(run_evaluation())
