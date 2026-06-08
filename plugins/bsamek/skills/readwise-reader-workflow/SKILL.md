---
name: readwise-reader-workflow
description: Use when reading Readwise Reader with Brian: triage oldest-saved Inbox or Feed items, get the next oldest-saved Later item, or read and summarize an article from Later using the Readwise CLI.
---

# Readwise Reader Workflow

Use the `readwise` CLI for Reader workflows. When the user asks for the next
item in Inbox, Later, or Feeds in this workflow, sort by `saved_at` ascending
oldest first unless they explicitly ask for another ordering.

Do not use API/default order directly: `reader-list-documents` returns most
recently added first.

If the CLI reports `fetch failed`, rerun the same command with network
escalation.

## Metadata Fields

Always include:

- Title
- Author
- Saved date
- Readwise summary
- Reading time
- Word count
- Reader URL

Useful extra metadata to mention when available or relevant:

- `site_name`
- `category`
- `source_url`
- `published_date`
- `tags`
- `listening_time` for videos, podcasts, or audio when `reading_time` is null

Format dates for Brian in `America/New_York` unless the user asks otherwise.

## Fetch Oldest Saved Items

Use a generous limit so the oldest saved item is present locally before sorting.
If the queue may be larger than the limit and exact oldest matters, paginate with
`--page-cursor` until exhausted, then sort all fetched results by `saved_at`.

Shared response fields:

```bash
id,title,author,url,source_url,site_name,category,tags,word_count,reading_time,listening_time,saved_at,published_date,summary,location,first_opened_at
```

### Inbox

For "next N articles in inbox", default N to 1. Reader calls Inbox `new`.

```bash
readwise --json reader-list-documents \
  --location new \
  --limit 1000 \
  --response-fields id,title,author,url,source_url,site_name,category,tags,word_count,reading_time,listening_time,saved_at,published_date,summary,location,first_opened_at
```

Then select `.results | sort_by(.saved_at) | .[:N]`.

After presenting each item, wait for Brian to choose:

- Move to Later:
  ```bash
  readwise reader-move-documents --document-ids <id> --location later
  ```
- Move to Archive:
  ```bash
  readwise reader-move-documents --document-ids <id> --location archive
  ```

### Later

For "next article in Later", return the single oldest saved Later item.

```bash
readwise --json reader-list-documents \
  --location later \
  --limit 1000 \
  --response-fields id,title,author,url,source_url,site_name,category,tags,word_count,reading_time,listening_time,saved_at,published_date,summary,location,first_opened_at
```

Then select `.results | sort_by(.saved_at) | .[0]`.

Important: another local skill may define "oldest Later" as oldest
`last_moved_at`. For this workflow, use `saved_at` unless Brian explicitly asks
for oldest moved to Later.

### Feeds

For "next N articles in Feeds", default N to 1 and sort by `saved_at` ascending.
Feeds are a mark-read workflow, not an archive workflow. Prefer unseen feed
items unless Brian asks otherwise.

```bash
readwise --json reader-list-documents \
  --location feed \
  --seen false \
  --limit 1000 \
  --response-fields id,title,author,url,source_url,site_name,category,tags,word_count,reading_time,listening_time,saved_at,published_date,summary,location,first_opened_at
```

Then select `.results | sort_by(.saved_at) | .[:N]`.

After presenting each item, wait for Brian to choose:

- Move to Later:
  ```bash
  readwise reader-move-documents --document-ids <id> --location later
  ```
- Mark read:
  ```bash
  readwise reader-bulk-edit-document-metadata --documents '[{"document_id":"<id>","seen":true}]'
  ```

## Read and Summarize a Later Article

When Brian asks to read and summarize an article from Later:

1. Identify the target article. If none is named, use the oldest saved Later
   item.
2. Fetch details:
   ```bash
   readwise --json reader-get-document-details --document-id <id>
   ```
3. Write a fuller summary than the Reader metadata summary. Scale the summary
   to the article:
   - Short article: a concise paragraph plus any key takeaway.
   - Medium article: a few tight bullets or short paragraphs.
   - Long article: a structured summary with thesis, main points, caveats, and
     what seems worth remembering.

Do not dump the full article text. Quote sparingly, only when a short phrase is
needed for precision.

## Output Style

For queue items, use a compact repeated block:

```text
Title:
Author:
Saved:
Summary:
Reading time:
Word count:
Reader URL:
Useful metadata:
```

For triage flows, ask for the user's decision after the item list and then apply
the requested move or mark-read action before continuing.
