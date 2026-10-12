"""Deterministic signals about progress AND lack of progress. profile-keeper interprets them; gt computes them."""

from datetime import date

from .derive import linear_slope


def _days(today: date, iso: str) -> int:
    return (today - date.fromisoformat(iso[:10])).days


def compute_signals(st: dict, config: dict, today: date) -> list:
    sig = []

    def add(type_, severity, detail, path_id=None, evidence=None, data=None):
        sig.append({"type": type_, "severity": severity, "path_id": path_id, "detail": detail,
                    "evidence": evidence or [], "data": data or {}})

    # progress: new clean (cold) tempo, milestones, song promotions in the last 7 days
    for ex in st["exercises"].values():
        cold = [h for h in ex["history"] if h["kind"] == "cold_clean"]
        recent = [h for h in cold if _days(today, h["date"]) < 7]
        older = [h["bpm"] for h in cold if _days(today, h["date"]) >= 7]
        if recent:
            best = max(h["bpm"] for h in recent)
            prev = max(older) if older else None
            if prev is None or best > prev:
                add("progress", "info", f"Nowe czyste tempo (na zimno) w „{ex['title']}”: {best} BPM"
                    + (f" (wcześniej {prev})" if prev else ""), ex["path_id"],
                    data={"exercise_id": ex["exercise_id"], "bpm": best, "previous": prev})
    for path in st["paths"].values():
        for m in path["milestones"]:
            if m.get("reached") and _days(today, m["reached"]) < 7:
                add("progress", "info", f"Kamień milowy „{m.get('desc', m['id'])}” zaliczony", path["path_id"],
                    data={"milestone_id": m["id"]})
    for song in st["songs"].values():
        hist = song["status_history"]
        if len(hist) > 1 and _days(today, hist[-1]["ts"]) < 7:
            add("progress", "info", f"„{song['title']}” → {song['status']}", song.get("path_id"),
                data={"song_id": song["song_id"], "status": song["status"]})

    # plateau: enough observations in the window, but the trend is flat
    for path in st["paths"].values():
        if path["status"] != "active":
            continue
        ms = path["metric_state"]
        window = [o for o in path["observations"] if _days(today, o["date"]) <= config["plateau_window_days"]]
        slope = linear_slope([(-_days(today, o["date"]), o["value"]) for o in window])
        if len(window) >= config["plateau_min_points"] and slope is not None:
            weekly = round(slope * 7, 2)
            target = ms["target"] or 1
            if ms["risk"] != "reached" and weekly < config["plateau_min_weekly_gain_pct"] * target:
                add("plateau", "warning", f"Plateau w „{path['title']}”: {len(window)} pomiarów w "
                    f"{config['plateau_window_days']} dni, trend {weekly}/tydz.", path["path_id"],
                    data={"slope_per_week": weekly, "points": len(window)})
        if path["neglected"]:
            add("neglect", "warning", f"„{path['title']}” nie była ćwiczona od {path['days_since_touch']} dni "
                f"(próg {path['min_touch_days']})", path["path_id"], data={"days": path["days_since_touch"]})
        if ms["risk"] in ("at_risk", "overdue"):
            add("deadline_risk", "warning" if ms["risk"] == "at_risk" else "critical",
                f"„{path['title']}”: projekcja {ms['projection_at_deadline']} vs cel {ms['target']} "
                f"({ms['days_left']} dni)", path["path_id"], data=dict(ms))
        for eid in path["exercises"]:
            ex = st["exercises"][eid]
            if ex["suggested_stage"]:
                add("stage_ready", "info", f"„{ex['title']}” gotowe na stadium {ex['suggested_stage']}",
                    path["path_id"], data={"exercise_id": eid, "stage": ex["suggested_stage"]})

    # skipped sessions vs declared habit
    prof = st["profile"] or {}
    declared = prof.get("sessions_per_week")
    if declared and st["practice_days"]:
        first = date.fromisoformat(st["practice_days"][0])
        span = min(14, (today - first).days + 1)
        if span >= 7:
            actual = sum(1 for d in st["practice_days"] if _days(today, d) < span)
            expected = declared * span / 7
            if actual < config["skipped_sessions_ratio"] * expected:
                add("skipped_sessions", "warning", f"{actual} dni z graniem w {span} dni przy deklarowanych "
                    f"{declared}/tydz.", data={"actual": actual, "expected": round(expected, 1)})
    if st["days_since_practice"] is not None and st["days_since_practice"] >= config["inactivity_days"]:
        add("inactivity", "warning", f"{st['days_since_practice']} dni bez grania",
            data={"days": st["days_since_practice"]})

    # health: pain, high tension, volume jump
    for p in st["pains"]:
        if _days(today, p["ts"]) <= 14:
            add("health_risk", "critical" if p["severity"] >= 3 else "warning",
                f"Zgłoszony ból: {p['location']} ({p['severity']}/5, {_days(today, p['ts'])} dni temu)",
                data={"location": p["location"], "severity": p["severity"]})
    vol = st["volume"]
    ref = max(vol["minutes_prev_7d"], vol["minutes_prev_8_28d"] / 3)
    if ref and vol["minutes_7d"] > ref * (1 + config["volume_jump_limit"]):
        add("health_risk", "warning", f"Objętość {round(vol['minutes_7d'])} min/7 dni vs ok. {round(ref)} wcześniej "
            f"(> +{int(config['volume_jump_limit'] * 100)}%)", data={"minutes_7d": vol["minutes_7d"], "ref": ref})

    # recordings: timing trend per exercise
    by_ex = {}
    for r in st["recordings"]:
        if r.get("exercise_id") and "timing_mean_abs_ms" in r["metrics"]:
            by_ex.setdefault(r["exercise_id"], []).append(r)
    for eid, recs in by_ex.items():
        if len(recs) >= 2:
            a, b = recs[-2]["metrics"]["timing_mean_abs_ms"], recs[-1]["metrics"]["timing_mean_abs_ms"]
            if abs(b - a) >= 2:
                ex = st["exercises"].get(eid, {})
                add("timing_trend", "info" if b < a else "warning",
                    f"Timing w „{ex.get('title', eid)}”: {a:.0f} → {b:.0f} ms średniego odchylenia",
                    ex.get("path_id"), data={"exercise_id": eid, "before_ms": a, "after_ms": b})

    order = {"critical": 0, "warning": 1, "info": 2}
    sig.sort(key=lambda s: (order[s["severity"]], s["type"]))
    return sig
