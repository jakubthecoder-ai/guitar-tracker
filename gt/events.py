"""Event definitions and validation. The event log is the single source of truth."""

import uuid
from datetime import date

from .config import AXES, METRIC_TYPES, PATH_STATUSES, PRACTICE_TYPES, SONG_STATUSES, STAGES, now_iso

SOURCES = ["cli", "mcp", "html", "agent", "audio"]

# field -> (type, required). Types: str, int, num, bool, list, dict, date, or a list of allowed values.
SPECS = {
    "profile_initialized": {"axes": ("dict", True), "weekly_minutes": ("int", False),
                            "sessions_per_week": ("int", False), "years_playing": ("num", False),
                            "genres": ("list", False), "gear": ("dict", False), "intention": ("str", False),
                            "goals_text": ("str", False), "benchmarks": ("dict", False), "notes": ("str", False),
                            "answers": ("list", False), "risks": ("list", False), "name": ("str", False)},
    "profile_changed": {"change_id": ("str", True), "field": ("str", True), "new": ("any", True),
                        "trigger": (["progress", "plateau", "neglect", "skip", "user", "placement",
                                     "deadline_risk", "health", "recording", "retro"], True),
                        "rationale": ("str", True), "evidence": ("list", False),
                        "requires_confirmation": ("bool", False)},
    "profile_change_confirmed": {"change_id": ("str", True), "accepted": ("bool", True), "note": ("str", False)},
    "path_proposed": {"proposal_id": ("str", True), "title": ("str", True), "goal": ("str", True),
                      "topic_axis": (AXES, True), "rationale": ("str", False), "primary_metric": ("dict", False)},
    "path_created": {"path_id": ("str", True), "title": ("str", True), "goal": ("str", True),
                     "topic_axis": (AXES, True), "primary_metric": ("dict", True), "deadline": ("date", True),
                     "priority": ("int", False), "status": (["active", "paused"], True),
                     "milestones": ("list", False), "min_touch_days": ("int", False),
                     "created_from": (["placement", "user"], False), "interview": ("str", False),
                     "baseline": ("dict", False), "proposal_id": ("str", False)},
    "path_status_changed": {"path_id": ("str", True), "status": (PATH_STATUSES, True), "reason": ("str", False)},
    "path_priority_changed": {"path_id": ("str", True), "priority": ("int", True), "reason": ("str", False)},
    "deadline_changed": {"path_id": ("str", True), "deadline": ("date", True), "reason": ("str", True)},
    "milestone_reached": {"path_id": ("str", True), "milestone_id": ("str", True), "note": ("str", False)},
    "metric_recorded": {"path_id": ("str", True), "value": ("num", True), "note": ("str", False)},
    "retro_recorded": {"path_id": ("str", False), "week": ("str", True), "text": ("str", True)},
    "exercise_created": {"exercise_id": ("str", True), "path_id": ("str", True), "title": ("str", True),
                         "technique": ("str", False), "subdivision": ("str", False), "bpm_start": ("int", False),
                         "bpm_target": ("int", False), "step_pct": ("num", False), "description": ("str", False),
                         "stage": (STAGES, False), "primary": ("bool", False)},
    "exercise_stage_changed": {"exercise_id": ("str", True), "stage": (STAGES, True), "reason": ("str", False)},
    "plan_committed": {"date": ("date", True), "minutes": ("int", True), "blocks": ("list", True),
                       "rationale": ("str", False)},
    "session_started": {"session_id": ("str", True), "minutes_planned": ("int", False), "plan_date": ("date", False)},
    "item_logged": {"path_id": ("str", False), "exercise_id": ("str", False), "song_id": ("str", False),
                    "session_id": ("str", False), "practice_type": (PRACTICE_TYPES, True), "minutes": ("num", True),
                    "bpm": ("int", False), "clean_reps": ("int", False), "max_bpm_burst": ("int", False),
                    "rating": ("int", False), "tension": ("int", False), "note": ("str", False),
                    "done": ("bool", False)},
    "cold_check": {"exercise_id": ("str", True), "bpm": ("int", True), "clean": ("bool", True),
                   "session_id": ("str", False), "note": ("str", False)},
    "session_ended": {"session_id": ("str", True), "rating": ("int", False), "note": ("str", False)},
    "pain_reported": {"location": ("str", True), "severity": ("int", True), "note": ("str", False)},
    "song_added": {"song_id": ("str", True), "artist": ("str", True), "title": ("str", True),
                   "path_id": ("str", False), "role": ("str", False), "tuning": ("str", False),
                   "sections": ("list", False), "techniques": ("list", False), "difficulty": ("num", False),
                   "source": ("str", False), "verified_at": ("str", False), "why": ("str", False),
                   "status": (SONG_STATUSES, False), "url": ("str", False)},
    "song_status_changed": {"song_id": ("str", True), "status": (SONG_STATUSES, True), "note": ("str", False)},
    "mentor_note": {"text": ("str", True), "scope": ("str", False)},
    "recording_analyzed": {"exercise_id": ("str", False), "file": ("str", True), "metrics": ("dict", True)},
}

METRIC_SPEC = {"type": (METRIC_TYPES, True), "target": ("num", True), "unit": ("str", False),
               "exercise_id": ("str", False), "description": ("str", False)}


def new_id(prefix: str = "") -> str:
    u = uuid.uuid4().hex
    return f"{prefix}{u[:8]}" if prefix else str(uuid.uuid4())


def make_event(etype: str, payload: dict, source: str = "cli", actor: str = "user", ts: str = None) -> dict:
    ev = {"id": str(uuid.uuid4()), "ts": ts or now_iso(), "type": etype, "source": source,
          "actor": actor, "payload": {k: v for k, v in payload.items() if v is not None}}
    errors = validate_event(ev)
    if errors:
        raise ValueError("; ".join(errors))
    return ev


def _check(value, typ) -> bool:
    if typ == "any":
        return True
    if isinstance(typ, list):
        return value in typ
    if typ == "str":
        return isinstance(value, str)
    if typ == "int":
        return isinstance(value, int) and not isinstance(value, bool)
    if typ == "num":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if typ == "bool":
        return isinstance(value, bool)
    if typ == "list":
        return isinstance(value, list)
    if typ == "dict":
        return isinstance(value, dict)
    if typ == "date":
        try:
            date.fromisoformat(value)
            return True
        except (TypeError, ValueError):
            return False
    raise AssertionError(typ)


def validate_fields(obj: dict, spec: dict, where: str) -> list:
    errors = []
    for field, (typ, required) in spec.items():
        if field not in obj or obj[field] is None:
            if required:
                errors.append(f"{where}: brak pola '{field}'")
            continue
        if not _check(obj[field], typ):
            allowed = f" (dozwolone: {', '.join(map(str, typ))})" if isinstance(typ, list) else f" (oczekiwano {typ})"
            errors.append(f"{where}: złe pole '{field}'={obj[field]!r}{allowed}")
    return errors


def validate_event(ev: dict) -> list:
    errors = []
    for f in ["id", "ts", "type", "source", "payload"]:
        if f not in ev:
            errors.append(f"zdarzenie: brak pola '{f}'")
    if errors:
        return errors
    if ev["type"] not in SPECS:
        return [f"nieznany typ zdarzenia '{ev['type']}'"]
    if ev["source"] not in SOURCES:
        errors.append(f"nieznane źródło '{ev['source']}'")
    errors += validate_fields(ev["payload"], SPECS[ev["type"]], ev["type"])
    if ev["type"] == "path_created" and isinstance(ev["payload"].get("primary_metric"), dict):
        errors += validate_fields(ev["payload"]["primary_metric"], METRIC_SPEC, "primary_metric")
    if ev["type"] == "item_logged":
        p = ev["payload"]
        for k in ("rating", "tension"):
            if k in p and not 1 <= p[k] <= 5:
                errors.append(f"item_logged: {k} musi być 1–5")
    if ev["type"] == "profile_initialized":
        for axis, v in ev["payload"].get("axes", {}).items():
            if axis not in AXES:
                errors.append(f"profile_initialized: nieznana oś '{axis}'")
            elif not isinstance(v, dict) or not isinstance(v.get("level"), int) or not 1 <= v["level"] <= 5:
                errors.append(f"profile_initialized: oś '{axis}' wymaga level 1–5")
    return errors
