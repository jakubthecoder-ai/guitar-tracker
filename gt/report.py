"""Self-contained interactive HTML report. Data embedded as JSON; JS renders and emits events (server or offline queue)."""

import json
from datetime import date, timedelta
from pathlib import Path

from .config import AXES
from .schedule import build_plan
from .store import atomic_write
from .views import AXIS_PL

TEMPLATE = Path(__file__).parent / "templates" / "report.html"


def view_model(store, st: dict, today: date, server: dict | None = None) -> dict:
    events = store.load_events()
    minutes_by_day = {}
    for ev in events:
        if ev["type"] == "item_logged":
            d = ev["ts"][:10]
            minutes_by_day[d] = minutes_by_day.get(d, 0) + ev["payload"]["minutes"]
    start = today - timedelta(days=today.weekday() + 7 * 11)  # Monday, 12 weeks back
    plan = st["plans"].get(today.isoformat())
    preview = None
    if not plan and st["paths"]:
        preview = build_plan(st, store.config, today, 60)
    prof = st["profile"] or {}
    return {
        "as_of": today.isoformat(),
        "axes": [{"id": a, "label": AXIS_PL[a], "level": (prof.get("axes", {}).get(a) or {}).get("level")}
                 for a in AXES],
        "profile": {k: prof.get(k) for k in ("name", "intention", "weekly_minutes", "sessions_per_week", "genres",
                                             "gear", "years_playing")},
        "pending_changes": st["pending_changes"],
        "history": st["profile_history"][-30:],
        "paths": list(st["paths"].values()),
        "exercises": st["exercises"],
        "songs": list(st["songs"].values()),
        "plan": plan,
        "plan_preview": preview,
        "volume": st["volume"],
        "days_since_practice": st["days_since_practice"],
        "open_session": st["open_session"],
        "notes": st["notes"][-5:],
        "calendar": {"start": start.isoformat(), "days": (today - start).days + 1, "minutes": minutes_by_day},
        "server": server,
    }


def render_html(vm: dict) -> str:
    data = json.dumps(vm, ensure_ascii=False, sort_keys=True, default=str).replace("</", "<\\/")
    return TEMPLATE.read_text(encoding="utf-8").replace("/*__GT_STATE__*/{}", data)


def write_report(store, st: dict, today: date, out: Path | None = None) -> Path:
    out = out or store.home / "reports" / "latest.html"
    atomic_write(out, render_html(view_model(store, st, today)))
    return out
