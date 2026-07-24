#!/usr/bin/env python3
"""Merge paginated ClickUp task exports (data/tasks_page*.json) into data/tasks_karol.json.

Used only during a manual refresh: after re-fetching pages from the ClickUp MCP
`clickup_filter_tasks` tool and saving each page as data/tasks_page0.json,
data/tasks_page1.json, ..., run this to dedupe by task id and produce the single
tasks_karol.json consumed by build_dashboard.py.
"""
import json
import sys
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def main():
    pages = sorted(DATA_DIR.glob("tasks_page*.json"))
    if not pages:
        sys.exit("No data/tasks_page*.json files found.")

    by_id = {}
    for page in pages:
        payload = json.loads(page.read_text())
        for task in payload["tasks"]:
            existing = by_id.get(task["id"])
            if existing is None or (existing.get("due_date") is None and task.get("due_date") is not None):
                by_id[task["id"]] = task

    tasks = sorted(by_id.values(), key=lambda t: (t["due_date"] is None, t["due_date"] or "0"))
    out = DATA_DIR / "tasks_karol.json"
    out.write_text(json.dumps({"tasks": tasks}, ensure_ascii=False, indent=2) + "\n")
    print(f"Wrote {len(tasks)} tasks to {out}")


if __name__ == "__main__":
    main()
