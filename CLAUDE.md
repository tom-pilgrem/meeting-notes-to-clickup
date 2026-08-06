# CLAUDE.md -- meeting-notes-to-clickup

This file tells Claude Code how to work in this repo. The project turns
meeting notes stored as Google Docs into ClickUp action-item tasks, using a
Claude Haiku extraction call with a pre-tested prompt and tool schema.

---

## What This Project Does

1. Watch a specific Google Drive folder for meeting note docs.
2. For each new/unprocessed doc, pull the text content.
3. Call the Claude API (model: Haiku) with a fixed prompt + forced tool call
   (`create_action_items`) to extract structured action items.
4. Map extracted fields to ClickUp task fields (assignee, due date, priority).
5. Create tasks in a specific ClickUp list. If the extraction was flagged for
   human review, still create the task(s), but prepend the flag_type and
   flags explanation to each task's description so the assignee sees it and
   reviews in ClickUp rather than the task silently vanishing into a log.
6. Track which docs have already been processed so re-runs don't duplicate
   tasks.

This is a small, single-purpose automation, not a general analytics project.
Favor a simple, readable script over frameworks or abstractions.

---

## Config / IDs

| What | Value |
|------|-------|
| Google Drive folder | `1-BfMpi5B6MYrUg1muwF7VsXioBwdFkzr` (https://drive.google.com/drive/u/1/folders/1-BfMpi5B6MYrUg1muwF7VsXioBwdFkzr) |
| ClickUp workspace/team ID | `9016358257` |
| ClickUp target list ID | `901616291856` (https://app.clickup.com/9016358257/v/l/li/901616291856) |
| Extraction model | `claude-haiku-4-5` (see model IDs in [claude-api skill](../.claude/skills) if the exact ID needs confirming at build time) |

Secrets (Anthropic API key, Google credentials, ClickUp API token) belong in
environment variables / a local `.env` that is **gitignored** -- never commit
credentials to this repo.

---

## Extraction Prompt (proven -- do not rewrite without reason)

```
Extract action items from this meeting note. For each item, identify the task, who owns it, any due date, and priority.

Rules:
- If no owner is stated, set assignee to "unassigned"
- If no due date is stated, omit due_date
- If the note contains no actionable items, return an empty action_items array and explain why in the flags field
- If the note appears to duplicate an earlier one (same title, same date, near-identical content), flag it in the flags field rather than guessing
- Priority defaults to "normal" unless urgency is explicit
- Only set priority to "urgent" or "high" if the note contains explicit urgency language (e.g. "urgent", "ASAP", "critical", a tight deadline). Otherwise use "normal".
- Always respond by calling the create_action_items tool
- Set flag_type to "none" unless something needs human review, otherwise choose the closest of: possible_duplicate, no_action_items, ambiguous_owner, other

Meeting note:
{{Google_Doc_Text_Content}}
```

Substitute `{{Google_Doc_Text_Content}}` with the raw text of the Google Doc.

### Tool schema: `create_action_items`

```json
{
  "action_items": {
    "type": "array",
    "items": {
      "type": "object",
      "properties": {
        "title": {
          "type": "string",
          "description": "Short task title, imperative form, e.g. 'Send Q3 report to finance'"
        },
        "assignee": {
          "type": "string",
          "description": "Name of the person responsible, or 'unassigned' if not stated in the note"
        },
        "due_date": {
          "type": "string",
          "description": "ISO 8601 date (YYYY-MM-DD) if mentioned in the note"
        },
        "priority": {
          "type": "string",
          "enum": ["urgent", "high", "normal", "low"]
        },
        "description": {
          "type": "string",
          "description": "One or two sentences of context for the task"
        }
      },
      "required": ["title", "assignee", "priority"]
    }
  },
  "flag_type": {
    "type": "string",
    "enum": ["none", "possible_duplicate", "no_action_items", "ambiguous_owner", "other"],
    "description": "Category of concern with this extraction, if any. Use 'none' if nothing needs review."
  },
  "flags": {
    "type": "string",
    "description": "Human-readable explanation of the concern. Empty string if flag_type is 'none'."
  }
}
```

Call the API with `tool_choice` forced to `create_action_items` (as already
validated in the Anthropic Console workbench) so the response is always
structured -- never parse free text for this step.

---

## Field Mapping: extraction -> ClickUp task

| Extracted field | ClickUp field | Notes |
|---|---|---|
| `title` | task `name` | direct |
| `description` | task `description` | direct |
| `assignee` | `assignees` (user ID array) | resolve name -> ClickUp user ID first (see below); if unresolved or `"unassigned"`, leave assignees empty rather than guessing |
| `due_date` (ISO date) | `due_date` (Unix ms epoch) | convert; omit the field entirely if not present in extraction |
| `priority` | ClickUp numeric priority | `urgent`→1, `high`→2, `normal`→3, `low`→4 |
| `flag_type` (when != "none") | "Flag Type" custom field (`d74548fd-763e-408c-b488-fc45a0759cd7`, short_text, list `901616291856`) | write the flag_type string directly; omit the custom field entirely for unflagged tasks |

**Assignee resolution:** ClickUp needs a user ID, not a name. Look up the
extracted name against the workspace member list once per run (cache it,
don't call the API per-task). If no confident match, leave the task
unassigned and note it in the run log -- do not silently assign the wrong
person.

**Flagged extractions (`flag_type != "none"`):** still create the ClickUp
task(s) -- do not skip creation. Prepend a review note (the flag_type and the
flags explanation) to each task's description, so the flag is visible to the
assignee directly in ClickUp rather than only in a log file. Also write the
flag_type into the "Flag Type" custom field on the task, so flagged tasks can
be filtered/sorted on in ClickUp views without opening each one. If the
extraction returned no action items (e.g. `flag_type: "no_action_items"`),
create a single fallback task for the doc (title referencing the doc name)
carrying the flag note, so a flagged doc never disappears without producing
anything to review. Also log the doc, flag_type, and flags explanation to the
run log for traceability. This is a human-in-the-loop review mechanism, not
an error case to swallow -- the review now happens via the created task(s)
rather than by re-running the pipeline.

---

## Dedup / State Tracking

Before processing, check which Drive docs have already been handled (by doc
ID, and ideally the doc's `modifiedTime` so an edited note can be
reprocessed deliberately). A simple local JSON/SQLite state file mapping
`doc_id -> {last_processed_at, modifiedTime, created_task_ids}` is enough for
this project's scale -- don't reach for a database service.

`state.json` and `run_log.jsonl` are tracked in git, not gitignored (see
"Cloud Scheduling" below) -- this is intentional, not an accident. Never
add them back to `.gitignore`.

---

## Cloud Scheduling

The pipeline runs on a schedule via GitHub Actions
(`.github/workflows/run-pipeline.yml`), not on anyone's laptop or a
third-party cloud service (AWS Lambda, Fabric, and Databricks were
considered and rejected as overkill for a script this small that already
lives in this repo).

**Why `state.json` and `run_log.jsonl` are committed back to the repo:**
GitHub Actions runners are ephemeral -- a fresh VM per run, nothing persists
on disk between runs. The workflow commits both files back to the repo
after every run so the dedup logic keeps working across runs. If you ever
change the persistence mechanism (e.g. move to S3, a database, etc.),
update this section and the workflow together -- don't let them drift.

**Schedule:** hourly, 9am-5pm, Monday-Friday, Australia/Sydney time
(business hours for this org). Cron itself is UTC-only and can't follow
daylight saving, so the business-hours window is enforced at runtime inside
the workflow (a `check` job compares the actual Sydney local time), not
baked into the cron expression. If the business hours or timezone ever
change, update the `check` job's shell logic in the workflow file, not a
cron string.

**Manual runs** (`workflow_dispatch`) always execute regardless of time --
the business-hours gate only applies to `schedule`-triggered runs. This is
deliberate, so the pipeline can be triggered on demand for testing without
fighting the time gate.

---

## Suggested Build Approach

A small Python script (Anthropic SDK + Google Drive API client + ClickUp
REST API), runnable on demand and scheduled via GitHub Actions (see "Cloud
Scheduling" below). Confirm with the user before making a significant
change to this shape if it doesn't match what they have in mind.

While developing/testing in this Claude Code session, Drive and ClickUp
connectors may already be available as MCP tools -- fine to use them for
manual testing and one-off task creation, but the production path should
still call the Anthropic Messages API directly with the fixed Haiku prompt
above so the extraction step is reproducible outside a Claude Code session.

---

## Rules

1. Never modify the extraction prompt or tool schema without the user's
   explicit sign-off -- it's already been tested and tuned.
2. For a flagged extraction, still create the ClickUp task(s), but always
   prepend the flag_type and flags explanation to the task description --
   never create a flagged task that looks identical to an unflagged one.
3. Never guess an assignee ClickUp ID from a partial name match -- prefer
   leaving unassigned over misassigning.
4. Keep credentials out of the repo (env vars only, `.gitignore`d).
5. Log every run (docs seen, tasks created, tasks flagged/skipped) so
   failures are traceable without re-reading Drive/ClickUp state by hand.
