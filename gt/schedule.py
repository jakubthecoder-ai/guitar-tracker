"""Deterministic session skeleton: WHICH paths and HOW MANY minutes. Agents decide WHAT to play inside slots."""

from datetime import date

RISK_URGENCY = {"at_risk": 1.5, "overdue": 1.5, "tight": 1.25, "unknown": 1.0, "on_track": 0.9, "reached": 0.5}


def _k_for(minutes: int, config: dict) -> int:
    table = sorted((int(k), v) for k, v in config["paths_per_session"].items())
    k = table[0][1]
    for limit, val in table:
        if minutes >= limit:
            k = val
    return k


def next_bpm(ex: dict, config: dict) -> int | None:
    target = ex.get("bpm_target")
    if not target:
        return None
    stage = ex["stage"]
    if stage == "learn":
        return ex.get("bpm_start") or round(target * 0.6)
    if stage == "stabilise":
        return ex["candidate_bpm"] or ex["clean_bpm"] or ex.get("bpm_start") or round(target * 0.65)
    if stage == "speed":
        base = ex["clean_bpm"] or ex["candidate_bpm"] or ex.get("bpm_start") or round(target * 0.7)
        last = next((h for h in reversed(ex["history"]) if h["kind"] in ("clean_reps", "attempt")), None)
        if last and last["kind"] == "clean_reps" and last["bpm"] >= base:
            return min(target, round(last["bpm"] * (1 + ex.get("step_pct", config["bpm_step_pct"]))))
        return base
    return target


def score_path(path: dict, st: dict, config: dict) -> tuple:
    reasons = []
    pw = config["priority_weights"].get(str(path.get("priority", 3)), 1.0)
    reasons.append(f"priorytet {path.get('priority', 3)}")
    neglect = 1 + path["days_since_touch"] / max(path["min_touch_days"], 1)
    if path["neglected"]:
        reasons.append(f"zaniedbana: {path['days_since_touch']} dni bez ćwiczenia (próg {path['min_touch_days']})")
    ms = path["metric_state"]
    urgency = RISK_URGENCY.get(ms["risk"], 1.0)
    if ms["days_left"] >= 0:
        urgency *= 1 + max(0, 30 - ms["days_left"]) / 60
    if ms["risk"] in ("at_risk", "tight", "overdue"):
        reasons.append(f"ryzyko deadline'u ({ms['risk']}, {ms['days_left']} dni)")
    attempts = [h for eid in path["exercises"] for h in st["exercises"][eid]["history"][-10:]
                if h["kind"] in ("attempt", "clean_reps", "cold_fail", "cold_clean")]
    weak = sum(1 for h in attempts if h["kind"] in ("attempt", "cold_fail"))
    weakness = 1 + 0.5 * (weak / len(attempts)) if attempts else 1.0
    if attempts and weak / len(attempts) >= 0.5:
        reasons.append("dużo nieczystych prób ostatnio")
    score = round(pw * neglect * urgency * weakness, 3)
    return score, reasons


def build_plan(st: dict, config: dict, today: date, minutes: int, only_paths: list | None = None,
               ignore_volume_cap: bool = False) -> dict:
    warnings = []
    mode = "normal"
    pains = [p for p in st["pains"] if (today - date.fromisoformat(p["ts"][:10])).days <= config["pain_lookback_days"]]
    if any(p["severity"] >= 3 for p in pains):
        mode = "light"
        minutes = min(minutes, 20)
        warnings.append("Zgłoszony ból w ostatnich dniach: sesja lekka (max 20 min, tempo ≤70% czystego, bez burstów). "
                        "Jeśli ból się utrzymuje lub nasila: przerwa i konsultacja (fizjoterapeuta/lekarz).")
    vol = st["volume"]
    # reference = larger of last week and the 3 weeks before it (avg), so one missed week does not reset the base
    ref = max(vol["minutes_prev_7d"], vol["minutes_prev_8_28d"] / 3)
    if ref > 0 and mode == "normal":
        cap = ref * (1 + config["volume_jump_limit"]) - vol["minutes_7d"]
        new_min = max(config["min_session_minutes"], int(cap))
        if new_min < minutes:
            limit = f"+{int(config['volume_jump_limit'] * 100)}% względem ostatnich tygodni ({round(ref)} min/tydz.)"
            if ignore_volume_cap:
                warnings.append(f"Limit przyrostu objętości ({limit}) przekroczony na życzenie użytkownika: "
                                f"{minutes} min zamiast {new_min}. Obserwuj napięcie i ból.")
            else:
                warnings.append(f"Limit przyrostu objętości ({limit}): skracam sesję z {minutes} do {new_min} min. "
                                "Świadome przekroczenie: `gt plan --ignore-volume-cap`.")
                minutes = new_min
    if st["days_since_practice"] is not None and st["days_since_practice"] >= config["inactivity_days"]:
        warnings.append(f"{st['days_since_practice']} dni przerwy: zaczynamy spokojniej, tempo od czystego, nie od rekordu.")

    candidates = [p for p in st["paths"].values() if p["status"] == "active"
                  and (not only_paths or p["path_id"] in only_paths)]
    if only_paths:
        missing = set(only_paths) - {p["path_id"] for p in candidates}
        if missing:
            warnings.append(f"Pominięte (nieaktywne lub nieznane): {', '.join(sorted(missing))}")
    scored = []
    for p in candidates:
        s, reasons = score_path(p, st, config)
        scored.append({"path_id": p["path_id"], "title": p["title"], "score": s, "reasons": reasons,
                       "forced": p["neglected"]})
    scored.sort(key=lambda x: (not x["forced"], -x["score"], x["path_id"]))
    k = min(_k_for(minutes, config), len(scored)) if not only_paths else len(scored)
    k = min(k, max(int(n) for n in config["path_shares"]))
    selected, skipped = scored[:k], scored[k:]
    if any(s["forced"] for s in skipped):
        warnings.append("Więcej zaniedbanych ścieżek niż slotów: rozważ dłuższą sesję albo pauzę ścieżki.")
    selected.sort(key=lambda x: -x["score"])

    warmup = max(config["min_warmup_minutes"], round(minutes * config["warmup_share"]))
    review = round(minutes * config["review_share"]) if minutes >= 30 else 0
    remaining = max(minutes - warmup - review, 0)
    shares = config["path_shares"].get(str(len(selected)), [])
    total_share = sum(shares) or 1
    alloc = [round(remaining * s / total_share) for s in shares]
    if alloc:
        alloc[0] += remaining - sum(alloc)

    cold = [{"exercise_id": e["exercise_id"], "title": e["title"], "path_id": e["path_id"],
             "bpm": e["candidate_bpm"], "last_clean_confirmed": e["clean_bpm"]}
            for e in st["exercises"].values()
            if e["needs_cold_check"] and e["last_logged"] and e["last_logged"] < today.isoformat()
            and st["paths"].get(e["path_id"], {}).get("status") == "active"]

    slots = [{"kind": "warmup", "minutes": warmup, "note": "Rozgrzewka 3–5 min bez max tempa, potem test na zimno "
              "(bez wcześniejszego rozgrywania tych elementów).", "cold_checks": cold}]
    for sel, mins in zip(selected, alloc):
        path = st["paths"][sel["path_id"]]
        exs = []
        for eid in path["exercises"]:
            e = st["exercises"][eid]
            if e["stage"] == "maintain":
                continue
            exs.append({"exercise_id": eid, "title": e["title"], "stage": e["stage"],
                        "mode": "block" if e["stage"] == "learn" else "interleave",
                        "bpm_next": next_bpm(e, config) if mode == "normal" else (
                            round((e["clean_bpm"] or next_bpm(e, config) or 0) * 0.7) or None),
                        "bpm_clean": e["clean_bpm"], "bpm_target": e.get("bpm_target"),
                        "suggested_stage": e["suggested_stage"]})
        slots.append({"kind": "path", "path_id": sel["path_id"], "title": sel["title"], "minutes": mins,
                      "next_milestone": path["next_milestone"], "metric_state": path["metric_state"],
                      "exercises": exs, "needs_exercises": not exs})
    if review:
        reviews = [{"exercise_id": e["exercise_id"], "title": e["title"], "path_id": e["path_id"]}
                   for e in st["exercises"].values()
                   if e["stage"] == "maintain" and e["next_review"] and e["next_review"] <= today.isoformat()]
        sel_ids = [s["path_id"] for s in selected]
        songs = sorted((s for s in st["songs"].values() if s["status"] in ("learning", "polishing", "performance_ready")
                        and st["paths"].get(s.get("path_id"), {}).get("status", "active") == "active"),
                       key=lambda s: (s.get("path_id") not in sel_ids, s["last_played"] or ""))[:2]
        slots.append({"kind": "review_music", "minutes": review, "reviews_due": reviews,
                      "songs": [{"song_id": s["song_id"], "artist": s["artist"], "title": s["title"],
                                 "status": s["status"]} for s in songs],
                      "note": "Powtórki z maintain + blok muzyczny (utwór lub jam z podkładem)."})

    return {
        "date": today.isoformat(),
        "minutes": minutes,
        "mode": mode,
        "selected": selected,
        "skipped": skipped,
        "slots": slots,
        "warnings": warnings,
        "rules": {
            "learn_stage": "ciągły blok, wolno, fragmentami",
            "interleave": f"elementy stabilise/speed/apply z różnych ścieżek w rotacjach "
                          f"{config['rotation_minutes'][0]}–{config['rotation_minutes'][1]} min, cyklicznie 2–4 elementy",
            "microbreak_every_minutes": config["microbreak_every_minutes"],
            "bpm": f"podnoś o ~{int(config['bpm_step_pct'] * 100)}% po {config['min_clean_reps']} czystych powtórzeniach; "
                   "nowe tempo liczy się dopiero po teście na zimno następnego dnia",
            "end": "log: BPM, czyste powtórzenia, ocena 1–5, napięcie 1–5, notatka",
        },
        "active_paths_without_exercises": [s["path_id"] for s in slots if s.get("needs_exercises")],
    }
