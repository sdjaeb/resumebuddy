---
name: codex-verification-before-completion
description: Use when reporting that work is fixed, complete, or ready; requires fresh verification evidence tied to the current change.
---

# Codex Verification Before Completion

## Purpose

Use this skill whenever you are about to say a task is fixed, complete,
passing, or ready for review. Inspection is not proof. Old test output is not
proof. Claims require fresh evidence from the current state.

## Core rules

- Do not say a change is done without running at least one relevant validation
  command after the final edit.
- Prefer the narrowest command that proves the changed behavior.
- If full validation is not possible, state the gap explicitly instead of
  implying success.
- Tie each completion claim to the command that supports it.
- If verification fails, report the failure plainly and continue debugging.

## Verification workflow

1. Identify what changed.
   - Behavior, configuration, workflow, or documentation.
2. Choose the proof.
   - Test command, lint/type check, diff hygiene, runtime probe, or file-system
     check appropriate to the change.
3. Run the proof after the final change.
   - Fresh output only. Do not rely on stale results from before the last edit.
4. Report the result concretely.
   - Include the command and the outcome.
   - If there are gaps, list them as unverified items.

## Minimum evidence by change type

- Code behavior change: targeted test or executable reproduction.
- Debug fix: reproduction command or log probe showing the failure is gone.
- Repo guidance/docs update: `git diff --check` and a content sanity review.
- Branch/worktree workflow change: `git worktree list`, branch status, and
  path verification.
- Global skill install: file existence checks in the destination directory.

## Response pattern

When closing work, report:

- what changed,
- what you ran to verify it,
- what passed,
- and anything not verified.

If you could not run verification, say that directly.
