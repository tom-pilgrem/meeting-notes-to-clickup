# meeting-notes-to-clickup
Project to build an AI solution to write meeting notes to click up tasks

See [CLAUDE.md](CLAUDE.md) for the full pipeline design, config values, and rules.

## Setup

1. `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and fill in:
   - `ANTHROPIC_API_KEY`
   - `CLICKUP_API_TOKEN` (personal API token, or an OAuth token, with access to the target list)
   - `GOOGLE_OAUTH_CLIENT_SECRETS_FILE` — path to an OAuth client secrets JSON (Desktop app credential type) downloaded from Google Cloud Console, with the Drive API enabled
3. Run `python main.py`. The first run opens a browser for Google OAuth consent; a `token.json` is cached afterward and refreshed automatically.

## Running it again

Re-running `python main.py` only processes docs that are new or have changed `modifiedTime` since the last run — tracked in `state.json`. Flagged extractions (see `run_log.jsonl`) are deliberately left unprocessed so they get re-evaluated after human review rather than silently skipped.

