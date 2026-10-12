"""Fold the event log into the current state (derived/state.json). Pure function of events + config + date."""

import copy
from datetime import date, timedelta

from .config import AXES, SONG_STATUSES, STAGES


def _d(ts: str) -> date:
    return date.fromisoformat(ts[:10])


def _set_dotted(obj: dict, dotted: str, value) -> object:
    keys = dotted.split(".")
    cur = obj
    for k in keys[:-1]:
        cur = cur.setdefault(k, {})
    old = cur.get(keys[-1])
    cur[keys[-1]] = value
    return old


def linear_slope(points: list) -> float | None:
    """points: [(day_number, value)] -> slope per day (least squares)."""
    if len(points) < 2:
        return None
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    if max(xs) == min(xs):
        return None
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    num = sum((x - mx) * (y - my) for x, y in points)
    den = sum((x - mx) ** 2 for x in xs)
    return num / den


def derive(events: list, config: dict, today: date) -> dict:
    st = {
        "as_of": today.isoformat(),
        "profile": None,
        "profile_history": [],
        "pending_changes": [],
        "proposals": {},
        "paths": {},
        "exercises": {},
        "songs": {},
        "sessions": [],
        "open_session": None,
        "plans": {},
        "notes": [],
        "retros": [],
        "pains": [],
        "recordings": [],
        "event_count": len(events),
        "last_activity": None,
    }
    changes = {}
    sessions = {}
    logs = []

    for ev in events:
        t, p, ts = ev["type"], ev["payload"], ev["ts"]
        if t == "profile_initialized":
            prof = copy.deepcopy(p)
            prof["initialized_at"] = ts
            for axis in AXES:
                prof.setdefault("axes", {}).setdefault(axis, {"level": None})
            st["profile"] = prof
            st["profile_history"].append({"ts": ts, "field": "*", "old": None, "new": "init",
                                          "trigger": "placement", "rationale": "Profil startowy z wywiadu",
                                          "evidence": [ev["id"]], "status": "applied"})
        elif t == "profile_changed":
            ch = dict(p, ts=ts, event_id=ev["id"],
                      status="pending" if p.get("requires_confirmation") else "applied")
            changes[p["change_id"]] = ch
            if ch["status"] == "applied":
                ch["old"] = _apply_change(st, ch)
            st["profile_history"].append(ch)
        elif t == "profile_change_confirmed":
            ch = changes.get(p["change_id"])
            if ch and ch["status"] == "pending":
                ch["status"] = "applied" if p["accepted"] else "rejected"
                ch["confirmed_at"] = ts
                if p["accepted"]:
                    ch["old"] = _apply_change(st, ch)
        elif t == "path_proposed":
            st["proposals"][p["proposal_id"]] = dict(p, ts=ts, status="open")
        elif t == "path_created":
            path = copy.deepcopy(p)
            path.update(created=ts[:10], exercises=[], songs=[], status_history=[{"ts": ts, "status": p["status"]}],
                        last_touch=None, minutes_total=0.0, observations=[])
            path.setdefault("priority", 3)
            path.setdefault("min_touch_days", config["min_touch_days"])
            path.setdefault("milestones", [])
            for i, m in enumerate(path["milestones"]):
                m.setdefault("id", f"m{i}")
                m.setdefault("reached", None)
            st["paths"][p["path_id"]] = path
            if p.get("proposal_id") in st["proposals"]:
                st["proposals"][p["proposal_id"]]["status"] = "accepted"
        elif t == "path_status_changed" and p["path_id"] in st["paths"]:
            path = st["paths"][p["path_id"]]
            path["status"] = p["status"]
            path["status_history"].append({"ts": ts, "status": p["status"], "reason": p.get("reason")})
        elif t == "path_priority_changed" and p["path_id"] in st["paths"]:
            st["paths"][p["path_id"]]["priority"] = p["priority"]
        elif t == "deadline_changed" and p["path_id"] in st["paths"]:
            path = st["paths"][p["path_id"]]
            path.setdefault("deadline_history", []).append({"ts": ts, "old": path["deadline"], "new": p["deadline"],
                                                            "reason": p["reason"]})
            path["deadline"] = p["deadline"]
        elif t == "milestone_reached" and p["path_id"] in st["paths"]:
            for m in st["paths"][p["path_id"]]["milestones"]:
                if m["id"] == p["milestone_id"]:
                    m["reached"] = ts[:10]
        elif t == "metric_recorded" and p["path_id"] in st["paths"]:
            st["paths"][p["path_id"]]["observations"].append({"date": ts[:10], "value": p["value"], "src": "manual"})
        elif t == "retro_recorded":
            st["retros"].append(dict(p, ts=ts))
        elif t == "exercise_created":
            ex = copy.deepcopy(p)
            ex.setdefault("stage", "learn")
            ex.setdefault("step_pct", config["bpm_step_pct"])
            ex.update(created=ts[:10], clean_bpm=None, candidate_bpm=None, burst_bpm=None, last_logged=None,
                      history=[], log=[], stage_changed=ts[:10], maintain_reviews=0, minutes_total=0.0,
                      last_tension=None, last_rating=None)
            st["exercises"][p["exercise_id"]] = ex
            if p["path_id"] in st["paths"]:
                st["paths"][p["path_id"]]["exercises"].append(p["exercise_id"])
        elif t == "exercise_stage_changed" and p["exercise_id"] in st["exercises"]:
            ex = st["exercises"][p["exercise_id"]]
            ex["stage"], ex["stage_changed"], ex["maintain_reviews"] = p["stage"], ts[:10], 0
        elif t == "plan_committed":
            st["plans"][p["date"]] = dict(p, ts=ts)
        elif t == "session_started":
            sessions[p["session_id"]] = {"session_id": p["session_id"], "started": ts, "ended": None,
                                         "minutes_planned": p.get("minutes_planned"), "minutes": 0.0,
                                         "items": 0, "rating": None, "note": None}
            st["open_session"] = p["session_id"]
        elif t == "session_ended" and p["session_id"] in sessions:
            s = sessions[p["session_id"]]
            s.update(ended=ts, rating=p.get("rating"), note=p.get("note"))
            if st["open_session"] == p["session_id"]:
                st["open_session"] = None
        elif t == "item_logged":
            logs.append(ev)
            sid = p.get("session_id") or st["open_session"]
            if sid in sessions:
                sessions[sid]["minutes"] += p["minutes"]
                sessions[sid]["items"] += 1
            _apply_log(st, ev, config)
        elif t == "cold_check" and p["exercise_id"] in st["exercises"]:
            ex = st["exercises"][p["exercise_id"]]
            ex["history"].append({"date": ts[:10], "bpm": p["bpm"], "kind": "cold_clean" if p["clean"] else "cold_fail"})
            if p["clean"] and (ex["clean_bpm"] is None or p["bpm"] > ex["clean_bpm"]):
                ex["clean_bpm"] = p["bpm"]
            path = st["paths"].get(ex["path_id"])
            if path and p["clean"]:
                metric = path["primary_metric"]
                if metric["type"] == "bpm" and metric.get("exercise_id") in (None, ex["exercise_id"]):
                    path["observations"].append({"date": ts[:10], "value": p["bpm"], "src": "cold_check"})
        elif t == "pain_reported":
            st["pains"].append(dict(p, ts=ts))
        elif t == "song_added":
            song = copy.deepcopy(p)
            song.setdefault("status", "backlog")
            song.update(added=ts[:10], status_history=[{"ts": ts, "status": song["status"]}], last_played=None)
            st["songs"][p["song_id"]] = song
            if p.get("path_id") in st["paths"]:
                st["paths"][p["path_id"]]["songs"].append(p["song_id"])
        elif t == "song_verified" and p["song_id"] in st["songs"]:
            song = st["songs"][p["song_id"]]
            song.update({k: v for k, v in p.items() if k != "song_id" and k != "verified"})
            song["verified_at"] = ts[:10] if p["verified"] else None
            song["verification"] = "ok" if p["verified"] else "not_found"
        elif t == "song_status_changed" and p["song_id"] in st["songs"]:
            song = st["songs"][p["song_id"]]
            song["status"] = p["status"]
            song["status_history"].append({"ts": ts, "status": p["status"], "note": p.get("note")})
            path = st["paths"].get(song.get("path_id"))
            if path and path["primary_metric"]["type"] == "song_status":
                path["observations"].append({"date": ts[:10], "value": SONG_STATUSES.index(p["status"]),
                                             "src": "song_status"})
        elif t == "mentor_note":
            st["notes"].append(dict(p, ts=ts))
        elif t == "recording_analyzed":
            st["recordings"].append(dict(p, ts=ts))
        if t not in ("mentor_note", "path_proposed"):
            st["last_activity"] = ts

    st["sessions"] = sorted(sessions.values(), key=lambda s: s["started"])
    st["pending_changes"] = [c for c in changes.values() if c["status"] == "pending"]
    _finalize(st, logs, config, today, events)
    return st


def _apply_change(st: dict, ch: dict):
    field = ch["field"]
    if field.startswith("path."):
        _, pid, attr = field.split(".", 2)
        path = st["paths"].get(pid)
        if not path:
            return None
        old = path.get(attr)
        path[attr] = ch["new"]
        return old
    if st["profile"] is None:
        st["profile"] = {"axes": {a: {"level": None} for a in AXES}}
    return _set_dotted(st["profile"], field, ch["new"])


def _apply_log(st: dict, ev: dict, config: dict) -> None:
    p, day = ev["payload"], ev["ts"][:10]
    path = st["paths"].get(p.get("path_id"))
    ex = st["exercises"].get(p.get("exercise_id"))
    if ex and not path:
        path = st["paths"].get(ex["path_id"])
    song = st["songs"].get(p.get("song_id"))
    if song and not path:
        path = st["paths"].get(song.get("path_id"))
    if path:
        path["last_touch"] = max(filter(None, [path["last_touch"], day]))
        path["minutes_total"] += p["minutes"]
        if path["primary_metric"]["type"] == "minutes":
            path["observations"].append({"date": day, "value": path["minutes_total"], "src": "minutes"})
    if song:
        song["last_played"] = day
    if ex:
        ex["last_logged"] = day
        ex["minutes_total"] += p["minutes"]
        for k in ("tension", "rating", "note"):
            if p.get(k) is not None:
                ex[f"last_{k}"] = p[k]
        ex["log"].append({k: v for k, v in {"date": day, "minutes": p["minutes"], "bpm": p.get("bpm"),
                                            "clean_reps": p.get("clean_reps"), "tension": p.get("tension"),
                                            "rating": p.get("rating"), "note": p.get("note")}.items()
                          if v is not None})
        if ex["stage"] == "maintain":
            ex["maintain_reviews"] += 1
        bpm = p.get("bpm")
        if bpm:
            clean = (p.get("clean_reps") or 0) >= config["min_clean_reps"]
            ex["history"].append({"date": day, "bpm": bpm, "kind": "clean_reps" if clean else "attempt",
                                  "clean_reps": p.get("clean_reps"), "rating": p.get("rating")})
            if clean and (ex["candidate_bpm"] is None or bpm > ex["candidate_bpm"]):
                ex["candidate_bpm"] = bpm
        burst = p.get("max_bpm_burst")
        if burst:
            ex["history"].append({"date": day, "bpm": burst, "kind": "burst"})
            if ex["burst_bpm"] is None or burst > ex["burst_bpm"]:
                ex["burst_bpm"] = burst


def _finalize(st: dict, logs: list, config: dict, today: date, events: list = ()) -> None:
    window = config["trend_window_days"]
    for path in st["paths"].values():
        ref = path["last_touch"] or path["created"]
        path["days_since_touch"] = (today - date.fromisoformat(ref)).days
        path["neglected"] = path["status"] == "active" and path["days_since_touch"] > path["min_touch_days"]
        path["minutes_7d"] = sum(e["payload"]["minutes"] for e in logs if _touches(st, e, path["path_id"])
                                 and (today - _d(e["ts"])).days < 7)
        metric = path["primary_metric"]
        obs = sorted(path["observations"], key=lambda o: o["date"])
        if metric["type"] == "bpm":
            current = max((o["value"] for o in obs), default=None)
            baseline = (path.get("baseline") or {}).get("bpm")
            if current is None and baseline is not None:
                current = baseline
        else:
            current = obs[-1]["value"] if obs else (path.get("baseline") or {}).get("value")
        recent = [((date.fromisoformat(o["date"]) - today).days, o["value"]) for o in obs
                  if (today - date.fromisoformat(o["date"])).days <= window]
        if metric["type"] == "bpm" and (path.get("baseline") or {}).get("bpm") is not None:
            bday = (date.fromisoformat(path["created"]) - today).days
            if -bday <= window:
                recent.append((bday, path["baseline"]["bpm"]))
        slope = linear_slope(recent)
        days_left = (date.fromisoformat(path["deadline"]) - today).days
        projection = None
        if current is not None and slope is not None:
            projection = round(current + slope * max(days_left, 0), 1)
        target = metric["target"]
        if current is not None and current >= target:
            risk = "reached"
        elif days_left < 0:
            risk = "overdue"
        elif projection is None:
            risk = "unknown"
        elif projection >= target:
            risk = "on_track"
        elif projection >= current + 0.7 * (target - current):
            risk = "tight"
        else:
            risk = "at_risk"
        progress = None
        start = (path.get("baseline") or {}).get("bpm" if metric["type"] == "bpm" else "value")
        if current is not None and start is not None and target != start:
            progress = round(max(0.0, min(1.0, (current - start) / (target - start))), 3)
        eta = None
        if current is not None and slope and slope > 0 and current < target:
            eta = (today + timedelta(days=round((target - current) / slope))).isoformat()
        path["metric_state"] = {"eta": eta, "current": current, "target": target, "slope_per_week": None if slope is None
                                else round(slope * 7, 2), "projection_at_deadline": projection,
                                "days_left": days_left, "risk": risk, "progress": progress}
        nxt = [m for m in path["milestones"] if not m.get("reached")]
        path["next_milestone"] = nxt[0] if nxt else None

    intervals = config["review_intervals_days"]
    thr = config["stabilise_threshold"]
    for ex in st["exercises"].values():
        target = ex.get("bpm_target")
        suggestion = None
        if target:
            if ex["stage"] == "learn" and (ex["candidate_bpm"] or 0) >= thr * target:
                suggestion = "stabilise"
            elif ex["stage"] == "stabilise" and (ex["clean_bpm"] or 0) >= thr * target:
                suggestion = "speed"
            elif ex["stage"] == "speed" and (ex["clean_bpm"] or 0) >= target:
                suggestion = "apply"
        ex["suggested_stage"] = suggestion
        ex["needs_cold_check"] = bool(ex["candidate_bpm"] and (ex["clean_bpm"] or 0) < ex["candidate_bpm"])
        if ex["stage"] == "maintain":
            base = date.fromisoformat(ex["last_logged"] or ex["stage_changed"])
            gap = intervals[min(ex["maintain_reviews"], len(intervals) - 1)]
            ex["next_review"] = (base + timedelta(days=gap)).isoformat()
        else:
            ex["next_review"] = None

    def minutes_between(a, b):
        return sum(e["payload"]["minutes"] for e in logs if a <= (today - _d(e["ts"])).days < b)

    st["volume"] = {"minutes_7d": minutes_between(0, 7), "minutes_prev_7d": minutes_between(7, 14),
                    "minutes_prev_8_28d": minutes_between(7, 28),
                    "sessions_14d": sum(1 for s in st["sessions"] if (today - _d(s["started"])).days < 14)}
    days = sorted({_d(e["ts"]) for e in logs} | {_d(e["ts"]) for e in events if e["type"] == "cold_check"})
    st["practice_days"] = [d.isoformat() for d in days]
    st["days_since_practice"] = (today - days[-1]).days if days else None
    st["active_paths"] = [pid for pid, p in st["paths"].items() if p["status"] == "active"]


def _touches(st: dict, ev: dict, path_id: str) -> bool:
    p = ev["payload"]
    if p.get("path_id") == path_id:
        return True
    ex = st["exercises"].get(p.get("exercise_id"))
    if ex and ex["path_id"] == path_id and not p.get("path_id"):
        return True
    song = st["songs"].get(p.get("song_id"))
    return bool(song and song.get("path_id") == path_id and not p.get("path_id"))


__all__ = ["derive", "linear_slope", "STAGES"]
