import os
import sys
import sqlite3
import re
import json

# Add src to path to import models and repository
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from resumebuddy.domain.models import JobOpportunity
from resumebuddy.infrastructure.adapters.repository import SQLiteJobRepository

def extract_prospects_from_script(script_path):
    with open(script_path, 'r') as f:
        content = f.read()
    
    # Use regex to find the prospects list definition
    # This is a bit brittle but works for this one-time migration
    match = re.search(r'prospects = \[(.*?)\]', content, re.DOTALL)
    if not match:
        print("Could not find prospects list in scripts/generate_dashboard.py")
        return []
    
    # We can't easily eval() because it contains dicts and might have logic
    # But generate_dashboard.py's prospects list is mostly static dicts
    # Let's try to extract it by parsing the string as a list of dicts
    prospects_str = "[" + match.group(1) + "]"
    
    # Clean up comments and trailing commas for json-like parsing if possible
    # Or just use a simple eval since it's a trusted local script
    try:
        # We need to define any variables used in the script if there are any
        # Looking at the script, it's mostly literal values
        prospects = eval(prospects_str)
        return prospects
    except Exception as e:
        print(f"Error evaluating prospects string: {e}")
        return []

def main():
    script_path = "scripts/generate_dashboard.py"
    if not os.path.exists(script_path):
        print(f"Error: {script_path} not found.")
        return

    prospects = extract_prospects_from_script(script_path)
    if not prospects:
        print("No prospects found to migrate.")
        return

    repo = SQLiteJobRepository("jobs.db")
    print(f"Migrating {len(prospects)} jobs to SQLite...")

    for p in prospects:
        job = JobOpportunity(
            id=p['id'],
            name=p['name'],
            score=p['score'],
            priority=p['priority'],
            url=p['url'],
            dir=p['dir'],
            status=p.get('default_status', 'Ready to Apply')
        )
        repo.save_job(job)
        print(f" Saved: {job.name}")

    print("Migration complete. Database 'jobs.db' created/updated.")

if __name__ == "__main__":
    main()
