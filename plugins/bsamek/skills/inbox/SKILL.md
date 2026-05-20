---
name: inbox
description: Use when the user invokes /inbox to process their GTD inbox in Things.
---

Process the user's GTD inbox items, deciding where each item belongs in Things.

> **Setup note**: This skill assumes Things 3 (via an MCP server exposing `get_inbox`, `get_projects`, `add_project`, `update_todo`) and an Obsidian vault rooted at `~/obsidian/` with `projects/`, `notes/`, and `areas/` subfolders. Adjust the paths in step 3 to match your own vault layout.

## Step 1: Gather inbox items

Run in parallel:
1. **Things inbox**: Call `get_inbox` to get all Things inbox items.
2. **Things projects**: Call `get_projects` to know what projects exist for routing tasks.

## Step 2: Present and triage each item

For each inbox item, present it to the user one at a time and ask where it belongs:

```
Item: <title>
Notes: <notes if any>

Where does this go?
  [p] New project
  [t] Task → which project? (or "no project")
  [w] Waiting for
  [s] Someday/maybe
  [r] Reference (Obsidian note only)
  [d] Delete/not actionable
```

Wait for the user's choice before moving to the next item. Accept abbreviated input (just "t", "p mongodb", etc.).

For tasks routed to an existing project, show a numbered list of current projects so the user can pick by number.

## Step 3: Execute each decision

After the user chooses, immediately perform the update before presenting the next item.

### New project
1. **Things**: Create a new project with `add_project`. Ask for the project name if not given.
2. **Obsidian**: Create `~/obsidian/projects/<ProjectName>.md` with the two-part structure (compiled truth above `---`, Timeline below). Add a dated timeline entry: "Created from inbox item: <title>".
3. Move the original task into the new project in Things, or delete it if it was just a project placeholder.

### Task (no project or existing project)
1. **Things**: Use `update_todo` to move the item out of Inbox. Set the project if applicable; set list to "Anytime".

### Waiting for
1. **Things**: Move to appropriate project or area, tag as "waiting", and note the date and who/what you're waiting on in the task notes.

### Someday/maybe
1. **Things**: Use `update_todo` to set the schedule to "Someday".

### Reference
1. **Things**: Delete the item (it's not actionable).
2. **Obsidian**: Add to the appropriate note in `~/obsidian/notes/` or `~/obsidian/areas/`.

### Delete
1. **Things**: Delete the item.

## Step 4: Confirm completion

After all items are processed, print a short summary:
```
Inbox processed: X items
  Projects created: N
  Tasks routed: N
  Waiting for: N
  Someday/maybe: N
  Deleted/reference: N
```

## Style rules

- Do not prefix Slack channel names with `#` in Obsidian (use `general`, not `#general`).
