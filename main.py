"""Entry point: watch the Drive folder, extract action items, create ClickUp tasks.

Run on demand: `python main.py`. See CLAUDE.md for the full pipeline description.
"""

import json
from datetime import datetime, timezone

import clickup
import drive
import extract
from config import RUN_LOG_FILE
from state import is_processed, load_state, mark_processed, save_state


def _log(entry: dict) -> None:
    entry["timestamp"] = datetime.now(timezone.utc).isoformat()
    with open(RUN_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def process_doc(doc: dict, state: dict) -> None:
    doc_id = doc["id"]
    doc_name = doc["name"]
    modified_time = doc["modifiedTime"]

    doc_text = drive.get_doc_text(doc_id)
    extraction = extract.extract_action_items(doc_text)

    if extraction["flag_type"] != "none":
        _log(
            {
                "event": "flagged",
                "doc_id": doc_id,
                "doc_name": doc_name,
                "flag_type": extraction["flag_type"],
                "flags": extraction["flags"],
            }
        )
        print(f"[FLAGGED] {doc_name}: {extraction['flag_type']} — {extraction['flags']}")
        # Deliberately not marking as processed: a flagged doc should be
        # re-evaluated after human review, not silently skipped forever.
        return

    created_task_ids = []
    for item in extraction["action_items"]:
        task = clickup.create_task(item)
        created_task_ids.append(task["id"])
        _log(
            {
                "event": "task_created",
                "doc_id": doc_id,
                "doc_name": doc_name,
                "task_id": task["id"],
                "title": item["title"],
            }
        )
        print(f"[CREATED] {doc_name}: {item['title']} -> task {task['id']}")

    mark_processed(state, doc_id, modified_time, created_task_ids)

    if not created_task_ids:
        _log({"event": "no_action_items", "doc_id": doc_id, "doc_name": doc_name})
        print(f"[NO ACTION ITEMS] {doc_name}")


def run() -> None:
    state = load_state()
    docs = drive.list_docs()
    _log({"event": "run_start", "docs_seen": len(docs)})

    for doc in docs:
        if is_processed(state, doc["id"], doc["modifiedTime"]):
            continue
        try:
            process_doc(doc, state)
        except Exception as e:
            _log(
                {
                    "event": "error",
                    "doc_id": doc["id"],
                    "doc_name": doc["name"],
                    "error": str(e),
                }
            )
            print(f"[ERROR] {doc['name']}: {e}")
        finally:
            save_state(state)

    _log({"event": "run_end"})


if __name__ == "__main__":
    run()
