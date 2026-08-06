"""Local JSON state file tracking which Drive docs have been processed.

Maps doc_id -> {last_processed_at, modifiedTime, created_task_ids}.
"""

import json
import os
from datetime import datetime, timezone

from config import STATE_FILE


def load_state() -> dict:
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state: dict) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def is_processed(state: dict, doc_id: str, modified_time: str) -> bool:
    """A doc counts as processed only if it's been seen at its current modifiedTime."""
    entry = state.get(doc_id)
    return bool(entry) and entry.get("modifiedTime") == modified_time


def mark_processed(
    state: dict, doc_id: str, modified_time: str, created_task_ids: list[str]
) -> None:
    state[doc_id] = {
        "last_processed_at": datetime.now(timezone.utc).isoformat(),
        "modifiedTime": modified_time,
        "created_task_ids": created_task_ids,
    }
