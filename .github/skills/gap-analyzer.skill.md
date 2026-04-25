---
name: gap-analyzer
description: Identifies technical and behavioral gaps between a candidate's resume and a specific Job Description.
---

# Gap Analyzer Skill

## Purpose
Systematically identify "Missing Skills" or "Weak Alignment" points to prepare for technical screens.

## Workflow
1. **Intake:** Read the full Job Description (JD) and the Candidate's Resume.
2. **Skill Mapping:** Categorize requirements into:
   - **Direct Match:** Strong evidence in resume.
   - **Tangential Match:** Experience in a related tool/stack (e.g., Pandas vs. Polars).
   - **Missing Skill:** No evidence found.
3. **Strategy Generation:** 
   - For **Direct Matches**: Select the strongest STAR story.
   - For **Tangential Matches**: Draft a bridge statement ("I've used X, which has similar patterns to Y...").
   - For **Missing Skills**: Draft a "Capacity to Accommodate" statement based on transferable architectural principles.

## Rules
- **Never Hallucinate:** If a skill is missing, state it honestly.
- **Focus on Principles:** If a specific library is missing, pivot to the underlying pattern (e.g., "I haven't used LangGraph, but I've built custom finite state machines in Python...").
