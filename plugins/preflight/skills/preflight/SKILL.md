---
name: preflight
description: Dispatch an Opus 4.7 agent and an OpenCode/GPT-5.5 run to review all changes on the current branch since it diverged from main. Use when the user invokes /preflight, before opening a PR.
---

# Preflight

## Overview

Run two parallel reviews of the diff between the current branch and `main`: one Opus 4.7 subagent and one OpenCode invocation using GPT-5.5. Relay both sets of findings to the user.

## Process

1. Determine the merge base and diff scope:
   - `git merge-base HEAD main` to find the divergence point
   - `git diff --stat $(git merge-base HEAD main)..HEAD` to see scope
   - `git log --oneline $(git merge-base HEAD main)..HEAD` for commit context

2. Write a review prompt file to `$TMPDIR/branch_review_prompt.md` containing:
   - Review goals: correctness bugs, security issues, error handling, test coverage gaps, API/contract changes, anything that would block a PR
   - Skip: nits, style preferences already enforced by linters, speculative refactors
   - **Do not run tests.** This review is purely about reading the code. Tests are run separately (before invoking this skill or in CI).
   - Output format: prioritized findings (Blocker / Should-fix / Consider), each with file:line and a concrete suggestion
   - The commit list from step 1
   - The full diff (`git diff <merge-base>..HEAD`)

3. Launch both reviewers **in parallel** (single message, two tool calls):

   **Opus 4.7 subagent** — use the `Agent` tool with:
   - `subagent_type: "general-purpose"`
   - `model: "opus"`
   - `description: "Branch review — Opus 4.7"`
   - A self-contained prompt that includes the merge base SHA, instructions to run `git diff <merge-base>..HEAD` and read changed files in full, and the review goals/format above. Explicitly instruct the agent not to run tests, builds, or other validation commands, this is a read-only code review.

   **GPT-5.5 via OpenCode** — use the `Bash` tool with `dangerouslyDisableSandbox: true`:
   ```bash
   GPT_OUT="$TMPDIR/gpt55_review.md"
   GPT_ERR="$TMPDIR/gpt55_review_err.log"
   opencode run \
     "Review the branch changes in the attached file. Output ONLY a prioritized findings list (Blocker/Should-fix/Consider), each with file:line and a concrete suggestion. No preamble, no summary, no commentary. If no issues, print: 'No significant issues found.'" \
     --model grove-openai/gpt-5.5 \
     -f "$TMPDIR/branch_review_prompt.md" \
     > "$GPT_OUT" 2>"$GPT_ERR"
   echo "exit:$?"
   ```
   Set timeout to 300000ms. Do **not** read stdout/stderr into context. After the Bash call returns, use the `Read` tool to read `$TMPDIR/gpt55_review.md` for the findings.

4. Relay both sets of findings to the user, clearly labeled **Opus 4.7** and **GPT-5.5**. Do not act on them unless asked.

## Notes

- The prompt file written in step 2 serves the GPT-5.5 run. The Opus agent fetches the diff itself via git.
- The Opus agent has no conversation context. The prompt must be self-contained.
- `dangerouslyDisableSandbox: true` is required for the OpenCode Bash call because OpenCode writes to `~/.local/share/opencode/`.
- GPT-5.5 stdout goes to `$TMPDIR/gpt55_review.md`; stderr goes to `$TMPDIR/gpt55_review_err.log`. Read the output file after the Bash call completes rather than capturing stdout. If the output file is empty or missing, check the error log.
