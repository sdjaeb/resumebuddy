---
name: codex-systematic-debugging
description: Use when debugging a bug, failing test, broken integration, or unexpected behavior and you need root-cause-first investigation before proposing fixes.
---

# Codex Systematic Debugging

## Purpose

Use this skill before proposing a fix for any defect. The goal is to identify
the actual failing boundary and fix the source of the problem, not the nearest
symptom.

## Core rules

- Do not propose or apply a fix before you can state the likely root cause.
- Read the exact error output, stack trace, payload, or log event first.
- Reproduce the problem or explain precisely why reproduction is blocked.
- When a flow crosses multiple components, gather evidence at each boundary.
- Prefer one minimal root-cause fix over layered defensive patches.

## Workflow

1. Capture the failing signal.
   - Record the exact command, request, log line, or event that shows the
     failure.
   - Note identifiers, timestamps, file paths, and environment details that
     constrain the issue.
2. Reproduce and narrow.
   - Confirm whether the issue is reproducible.
   - If not, gather more evidence instead of guessing.
   - Reduce the failing surface to the smallest path that still demonstrates
     the problem.
3. Trace the failing boundary.
   - Identify where the bad value, bad state, or wrong control flow first
     appears.
   - For multi-step systems, inspect what enters and exits each component.
4. Compare against a known-good reference.
   - Look for a working path in the codebase, tests, logs, or previous runs.
   - List the meaningful differences before choosing a fix.
5. State the root cause and proposed fix.
   - Explain the specific source of failure.
   - Explain why the selected fix addresses that source with minimal blast
     radius.
6. Verify after the fix.
   - Run fresh validation that would have failed before the change.
   - Report both the verification command and the result.

## Multi-boundary guidance

When the issue crosses service, script, API, or storage boundaries:

- Check the handoff at each boundary instead of assuming the deepest stack
  trace is the real source.
- Add or inspect diagnostics that show input, output, and key state at each
  layer.
- Name the first boundary where observed behavior diverges from expected
  behavior.

## Completion bar

Before calling a bug fixed, be able to state:

- the failing signal,
- the root cause,
- the exact change that addressed it,
- and the fresh verification that proves the issue no longer reproduces.
