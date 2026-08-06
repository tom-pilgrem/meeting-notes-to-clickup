"""ClickUp task creation: map extracted action items to ClickUp tasks.

See CLAUDE.md "Field Mapping" and "Assignee resolution" sections.
"""

from datetime import datetime, timezone

import requests

from config import (
    CLICKUP_API_TOKEN,
    CLICKUP_FLAG_TYPE_FIELD_ID,
    CLICKUP_LIST_ID,
    CLICKUP_PRIORITY,
    CLICKUP_TEAM_ID,
)

API_BASE = "https://api.clickup.com/api/v2"

_member_cache: list[dict] | None = None


def _headers() -> dict:
    return {"Authorization": CLICKUP_API_TOKEN, "Content-Type": "application/json"}


def get_workspace_members() -> list[dict]:
    """Fetch and cache the workspace member list for the configured team.

    Returns [{id, username, email}, ...]. Cached for the lifetime of the process
    so assignee resolution doesn't hit the API once per task.
    """
    global _member_cache
    if _member_cache is not None:
        return _member_cache

    response = requests.get(f"{API_BASE}/team", headers=_headers())
    response.raise_for_status()
    teams = response.json().get("teams", [])

    team = next((t for t in teams if t.get("id") == CLICKUP_TEAM_ID), None)
    if team is None:
        raise RuntimeError(
            f"ClickUp team {CLICKUP_TEAM_ID} not found among authorized teams "
            f"for this API token"
        )

    _member_cache = [
        {
            "id": m["user"]["id"],
            "username": m["user"].get("username", ""),
            "email": m["user"].get("email", ""),
        }
        for m in team.get("members", [])
    ]
    return _member_cache


def resolve_assignee(name: str) -> int | None:
    """Resolve an extracted assignee name to a ClickUp user ID.

    Never guesses from a partial match — an exact (case-insensitive) match on
    username or the local part of an email is required, otherwise returns None
    so the task is left unassigned rather than misassigned (see CLAUDE.md Rule 3).
    """
    if not name or name.strip().lower() == "unassigned":
        return None

    needle = name.strip().lower()
    for member in get_workspace_members():
        if member["username"].strip().lower() == needle:
            return member["id"]
        email_local = member["email"].split("@")[0].strip().lower()
        if email_local == needle:
            return member["id"]
    return None


def _due_date_to_ms(due_date: str | None) -> int | None:
    if not due_date:
        return None
    dt = datetime.strptime(due_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def create_task(
    item: dict, flag_type: str | None = None, list_id: str = CLICKUP_LIST_ID
) -> dict:
    """Create a single ClickUp task from one extracted action item.

    `item` is one entry from the extraction's action_items array:
    {title, assignee, due_date?, priority, description?}

    `flag_type` is the extraction's flag_type (e.g. "possible_duplicate"),
    passed only when the source extraction was flagged. Written into the
    list's "Flag Type" custom field so flagged tasks can be filtered/sorted
    on in ClickUp views, in addition to the note in the task description.
    """
    payload: dict = {
        "name": item["title"],
        "priority": CLICKUP_PRIORITY[item["priority"]],
    }
    if item.get("description"):
        payload["description"] = item["description"]

    assignee_id = resolve_assignee(item.get("assignee", ""))
    if assignee_id is not None:
        payload["assignees"] = [assignee_id]

    due_date_ms = _due_date_to_ms(item.get("due_date"))
    if due_date_ms is not None:
        payload["due_date"] = due_date_ms

    if flag_type:
        payload["custom_fields"] = [
            {"id": CLICKUP_FLAG_TYPE_FIELD_ID, "value": flag_type}
        ]

    response = requests.post(
        f"{API_BASE}/list/{list_id}/task", headers=_headers(), json=payload
    )
    response.raise_for_status()
    return response.json()
