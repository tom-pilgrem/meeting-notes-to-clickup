# meeting-notes-to-clickup
Project to build an AI solution to write meeting notes to click up tasks

See [CLAUDE.md](CLAUDE.md) for the full pipeline design, config values, and rules.

## Setup

1. `pip install -r requirements.txt`
2. Create a Google service account (Google Cloud Console → IAM & Admin → Service Accounts), enable the Drive API on that project, and download a JSON key for the service account.
3. Share the watched Drive folder with the service account's email address (`...@...iam.gserviceaccount.com`, found in the key file), with Viewer access — a service account has no Drive of its own, so without this it can't see the folder.
4. Copy `.env.example` to `.env` and fill in:
   - `ANTHROPIC_API_KEY`
   - `CLICKUP_API_TOKEN` (personal API token, or an OAuth token, with access to the target list)
   - `GOOGLE_SERVICE_ACCOUNT_FILE` — path to the service account JSON key from step 2
5. Run `python main.py`. No browser consent step — the service account authenticates directly.

## Running it again

Re-running `python main.py` only processes docs that are new or have changed `modifiedTime` since the last run — tracked in `state.json`. If an extraction is flagged (e.g. a possible duplicate, or an ambiguous owner), the ClickUp task(s) still get created, but with the flag type and explanation prepended to the task description — so review happens directly in ClickUp rather than by re-reading `run_log.jsonl`.

