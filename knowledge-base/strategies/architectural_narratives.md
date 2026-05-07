# Architectural Narratives & Definitions

### 1. Governance as Code
**Definition:** Automating policy enforcement through the technical stack rather than manual audits.
**In Practice:** "I write Pydantic schemas that enforce HIPAA/SOC2 rules at the API level. If data is non-compliant, the system automatically rejects it before it hits the database or an AI model."

### 2. The Deterministic AI Harness
**Definition:** A systems-engineering approach to managing the non-deterministic nature of LLMs.
**In Practice:** "I wrap LLM agents in state machines (Temporal/LangGraph) and validation layers. The AI provides the 'intelligence,' but my code provides the 'guardrails' ensuring the output always matches a trusted schema."

### 3. Forensic Data Engineering
**Definition:** Data engineering with 100% provenance and schema integrity.
**In Practice:** "I build integration hubs that treat every data point as a scientific record. Using vectorized compute (Polars/Arrow), I can deliver 80x performance gains while maintaining a perfect audit trail of how data was transformed for AI training."
