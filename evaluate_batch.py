import json
import subprocess
import os
import re

def run_evaluation():
    if not os.path.exists("prospective_jobs.jsonl"):
        print("Error: prospective_jobs.jsonl not found.")
        return

    with open("prospective_jobs.jsonl", "r") as f:
        jobs = [json.loads(line) for line in f]

    report_path = "output/batch_evaluation_report.md"
    os.makedirs("output", exist_ok=True)

    with open(report_path, "w") as report:
        report.write("# Batch Evaluation Report\n\n")
        report.write("| Index | Company | Title | Overall Score | Rationale |\n")
        report.write("|-------|---------|-------|---------------|-----------|\n")

        for i, job in enumerate(jobs):
            company = job.get('company', 'Unknown')
            title = job.get('title', 'Unknown')
            url = job.get('url', 'Unknown')
            
            print(f"[{i}/{len(jobs)}] Evaluating {title} at {company}...")
            
            cmd = f"rtk uv run resumebuddy evaluate --resume resume.txt --index {i} --model gemma4:e4b"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            stdout = result.stdout
            stderr = result.stderr
            
            score = "N/A"
            rationale = "No rationale found."
            
            if "403 Forbidden" in stdout or "403 Forbidden" in stderr or "403" in stdout:
                score = "Blocked (403)"
                rationale = f"Access denied on source: {company}. URL: {url}"
            elif "404 Not Found" in stdout or "404" in stdout:
                score = "Not Found (404)"
                rationale = f"Job listing no longer exists on source: {company}. URL: {url}"
            elif "Error during evaluation" in stdout:
                score = "Error"
                rationale = "Evaluation failed (likely LLM parsing issue)."
            else:
                # Attempt to extract score
                # Regex for "Overall Score:  A- " or similar
                score_match = re.search(r"Overall Score:\s+([A-F][+-]?)", stdout)
                if score_match:
                    score = score_match.group(1)
                
                # Attempt to extract rationale (text after "Rationale:")
                if "Rationale:" in stdout:
                    rationale = stdout.split("Rationale:")[1].strip()
                    # Clean up rationale for table (remove newlines, limit length)
                    rationale = rationale.replace("\n", " ").replace("|", "I")
                    if len(rationale) > 200:
                        rationale = rationale[:197] + "..."

            report.write(f"| {i} | {company} | {title} | {score} | {rationale} |\n")
            report.flush()
            print(f"  Result: {score}")

    print(f"\nBatch evaluation complete. Report saved to {report_path}")

if __name__ == "__main__":
    run_evaluation()
