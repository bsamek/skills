---
name: delegated-plan-execution
description: Execute an approved Plan-mode plan by delegating each step to a Sonnet implementer, then to fresh Sonnet spec-compliance and code-quality validators. One fix pass on failure, then escalate to the orchestrator. Commits per step. Use after Plan mode has produced a plan you want to execute under delegation.
---

# delegated-plan-execution

You are the orchestrator. The user has already used Claude Code's Plan mode to produce an approved plan file. Your job is to execute that plan one step at a time, delegating each step to a Sonnet subagent and then to two fresh Sonnet validator subagents (spec-compliance, then code-quality). You do not edit code yourself unless escalation kicks in.

This skill never invents work outside the plan. If you find yourself wanting to refactor, add a feature, or "improve" something not in the plan, stop — that belongs in a separate planning round.

## When this skill applies

- The user has an approved plan file (typically at `~/.claude/plans/<slug>.md`) and wants it executed under delegation.
- Do NOT invoke this for ad-hoc edits, single-file fixes, or tasks small enough that delegation overhead exceeds the work itself.

## Loop

### 1. Locate the plan file

- If the user passed a path as the skill argument, use it.
- Otherwise, list `~/.claude/plans/` sorted by mtime, pick the most recent, and confirm with the user before proceeding.

### 2. Parse the steps

Plan files written by Plan mode follow this convention: numbered subsections under `## Approach`, each ending in a `**Validate (step N):**` bulleted block.

- Treat each numbered subsection as one delegation unit.
- If a subsection clearly bundles more than one conceptual change (e.g. "add a package AND wire up CI AND update the README"), split it into smaller delegation units before dispatching. Err on the side of splitting — the validator cannot tell you which sub-change regressed if a step does too much. Tell the user about any splits before you start.

### 3. Verify clean starting state

Before step 1: run `git status`. If the tree is dirty with changes unrelated to the plan, stop and ask the user how to proceed. Do not stash or discard without explicit consent.

Record the pre-execution HEAD SHA — you will pass it to validators as the baseline.

### 4. For each step, in order

#### a. Implement

Dispatch the implementer via the Agent tool with:
- `subagent_type: "general-purpose"`
- `model: "sonnet"` (no version pinning beyond the family name)
- `description: "Implement plan step N"`
- The prompt template below, with `<path>` and `N` substituted.

Wait for it to return. Capture the reported commit SHAs.

**Implementer prompt template:**

> You are implementing step N of an approved plan at `<path>`. Read the plan in full so you have context, but implement ONLY step N. Do not start or finish neighbouring steps. Do not "improve" code outside the step.
>
> Use strict TDD even for MVP, hackathon, or exploratory work. Do not appeal to timeline, smallness of the change, or "this is throwaway" as a reason to skip tests. The cycle is red → green → refactor:
> 1. Write the failing test first. Run it and confirm it fails for the reason you expect (not e.g. an import error or syntax error).
> 2. Write the minimum implementation to make it pass. Run the test and confirm it passes.
> 3. Refactor if useful, keeping the test green.
>
> If a piece of behaviour is genuinely untestable in this environment (e.g. requires a real external service with no local stub), say so explicitly in your final report and explain why. Do not silently omit the test.
>
> Read the project's `AGENTS.md` (and `CLAUDE.md` if present) before editing, in case the project has additional discipline.
>
> Make one or more git commits as you go, with messages prefixed `step N: ...` — typically a red commit (failing test), a green commit (implementation), and optionally a refactor commit. Do not amend or squash. Run the full test suite at the end of the step, not just the new tests. Leave the working tree clean (`git status` empty) before returning.
>
> Final report (required structure):
> - Commit SHAs, in order, with one-line descriptions.
> - Full test-suite result (pass/fail counts).
> - Any deviation from the plan, with justification.
> - Any behaviour you deemed untestable, with reason.

#### b. Check git state

Before dispatching the validators, verify yourself:
- `git status` is clean.
- `git log <pre-step-sha>..HEAD --oneline` shows at least one commit with prefix `step N: ...`.
- No commits outside the step range.

If any of those fail, do NOT dispatch validators yet. Either re-dispatch the implementer with a corrective note or escalate immediately (the implementer has produced an inconsistent state).

#### c. Spec-compliance validation (fresh)

Dispatch a brand-new Agent call (not SendMessage to anything existing) with:
- `subagent_type: "general-purpose"`
- `model: "sonnet"`
- `description: "Spec validation, step N"`
- The prompt below.

**Spec validator prompt template:**

> You have no prior context for this work. The approved plan is at `<path>`. Step N has just been implemented in commits `<sha-range>` (baseline before the step was `<pre-step-sha>`).
>
> Inspect what changed: `git log --oneline <pre-step-sha>..HEAD`, `git show <sha>` for each commit, and `git diff <pre-step-sha>..HEAD` for the cumulative view. Also run `git status` to confirm the tree is clean — if it is not, that is a FAIL regardless of other findings.
>
> Read the plan's step N section, including the `**Validate (step N):**` bullets. For each Validate bullet, mark PASS or FAIL with file/line evidence. Also mark FAIL if the step is missing required scope from the section body (not just the bullets).
>
> Do NOT comment on code style, naming, duplication, or "improvements." That is the code-quality reviewer's job. Stay strictly on spec compliance.
>
> Final line of your report must be exactly `RESULT: PASS` or `RESULT: FAIL`.

#### d. Code-quality validation (fresh)

Dispatch a separate brand-new Agent call (do not reuse the spec validator's session):
- Same `subagent_type`, `model`, fresh `description`.

**Quality validator prompt template:**

> You have no prior context for this work. Step N of the plan at `<path>` was just implemented in commits `<sha-range>`. Read the diff (`git diff <pre-step-sha>..HEAD`) and the new test files in full.
>
> Assess:
> - Do the new tests actually exercise behaviour, or do they only check that code compiles / functions are callable? Flag any test whose assertions could pass against a stub implementation.
> - Is there dead code, premature abstraction, duplication, or unnecessary configurability?
> - Are error paths only handled where they cross a real system boundary (user input, external APIs)? Flag invented error handling for things that cannot fail.
> - Are comments justified (non-obvious why), or are they narrating what the code does? Project rule: no narrative comments.
> - Does `git status` show a clean tree? If not, that is a FAIL.
>
> Do NOT re-check whether the step meets its `**Validate (step N):**` bullets — that is a separate pass. Stay on code quality.
>
> Report concrete issues with `file:line` references. Final line must be exactly `RESULT: PASS` or `RESULT: FAIL`.

#### e. Both pass → next step

Move to step N+1.

#### f. One or both fail → fix pass

Dispatch the implementer one more time (fresh Agent call) with the combined validator reports:

**Fix-pass prompt template:**

> Step N was implemented in commits `<sha-range>` but failed validation.
>
> Spec validator findings:
> ```
> <spec report>
> ```
>
> Code-quality validator findings:
> ```
> <quality report>
> ```
>
> Address every FAIL item. Make new commits prefixed `step N fix: ...`. Do not rewrite, amend, or squash prior commits. Leave the tree clean. Run the full test suite at the end. Report the new commit SHAs and which finding each commit addresses.

Then re-dispatch BOTH validators fresh against the new commit range. If both now pass, proceed. If either still fails, go to step g.

#### g. Second failure → escalate

Stop the loop. Print:
- Which step failed.
- The final validator reports.
- The commit range produced so far.
- A short orchestrator note describing what the next direct action should be.

Then return to the user. You (the orchestrator) take over directly in the next conversation turn — escalation is not a separate dispatch. Do not silently retry. Do not roll back commits without the user's consent.

### 5. End of run

Print a summary table:

```
Step | Implementer commits | Spec | Quality | Fix-pass | Outcome
-----+---------------------+------+---------+----------+--------
1    | abc123, def456      | PASS | PASS    | —        | done
2    | ...
```

Then stop. Do not auto-suggest follow-up work.

## Commit-per-step discipline

- The implementer commits as it goes. The orchestrator never commits on behalf of the implementer.
- Fix-pass adds new commits, never amends.
- This is what makes the validator's `git log` / `git status` check meaningful.

## Worktrees

This skill does NOT mandate git worktrees. If the user wants isolation, they should branch before invoking the skill. The skill itself is branch-agnostic.

## What this skill does NOT do

- No design-doc gate. Plan mode is the design surface.
- No committed `docs/` planning artifacts.
- No second slash command.
- No auto-promotion to a global skill — the user can `mv` to `~/.claude/skills/` if it proves out.
- No meta "skill that updates this skill" — use `skill-creator` if iteration is needed.
