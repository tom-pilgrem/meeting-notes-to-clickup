"""Config constants for the meeting-notes-to-clickup pipeline. See CLAUDE.md."""

import os

from dotenv import load_dotenv

load_dotenv()

GOOGLE_DRIVE_FOLDER_ID = "1-BfMpi5B6MYrUg1muwF7VsXioBwdFkzr"
CLICKUP_TEAM_ID = "9016358257"
CLICKUP_LIST_ID = "901616291856"
EXTRACTION_MODEL = "claude-haiku-4-5"

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
CLICKUP_API_TOKEN = os.environ.get("CLICKUP_API_TOKEN")
GOOGLE_OAUTH_CLIENT_SECRETS_FILE = os.environ.get(
    "GOOGLE_OAUTH_CLIENT_SECRETS_FILE", "./client_secret.json"
)
GOOGLE_OAUTH_TOKEN_FILE = os.environ.get("GOOGLE_OAUTH_TOKEN_FILE", "./token.json")

STATE_FILE = "state.json"
RUN_LOG_FILE = "run_log.jsonl"

CLICKUP_PRIORITY = {
    "urgent": 1,
    "high": 2,
    "normal": 3,
    "low": 4,
}
