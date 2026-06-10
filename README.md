# bsamek/skills

A marketplace containing a single `bsamek` plugin with seven skills. Install with:

```
/plugin marketplace add bsamek/skills
/plugin install bsamek@skills
```

Skills are invoked as `bsamek:<skill>` (e.g. `bsamek:preflight`).

## Skills

### delegated-plan-execution

Orchestrate Plan-mode execution by delegating each step to a Sonnet implementer, then to fresh Sonnet spec-compliance and code-quality validators. One fix pass on failure, then escalates to the orchestrator.

### inbox

Process a GTD inbox in the Things app. Note: this skill is tailored to Brian's personal Things setup and is included as a worked example rather than a general-purpose tool.

### pr-comments

Review the comments on the current branch's PR and evaluate whether each should be addressed, with reasoning. Read-only: it advises, it does not change code.

### preflight

Dispatch parallel Opus and OpenCode reviews of a branch before opening a pull request. Surfaces issues early without blocking the author.

### readwise-reader-workflow

Read Readwise Reader with Brian: triage oldest-saved Inbox or Feed items, fetch the next oldest-saved Later item, and summarize Later articles.

### walkthrough

Generate a self-contained HTML document that walks a reviewer through the branch's changes, organized into logical sections with rendered diffs and risk callouts, then open it in the browser. Use before opening a PR.

### worktree

Create a git worktree and branch for a Jira ticket in one step. Looks up the ticket, derives a short slug from the summary, creates the worktree, and changes into it. Note: this skill assumes Brian's `jira` CLI setup and `.claude/worktrees/` layout.

## License

MIT. See [LICENSE](LICENSE).
