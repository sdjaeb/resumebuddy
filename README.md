# ResumeBuddy 🤖📄

ResumeBuddy is an agentic CLI application designed to transform the job search from a manual grind into a highly objective, data-driven operation. By leveraging local or cloud-based Large Language Models (like Gemma 4, Llama 3.2, or Anthropic/OpenAI models), ResumeBuddy automates the discovery, research, and evaluation of job postings against your specific career constraints.

**Why use ResumeBuddy?**
Job searching is exhausting and often subjective. ResumeBuddy provides an objective A-F score for roles based on your hard constraints (salary floors, tech stacks, location) and softer preferences (industry, startup vs. established company). It acts as your personal "Career Ops" platform, saving you hours of reading JDs that don't align with your goals.

## 🌟 Influences & Characteristics
This project embodies an **AI-Native Workflow** and an **Agentic Baseline** approach. It was heavily influenced by:
- [career-ops](https://github.com/santifer/career-ops): For the concept of treating the job search as an operational engineering problem with strict evaluation criteria.
- **Karpathy-style Knowledge Base / Obsidian**: The project utilizes a local, plain-text Markdown knowledge base (`knowledge-base/companies/`) for company research. This ensures your intel is highly readable (perfect for Obsidian), version-controllable, and easily injectable into LLM context windows without database overhead.

This project is built using a strict **Domain-Driven Design (DDD)** and **Hexagonal Architecture (Ports & Adapters)**. This decouples the core evaluation logic from specific scraper implementations or LLM providers, ensuring 100% test coverage and high maintainability.

## 🚀 Features

- **Interactive Profile Builder:** Define your salary floors, language preferences, and target industries to drive personalized job evaluations.
- **A-F Scoring System:** Evaluates roles across 12 dimensions (Skills, Culture, Company Health, Job Age, etc.).
- **Smart Scraping & Discovery:** Direct integration with **Workday, Greenhouse, Lever, and Ashby** job boards, plus generic scraping for remote job aggregators.
- **Automated Company Research:** Pulls 12 months of quarterly news, layoffs, and performance data into a local Markdown Knowledge Base.
- **Cover Letter Engine:** Generates letters that handle missing skills by highlighting tangential relevance or learning adaptability.

## 🛠 Installation

### Prerequisites
- [Ollama](https://ollama.ai/) installed and running locally.
- Recommended models: `gemma4:e4b` (High quality), `llama3.2:3b` (Fast/Efficient).
- [uv](https://github.com/astral-sh/uv) for Python dependency management.

### Setup
```bash
git clone <your-repo-url>
cd resumebuddy
uv venv
uv sync
```

## 📖 Usage

### 1. Build Your Profile
Set your job search constraints (salary, location, tech stack).
```bash
uv run resumebuddy profile
```

### 2. Fetch Prospective Jobs
Automatically discover jobs across configured sites and save them to `prospective_jobs.jsonl`.
```bash
uv run resumebuddy fetch
```

### 3. Evaluate a Job
Evaluate a discovered job by its index against your profile. It will automatically research the company if intel is missing.
```bash
# Provide your resume and the job index from the fetch list
uv run resumebuddy evaluate --resume sample_resume.md --index 2 --model llama3.2:3b
```
*(You can also evaluate a direct URL using `--jd "https://..."`)*

### 4. View Company Intel
Render a local wiki page for any researched company.
```bash
uv run resumebuddy view "Google"
```

### 5. Generate a Targeted Cover Letter
```bash
uv run resumebuddy cover-letter --resume sample_resume.md --jd "path/to/jd.txt"
```

## 🧠 Fine-Tuning a Cover Letter Model
Once you are ready to produce highly customized, expert-level cover letters or resume iterations, you can fine-tune a model using the provided synthetic data generator.

1. **Generate Data:** Use the script in `src/resumebuddy/data_generator.py` to create synthetic (Resume, JD, Rationale, Optimized Resume) quadruplets via the Google GenAI API.
    ```bash
    export GOOGLE_API_KEY="your_key"
    uv run python src/resumebuddy/data_generator.py
    ```
    *Note: The included `tmp/data/training_data.jsonl` currently has ~200 records. For optimal fine-tuning (e.g., using LoRA), you should aim to generate around 1,000 synthetic quadruplets.*
2. **Train:** Use a framework like `unsloth` to apply a LoRA/PEFT adapter to the base `gemma4:e4b` model using the generated `training_data.jsonl`.
3. **Export & Serve:** Convert the final adapter to GGUF format and load it back into Ollama as `gemma4-resume-expert`.

## 🧪 Testing
The project maintains 100% test coverage using `pytest`.
```bash
uv run pytest --cov=src/resumebuddy --cov-report=term-missing
```

## 🛡 Privacy & Governance
- **Privacy:** By default, `.gitignore` protects your personal `resume.txt` and `user_profile.json` from being committed.
- **AWP Guidelines:** This project follows the Agent Workflow Protocol (AWP) with strict 6-Limit budgeting to prevent runaway LLM costs.

---
*Built with ❤️ by Stephen Jaeb & Gemini CLI*
