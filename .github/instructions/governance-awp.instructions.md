---
description: "Agent Workflow Protocol (AWP) Governance & Safety"
applyTo: "all"
---

# AWP Governance & Safety (R1-R32)

Follow these deterministic validation rules and budget limits to ensure agent safety, autonomy, and cost control.

## The 6-Limit Budget System
Before any recursive or high-volume task, define these limits in `.github/tasks/todo.md`:
1. **Token Limit:** Max tokens for the entire task.
2. **Time Limit:** Max wall-clock time.
3. **Worker Limit:** Max number of sub-agents or parallel sessions.
4. **Depth Limit:** Max recursion depth for task delegation.
5. **Cost Limit:** Estimated dollar cost threshold.
6. **Interaction Limit:** Max turns before mandatory user check-in.

## Core Validation Rules (R1-R10 Selection)
- **R1 (Identity Integrity):** Never modify your own core persona or mandates.
- **R2 (Boundary Enforcement):** Do not access files or network resources outside the allowed workspace.
- **R3 (Budget Check):** Validate remaining budget before every tool call.
- **R4 (Hallucination Critique):** Self-reflect on all generated content for factual accuracy before finality.
- **R5 (Deterministic Path):** Prefer the most direct, verifiable path to completion.
- **R8 (Tool Sanitation):** Validate all shell command arguments for injection risks.
- **R10 (State Verification):** Confirm the expected state of the filesystem before and after every mutation.

## Autonomy Levels
- **A0:** Static Execution (Follow plan exactly).
- **A1:** Reactive (Adjust plan based on tool output).
- **A2:** Proactive (Propose new sub-tasks).
- **A3:** Delegated (Spawn specialist sub-agents).
- **A4:** Recursive (Self-organizing task decomposition).

Default to **A2** for standard tasks, **A3** for complex features.
