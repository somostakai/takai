#!/usr/bin/env python3
"""Build index.html from data/events_raw.json and data/tasks_karol.json.

Run this after refreshing the two data files (via the ClickUp / Google Calendar
MCP tools) to regenerate the static dashboard. See README.md for the full
refresh workflow.
"""
import json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
TZ = ZoneInfo("America/Sao_Paulo")

ROUTINE_TITLES = {
    "creative day",
    "focus day",
    "🫕 almoço e descanso",
    "☕️ café da tarde",
}

OWNER_EMAIL = "takai@somostakai.com.br"

WEEKDAYS_PT = [
    "segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
    "sexta-feira", "sábado", "domingo",
]
MONTHS_PT = [
    "jan", "fev", "mar", "abr", "mai", "jun",
    "jul", "ago", "set", "out", "nov", "dez",
]

STATUS_DONE = {"perdido", "concluído", "concluido", "fechado", "cancelado"}


def load(name):
    return json.loads((DATA_DIR / name).read_text())


def parse_dt(value):
    if value is None:
        return None
    return datetime.fromisoformat(value)


def process_events(raw_events, now):
    out = []
    for ev in raw_events:
        start = parse_dt(ev["start"])
        end = parse_dt(ev.get("end"))
        summary = (ev.get("summary") or "(sem título)").strip()
        attendees = [a for a in (ev.get("attendees") or [])]
        external = [a for a in attendees if a.lower() != OWNER_EMAIL]
        is_routine = summary in ROUTINE_TITLES
        is_meeting = len(external) > 0
        date_key = start.date().isoformat()
        out.append({
            "summary": summary,
            "dateKey": date_key,
            "weekday": WEEKDAYS_PT[start.weekday()],
            "dateLabel": f"{start.day:02d} {MONTHS_PT[start.month - 1]}",
            "allDay": bool(ev.get("allDay")),
            "timeLabel": "dia inteiro" if ev.get("allDay") else f"{start.strftime('%H:%M')}–{end.strftime('%H:%M')}" if end else start.strftime("%H:%M"),
            "startIso": ev["start"],
            "location": ev.get("location"),
            "attendeeCount": len(external),
            "attendees": external,
            "isRoutine": is_routine,
            "isMeeting": is_meeting,
            "htmlLink": ev.get("htmlLink"),
            "isPast": (end or start) < now,
        })
    out.sort(key=lambda e: e["startIso"])
    return out


PRIORITY_RANK = {"urgent": 0, "high": 1, "normal": 2, "low": 3, None: 4}
PRIORITY_LABEL = {"urgent": "urgente", "high": "alta", "normal": "normal", "low": "baixa", None: "—"}


def process_tasks(raw_tasks, now):
    today_start = datetime(now.year, now.month, now.day, tzinfo=TZ)
    week_end = today_start + timedelta(days=7)
    out = []
    for t in raw_tasks:
        due_ms = t.get("due_date")
        due_dt = datetime.fromtimestamp(int(due_ms) / 1000, tz=TZ) if due_ms else None
        status = (t.get("status") or "").strip()
        is_done = status.lower() in STATUS_DONE
        overdue = bool(due_dt and due_dt < today_start and not is_done)
        due_soon = bool(due_dt and today_start <= due_dt < week_end and not is_done)
        out.append({
            "id": t["id"],
            "name": t["name"],
            "url": t["url"],
            "status": status,
            "priority": t.get("priority"),
            "priorityLabel": PRIORITY_LABEL.get(t.get("priority"), t.get("priority") or "—"),
            "priorityRank": PRIORITY_RANK.get(t.get("priority"), 4),
            "list": t.get("list") or "—",
            "tags": t.get("tags") or [],
            "assignees": t.get("assignees") or [],
            "extraAssignees": [a for a in (t.get("assignees") or []) if a != "Karol"],
            "dueMs": due_ms and int(due_ms),
            "dueLabel": f"{due_dt.day:02d}/{due_dt.month:02d}/{due_dt.year}" if due_dt else "sem prazo",
            "overdue": overdue,
            "dueSoon": due_soon,
            "isDone": is_done,
        })
    out.sort(key=lambda t: (t["dueMs"] is None, t["dueMs"] or 0))
    return out


def build_stats(events, tasks, now):
    today_key = now.date().isoformat()
    week_key = (now + timedelta(days=7)).date().isoformat()
    upcoming = [e for e in events if not e["isPast"] and not e["isRoutine"]]
    open_tasks = [t for t in tasks if not t["isDone"]]
    overdue_tasks = [t for t in open_tasks if t["overdue"]]
    due_soon_tasks = [t for t in open_tasks if t["dueSoon"]]
    no_due_tasks = [t for t in open_tasks if t["dueMs"] is None]
    return {
        "commitmentsToday": len([e for e in upcoming if e["dateKey"] == today_key]),
        "commitments7d": len([e for e in upcoming if e["dateKey"] <= week_key]),
        "commitments30d": len(upcoming),
        "openTasks": len(open_tasks),
        "overdueTasks": len(overdue_tasks),
        "dueSoonTasks": len(due_soon_tasks),
        "noDueTasks": len(no_due_tasks),
    }


def main():
    now = datetime.now(tz=TZ)
    raw_events = load("events_raw.json")
    raw_tasks = load("tasks_karol.json")["tasks"]

    events = process_events(raw_events, now)
    tasks = process_tasks(raw_tasks, now)
    stats = build_stats(events, tasks, now)

    lists = sorted({t["list"] for t in tasks})
    statuses = sorted({t["status"] for t in tasks if t["status"]})

    generated_label = now.strftime("%d/%m/%Y às %H:%M")

    template = (ROOT / "scripts" / "template.html").read_text()
    html = (
        template
        .replace("__GENERATED_AT__", json.dumps(generated_label, ensure_ascii=False))
        .replace("__EVENTS_JSON__", json.dumps(events, ensure_ascii=False))
        .replace("__TASKS_JSON__", json.dumps(tasks, ensure_ascii=False))
        .replace("__STATS_JSON__", json.dumps(stats, ensure_ascii=False))
        .replace("__LISTS_JSON__", json.dumps(lists, ensure_ascii=False))
        .replace("__STATUSES_JSON__", json.dumps(statuses, ensure_ascii=False))
    )

    (ROOT / "index.html").write_text(html)
    print(f"index.html gerado — {len(events)} eventos, {len(tasks)} tarefas.")


if __name__ == "__main__":
    main()
