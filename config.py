"""Config constants for the meeting-notes-to-clickup pipeline. See CLAUDE.md."""

import os

from dotenv import load_dotenv

load_dotenv()

GOOGLE_DRIVE_FOLDER_ID = "1-BfMpi5B6MYrUg1muwF7VsXioBwdFkzr"
CLICKUP_TEAM_ID = "9016358257"
CLICKUP_LIST_ID = "901616291856"
CLICKUP_FLAG_TYPE_FIELD_ID = "d74548fd-763e-408c-b488-fc45a0759cd7"
EXTRACTION_MODEL = "claude-haiku-4-5"

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
CLICKUP_API_TOKEN = os.environ.get("CLICKUP_API_TOKEN")
GOOGLE_SERVICE_ACCOUNT_FILE = os.environ.get(
    "GOOGLE_SERVICE_ACCOUNT_FILE", "./service-account.json"
)

STATE_FILE = "state.json"
RUN_LOG_FILE = "run_log.jsonl"

CLICKUP_PRIORITY = {
    "urgent": 1,
    "high": 2,
    "normal": 3,
    "low": 4,
}
