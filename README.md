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

## Cloud scheduling (GitHub Actions)

The pipeline runs on a schedule via [`.github/workflows/run-pipeline.yml`](.github/workflows/run-pipeline.yml) — hourly, 9am-5pm weekdays (Australia/Sydney time, DST-aware), with a manual trigger available too. It runs on GitHub's own infrastructure, not your laptop.

**One-time setup, in the GitHub repo (Settings → Secrets and variables → Actions → New repository secret):**

| Secret name | Value |
|---|---|
| `ANTHROPIC_API_KEY` | Same value as in your local `.env` |
| `CLICKUP_API_TOKEN` | Same value as in your local `.env` |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | The **full contents** of your `service-account.json` file (paste the whole JSON, not a path) |

**Important — seed `state.json` before the first scheduled run.** `state.json` and `run_log.jsonl` are tracked files, not gitignored: the workflow commits them back to the repo after every run, since GitHub Actions runners are ephemeral and have nowhere else to persist state between runs. If you've already run the pipeline locally, your existing `state.json` has real processing history in it — commit and push that file (`git add state.json run_log.jsonl && git commit -m "Seed pipeline state" && git push`) **before** the schedule takes effect. Otherwise the first cloud run will think every doc is new and recreate ClickUp tasks that already exist.

To test the workflow without waiting for the next hour, use the "Run workflow" button on the Actions tab (or `gh workflow run run-pipeline.yml` if you have the GitHub CLI).

If you'd also set up the Windows Task Scheduler entry from before, unregister it (`Unregister-ScheduledTask -TaskName "MeetingNotesToClickUp"`) so you're not running the pipeline from two places at once.

