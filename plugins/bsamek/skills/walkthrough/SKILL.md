---
name: walkthrough
description: Walk the user through their branch's changes on this branch by generating an HTML document. Use when the user invokes /walkthrough.
---

# Walkthrough

## Overview

Generate an HTML document that walks a reviewer through the branch's changes so they can quickly get up to speed on a PR with little prior context. Open the document in the browser when done.

## Process

1. Gather context:
   - `git merge-base HEAD main` to find the divergence point.
   - `git log --oneline <merge-base>..HEAD` for commit messages.
   - `git diff --stat <merge-base>..HEAD` for the list of changed files.
   - `git diff <merge-base>..HEAD` for the full diff.
   - Read relevant source files as needed to understand intent and surrounding context.

2. Organize the changes into logical sections. A section is a coherent unit of work: a new feature, a refactor, a bug fix, a config change, etc. Group related files together. Do not just list files one by one.

3. Build an HTML document. Requirements:
   - **Light color scheme**: light background, dark text.
   - **Hero/summary section at the top**: one paragraph explaining what the branch does and why, written for someone unfamiliar with the codebase. Include the branch name and commit count.
   - **Table of contents** linking to each section.
   - **One section per logical group** of changes. Each section has:
     - A heading and a 2-4 sentence explanation of what changed and why.
     - The relevant diff rendered with syntax highlighting (use `<pre><code>` blocks, color added lines green `#e6ffed`, removed lines red `#ffeef0`, hunk headers gray).
     - Any diagrams, flowcharts, or ASCII art that clarify structure, data flow, or relationships — use inline SVG or a `<canvas>`-based approach when helpful.
   - **Risk / review callouts**: a highlighted box at the bottom (or inline where relevant) flagging anything subtle, risky, or that deserves extra reviewer attention.
   - Self-contained single file: no external CDN dependencies.

4. Write the HTML file to a temp path (e.g. `/tmp/walkthrough-<branch-name>.html`).

5. Open it in the browser: `open /tmp/walkthrough-<branch-name>.html`.

6. Report the file path to the user and offer to regenerate if they want changes.

## Notes

- Prioritize clarity for someone unfamiliar with the project. Assume they can read code but don't know the repo.
- Infer intent from commit messages, surrounding code, and naming. Quote commit messages when they explain the why.
- If a change is purely mechanical (rename, reformat), say so briefly and move on.
- Read full source files when the diff alone doesn't reveal why a change matters.
