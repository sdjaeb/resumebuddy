# Experience Presentation: Professional vs. R&D

To maintain 100% integrity while still highlighting cutting-edge AI skills, follow these rules for all resumes and social profiles.

## 0. The Source of Truth
*   **Baseline Resume:** Always use the root `resume.txt` as the mandatory source of truth for all job titles, dates, and historical technical facts.
*   **Tailoring Logic:** When tailoring for a specific role, select and rephrase bullet points from `resume.txt` that align with the target JD. Do not invent new responsibilities, but emphasize the specific technical achievements (e.g., performance tuning, orchestration, or compliance) that matter most to the hiring manager.

## 1. Clear Section Boundaries
*   **Professional Experience (Paid):** Focus strictly on the technical stack and business impact delivered during your tenure. 
    *   *Example (Symetra):* "Architecting a Python/FastAPI Integration Hub... ensuring 100% payload correctness."
*   **Strategic R&D & Open Source (Unpaid/Hobby):** This is where you claim **LangGraph, Agentic RAG, and AI Safety.**
    *   *Example (Data Platform Playbook):* "Principal Architect (R&D). Designing autonomous multi-agent systems using LangGraph..."

## 2. The "Bridge" Phrasing
When you want to mention an R&D skill inside a professional role description, use **Investigation** or **Feasibility** keywords.
*   **Allowed:** "Conducted feasibility research on integrating LLM-based verification into the SDLC."
*   **Allowed:** "Investigating the application of agentic state-machines to legacy distributed workers."
*   **Avoid:** "Shipped LangGraph to production" (unless you actually did).

## 3. Skill Categorization
In the "Skills" section of your resume, categorize clearly:
*   **Core Competencies (Production):** Distributed Systems, Python, AWS, Pydantic, Polars.
*   **Strategic Focus (R&D):** LangGraph (Stateful Agents), LLM Guardrails, Semantic Drift Detection.

## 4. The Interview Narrative
When asked about your AI experience, always lead with the **Staff Architect perspective**:
> "In my professional work at Symetra/Veda, I built the high-scale data engines that serve as the foundation for AI. Parallel to that, in my personal R&D (Data Platform Playbook), I have been architecting the agentic orchestration layer using LangGraph. This allows me to bring 20 years of production rigor to the emerging AI stack."
