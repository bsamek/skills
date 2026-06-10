---
name: preflight
description: Run an OpenCode (GPT-5.5) review of all changes on the current branch since it diverged from main. Use when the user invokes /preflight, before opening a PR.
---

# Preflight

## Overview

Run an OpenCode review (GPT-5.5) of the diff between the current branch and `main`. Relay the findings to the user.

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

3. Run OpenCode — use the `Bash` tool with `dangerouslyDisableSandbox: true`:
   ```bash
   OC_OUT="$TMPDIR/opencode_review.md"
   OC_ERR="$TMPDIR/opencode_review_err.log"
   opencode run \
     "Review the branch changes in the attached file. Output ONLY a prioritized findings list (Blocker/Should-fix/Consider), each with file:line and a concrete suggestion. No preamble, no summary, no commentary. If no issues, print: 'No significant issues found.'" \
     --model "${PREFLIGHT_OPENCODE_MODEL:-grove-openai/gpt-5.5}" \
     -f "$TMPDIR/branch_review_prompt.md" \
     > "$OC_OUT" 2>"$OC_ERR"
   echo "exit:$?"
   ```
   Set timeout to 300000ms. Do **not** read stdout/stderr into context. After the Bash call returns, use the `Read` tool to read `$TMPDIR/opencode_review.md` for the findings.

4. Relay the findings to the user. Do not act on them unless asked.

## Notes

- `dangerouslyDisableSandbox: true` is required for the OpenCode Bash call because OpenCode writes to `~/.local/share/opencode/`.
- The OpenCode model is read from `PREFLIGHT_OPENCODE_MODEL`, defaulting to `grove-openai/gpt-5.5` (GPT-5.5 via the MongoDB-internal Grove gateway). Set this env var to whatever GPT-5.5 model identifier your OpenCode setup supports; the default will not work outside MongoDB.
- OpenCode stdout goes to `$TMPDIR/opencode_review.md`; stderr goes to `$TMPDIR/opencode_review_err.log`. Read the output file after the Bash call completes rather than capturing stdout. If the output file is empty or missing, check the error log.
