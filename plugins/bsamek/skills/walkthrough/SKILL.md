---
name: walkthrough
description: Walk the user through their branch's changes chunk by chunk so they can self-review before opening a PR. Use when the user invokes /walkthrough.
---

# Walkthrough

## Overview

Explain the diff between the current branch and `main` in digestible chunks, pausing between each so the user can review and ask questions.

## Process

1. Find the divergence point: `git merge-base HEAD main`.

2. Get the list of changed files: `git diff --stat <merge-base>..HEAD`. Share a one-line summary of the branch's scope (file count, rough theme from commit messages).

3. Group changes into logical chunks. A chunk is usually one file, or a tight cluster of related hunks. For large files, split by function/section.

4. For each chunk, in order:
   - State which file (and section) is up.
   - Show the diff for that chunk (`git diff <merge-base>..HEAD -- <path>`, optionally narrowed).
   - Explain in 2-4 sentences: what changed, why (inferred from surrounding code and commit messages), and anything subtle or risky.
   - Stop and wait for the user. They'll say "next", ask a question, or request a deeper look.

5. After the last chunk, offer a brief overall summary and call out anything the user might want to double-check before pushing.

## Notes

- One chunk per turn. Don't dump the whole diff at once.
- Read the full file when needed for context. The diff alone often hides why a change matters.
- If a commit message explains intent, quote it rather than guessing.
