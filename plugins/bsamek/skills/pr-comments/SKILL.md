---
name: pr-comments
description: Review the comments on the current branch's PR and evaluate whether each should be addressed, without making any changes. Use when the user invokes /pr-comments or asks for an evaluation of PR feedback.
---

# PR Comments

## Overview

Read the review comments on the current branch's pull request and give the user a reasoned evaluation of each: whether it should be addressed, and why. This is read-only. Do not edit code, push commits, or reply to comments unless the user explicitly asks afterward.

## Process

1. Find the PR for the current branch and gather its comments:
   - `gh pr view --json number,title,url` to confirm the PR.
   - Inline review comments (code-anchored):
     `gh api repos/{owner}/{repo}/pulls/{number}/comments --paginate`
   - Review summaries (approve/request-changes bodies):
     `gh api repos/{owner}/{repo}/pulls/{number}/reviews --paginate`
   - Top-level conversation comments:
     `gh api repos/{owner}/{repo}/issues/{number}/comments --paginate`

   `gh pr view --json url` gives owner/repo/number, or let `gh` infer the repo. Skip empty bodies and your own prior automated comments. Group threaded replies together.

2. For each substantive comment, read the code it refers to (use the `path` and `line`/`diff_hunk` fields on inline comments) so the evaluation is grounded in the actual change, not just the comment text.

3. Produce an evaluation. For each comment give:
   - A short quote or paraphrase of the comment, with `file:line` and the commenter.
   - Your recommendation: **Address**, **Consider**, or **Skip**.
   - One to three sentences of reasoning: is it correct, does it matter, what would addressing it cost or risk.

4. Close with a brief summary: which comments you'd act on first, and any that conflict with each other or with the PR's intent.

## Notes

- Evaluate, don't implement. The whole point is a decision aid before touching code.
- Be willing to disagree with a comment. If a reviewer is wrong or the suggestion is out of scope, say so and explain why.
- Distinguish blocking correctness issues from style or preference. Weight them accordingly in the summary.
- If there are no comments, say so plainly rather than inventing feedback.
