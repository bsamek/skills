# bsamek/skills

A marketplace of Claude Code skills. Install the whole marketplace with:

```
/plugin marketplace add bsamek/skills
```

Then install individual skills with:

```
/plugin install <name>@bsamek-skills
```

## Skills

### delegated-plan-execution

Orchestrate Plan-mode execution by delegating each step to a Sonnet implementer, then to a fresh Sonnet validator. One fix pass on failure, then escalates to the orchestrator.

### inbox

Process a GTD inbox in the Things app. Note: this skill is tailored to Brian's personal Things setup and is included as a worked example rather than a general-purpose tool.

### preflight

Dispatch parallel Opus and OpenCode reviews of a branch before opening a pull request. Surfaces issues early without blocking the author.

### walkthrough

Walk through a branch's diff chunk by chunk for self-review. Use before opening a PR to catch issues that automated checks miss.

## License

MIT. See [LICENSE](LICENSE).
