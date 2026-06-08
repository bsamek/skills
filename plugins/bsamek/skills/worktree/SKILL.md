---
name: worktree
description: Create a git worktree for a Jira ticket. Looks up the ticket, derives a short branch name, creates the worktree and branch, then changes to the worktree directory. Invoke with /worktree <TICKET-KEY>.
---

# Worktree

Creates a git worktree for a Jira ticket in one step.

## When to Use

Use `/worktree <TICKET-KEY>` when starting work on a new ticket. The skill will:

1. Fetch the ticket summary from Jira.
2. Derive a short, lowercase, hyphenated slug from the summary (4–5 words max).
3. Construct the full name: `<TICKET-KEY>-<slug>` (e.g. `DEVPROD-1234-fix-agent-status`).
4. Create a git worktree + branch at `.claude/worktrees/<full-name>` inside the current repo.
5. Change the working directory to the new worktree.
6. Output a `/rename <slug>` line so the session can be renamed to the short name.

## Steps

### 1. Look up the ticket

```bash
jira issue view -p <PROJECT> <TICKET-KEY>
```

Read the **Summary** field. Ignore the rest for now.

### 2. Derive the short name

From the summary, extract 3–5 meaningful lowercase words and join them with hyphens. Drop stop words (a, an, the, to, for, in, of, and, or). Keep it under 40 characters total. For example:

- "Refactor agent status reporting" → `refactor-agent-status`
- "Fix BV path filtering for MQ versions" → `fix-bv-path-filtering`

Full branch name: `<TICKET-KEY>-<slug>` (e.g. `DEVPROD-33316-refactor-agent-status`).

### 3. Create the worktree

```bash
git worktree add .claude/worktrees/<full-name> -b <full-name>
```

Run from the repo root (the primary working directory, not an existing worktree).

### 4. Change to the worktree

```bash
cd .claude/worktrees/<full-name>
```

Report the full path to the user so they can open it in their editor.

### 5. Suggest the session rename

A skill cannot rename the session itself (`/rename` is only recognized when the user types it at the start of a message). Instead, end your output by emitting the rename command for the user to copy.

Put the command on its **own line by itself**, with no surrounding text on that line, so the user can double-click the line to select and copy it:

```
/rename <slug>
```

Use the **slug only** (e.g. `fix-agent-status`), not the full `<TICKET-KEY>-<slug>` name. Any explanatory text goes on separate lines before or after, never inline with the command.

## Notes

- Worktrees live at `<repo-root>/.claude/worktrees/<full-name>`.
- The branch name and directory name are always identical.
- If the branch already exists, omit `-b` and use `git worktree add .claude/worktrees/<full-name> <full-name>`.
- After switching, confirm the working directory with `pwd` and `git branch --show-current`.
