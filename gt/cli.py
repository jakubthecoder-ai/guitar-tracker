"""`gt` command line. Every command prints JSON to stdout; exit 0 = ok, 1 = validation error, 2 = usage error."""

import argparse
import json
import shutil
import sys
from datetime import date
from pathlib import Path

from . import config as C
from .derive import derive
from .events import make_event, new_id, validate_event
from .paths import check_path, slugify, unique_id
from .schedule import build_plan
from .store import Store
from .views import render_all


class GtError(Exception):
    def __init__(self, message, details=None, code=1):
        super().__init__(message)
        self.details, self.code = details, code


# --- helpers -------------------------------------------------------------------
def out(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))


def read_json_arg(value: str):
    if value == "-":
        return json.load(sys.stdin)
    if value.lstrip()[:1] in ("{", "["):
        return json.loads(value)  # inline JSON
    return json.loads(Path(value).read_text(encoding="utf-8"))


class Ctx:
    def __init__(self, args):
        self.store = Store(C.gt_home())
        self.source = getattr(args, "source", "cli") or "cli"
        self.actor = getattr(args, "actor", "user") or "user"
        self.today = date.fromisoformat(args.date) if getattr(args, "date", None) else C.today()

    def require_init(self):
        if not self.store.is_initialized():
            raise GtError(f"GT_HOME nie zainicjalizowany ({self.store.home}). Uruchom `gt init`.", code=2)

    def state(self) -> dict:
        return derive(self.store.load_events(), self.store.config, self.today)

    def ev(self, etype, payload):
        return make_event(etype, payload, source=self.source, actor=self.actor)

    def commit(self, events: list, git_message: str | None = None) -> dict:
        self.require_init()
        with self.store.lock():
            res = self.store.append_events(events)
            st = self.state()
            render_all(self.store.home, st)
            if git_message:
                res["git"] = self.store.commit(git_message)
        return res, st


# --- commands ------------------------------------------------------------------
def cmd_init(ctx, args):
    out({"ok": True, **ctx.store.init(git=not args.no_git)})


def cmd_profile(ctx, args):
    ctx.require_init()
    st = ctx.state()
    if args.action == "show":
        return out({"ok": True, "profile": st["profile"], "pending_changes": st["pending_changes"]})
    if args.action == "history":
        return out({"ok": True, "history": st["profile_history"]})
    if args.action == "init":
        data = read_json_arg(args.input)
        if st["profile"] is not None and not args.force:
            raise GtError("Profil już istnieje. Zmiany przez `gt profile change`, reset przez --force.")
        res, _ = ctx.commit([ctx.ev("profile_initialized", data)], "profil: inicjalizacja")
        return out({"ok": True, **res})
    if args.action == "change":
        data = read_json_arg(args.input)
        items = data if isinstance(data, list) else [data]
        events = []
        for it in items:
            field = it["field"]
            needs = it.get("requires_confirmation")
            if needs is None:
                needs = field.startswith("path.") or (field.startswith("axes.") and field.endswith(".level"))
            events.append(ctx.ev("profile_changed", {
                "change_id": it.get("change_id") or new_id("ch-"), "field": field, "new": it["new"],
                "trigger": it["trigger"], "rationale": it["rationale"], "evidence": it.get("evidence", []),
                "requires_confirmation": bool(needs)}))
        res, st = ctx.commit(events, "profil: zmiany")
        return out({"ok": True, **res, "pending": [c["change_id"] for c in st["pending_changes"]]})
    if args.action in ("confirm", "reject"):
        if not args.change_id:
            raise GtError("Podaj change_id", code=2)
        pending = {c["change_id"] for c in st["pending_changes"]}
        if args.change_id not in pending:
            raise GtError(f"Brak oczekującej zmiany '{args.change_id}'", {"pending": sorted(pending)})
        res, _ = ctx.commit([ctx.ev("profile_change_confirmed", {"change_id": args.change_id,
                                                                  "accepted": args.action == "confirm"})],
                            f"profil: {args.action} {args.change_id}")
        return out({"ok": True, **res})


def cmd_path(ctx, args):
    ctx.require_init()
    st = ctx.state()
    a = args.action
    if a == "list":
        rows = [{"path_id": p["path_id"], "title": p["title"], "status": p["status"], "priority": p["priority"],
                 "deadline": p["deadline"], "topic_axis": p["topic_axis"], "risk": p["metric_state"]["risk"],
                 "current": p["metric_state"]["current"], "target": p["metric_state"]["target"],
                 "days_since_touch": p["days_since_touch"]}
                for p in st["paths"].values() if not args.status or p["status"] == args.status]
        props = [p for p in st["proposals"].values() if p["status"] == "open"]
        return out({"ok": True, "paths": rows, "open_proposals": props})
    if a == "propose":
        data = read_json_arg(args.input)
        items = data if isinstance(data, list) else [data]
        events = [ctx.ev("path_proposed", dict(it, proposal_id=it.get("proposal_id") or new_id("prop-")))
                  for it in items]
        res, _ = ctx.commit(events, "ścieżki: propozycje")
        return out({"ok": True, **res, "proposal_ids": [e["payload"]["proposal_id"] for e in events]})
    if a == "check":
        spec = read_json_arg(args.input)
        return out({"ok": True, **check_path(spec, st, ctx.store.config, ctx.today)})
    if a == "create":
        spec = read_json_arg(args.input)
        chk = check_path(spec, st, ctx.store.config, ctx.today)
        if chk["errors"]:
            raise GtError("Ścieżka odrzucona", chk)
        if chk["warnings"] and not args.force:
            raise GtError("Ostrzeżenia: potwierdź z użytkownikiem i powtórz z --force", chk)
        pid = unique_id(spec.get("path_id") or slugify(spec["title"]), st["paths"])
        payload = {k: spec.get(k) for k in ("title", "goal", "topic_axis", "primary_metric", "deadline", "priority",
                                            "milestones", "min_touch_days", "created_from", "interview",
                                            "baseline", "proposal_id")}
        payload.update(path_id=pid, status="paused" if chk["queued"] else "active")
        events = [ctx.ev("path_created", payload)]
        for i, ex in enumerate(spec.get("exercises", [])):
            events.append(ctx.ev("exercise_created", _exercise_payload(ex, pid, st, i)))
        res, _ = ctx.commit(events, f"ścieżka: {pid}")
        return out({"ok": True, "path_id": pid, "status": payload["status"], "warnings": chk["warnings"],
                    "queued_reason": "limit aktywnych ścieżek" if chk["queued"] else None, **res})
    path = _get_path(st, args.path_id)
    if a == "show":
        exs = {e: st["exercises"][e] for e in path["exercises"]}
        songs = {s: st["songs"][s] for s in path["songs"]}
        retros = [r for r in st["retros"] if r.get("path_id") == path["path_id"]][-3:]
        return out({"ok": True, "path": path, "exercises": exs, "songs": songs, "recent_retros": retros})
    if a in ("pause", "resume", "close", "drop", "review"):
        status = {"pause": "paused", "resume": "active", "close": "done", "drop": "dropped", "review": "review"}[a]
        if status == "active" and len(st["active_paths"]) >= ctx.store.config["max_active_paths"] \
                and path["status"] != "active" and not args.force:
            raise GtError("Limit aktywnych ścieżek osiągnięty. Zapauzuj inną albo użyj --force.",
                          {"active": st["active_paths"]})
        ev = ctx.ev("path_status_changed", {"path_id": path["path_id"], "status": status, "reason": args.reason})
        res, _ = ctx.commit([ev], f"ścieżka {path['path_id']}: {status}")
        return out({"ok": True, **res})
    if a == "extend":
        if not args.deadline or not args.reason:
            raise GtError("extend wymaga --deadline i --reason", code=2)
        ev = ctx.ev("deadline_changed", {"path_id": path["path_id"], "deadline": args.deadline, "reason": args.reason})
        res, _ = ctx.commit([ev], f"ścieżka {path['path_id']}: deadline {args.deadline}")
        return out({"ok": True, **res})
    if a == "priority":
        ev = ctx.ev("path_priority_changed", {"path_id": path["path_id"], "priority": int(args.value),
                                              "reason": args.reason})
        res, _ = ctx.commit([ev], f"ścieżka {path['path_id']}: priorytet")
        return out({"ok": True, **res})
    if a == "milestone":
        ids = [m["id"] for m in path["milestones"]]
        if args.value not in ids:
            raise GtError(f"Nieznany kamień milowy. Dostępne: {ids}")
        ev = ctx.ev("milestone_reached", {"path_id": path["path_id"], "milestone_id": args.value, "note": args.reason})
        res, _ = ctx.commit([ev], f"ścieżka {path['path_id']}: kamień {args.value}")
        return out({"ok": True, **res})
    if a == "metric":
        ev = ctx.ev("metric_recorded", {"path_id": path["path_id"], "value": float(args.value), "note": args.reason})
        res, _ = ctx.commit([ev])
        return out({"ok": True, **res})
    if a == "retro":
        text = sys.stdin.read() if args.input in (None, "-") else (
            Path(args.input).read_text(encoding="utf-8") if len(args.input) < 255 and Path(args.input).is_file()
            else args.input)
        week = ctx.today.strftime("%G-W%V")
        res, _ = ctx.commit([ctx.ev("retro_recorded", {"path_id": path["path_id"], "week": week, "text": text})],
                            f"retro {path['path_id']} {week}")
        return out({"ok": True, "week": week, **res})


def _get_path(st, pid):
    if not pid:
        raise GtError("Podaj path_id", code=2)
    if pid not in st["paths"]:
        raise GtError(f"Nieznana ścieżka '{pid}'", {"paths": sorted(st["paths"])})
    return st["paths"][pid]


def _exercise_payload(ex: dict, path_id: str, st: dict, i: int = 0) -> dict:
    eid = ex.get("exercise_id") or unique_id(f"{path_id}-{slugify(ex['title'])}"[:50], st["exercises"])
    p = {k: ex.get(k) for k in ("title", "technique", "subdivision", "bpm_start", "bpm_target", "step_pct",
                                "description", "stage", "primary")}
    p.update(exercise_id=eid, path_id=path_id)
    return p


def cmd_exercise(ctx, args):
    ctx.require_init()
    st = ctx.state()
    if args.action == "list":
        rows = [e for e in st["exercises"].values() if not args.path_id or e["path_id"] == args.path_id]
        return out({"ok": True, "exercises": rows})
    if args.action == "add":
        data = read_json_arg(args.input)
        items = data if isinstance(data, list) else [data]
        events = []
        for i, ex in enumerate(items):
            pid = ex.get("path_id") or args.path_id
            _get_path(st, pid)
            payload = _exercise_payload(ex, pid, st, i)
            st["exercises"][payload["exercise_id"]] = {}  # reserve id within batch
            events.append(ctx.ev("exercise_created", payload))
        res, _ = ctx.commit(events, "ćwiczenia: nowe")
        return out({"ok": True, **res, "exercise_ids": [e["payload"]["exercise_id"] for e in events]})
    if args.action == "stage":
        if args.exercise_id not in st["exercises"]:
            raise GtError(f"Nieznane ćwiczenie '{args.exercise_id}'")
        ev = ctx.ev("exercise_stage_changed", {"exercise_id": args.exercise_id, "stage": args.stage,
                                               "reason": args.reason})
        res, _ = ctx.commit([ev])
        return out({"ok": True, **res})


def cmd_session(ctx, args):
    ctx.require_init()
    st = ctx.state()
    a = args.action
    if a == "start":
        if st["open_session"]:
            return out({"ok": True, "session_id": st["open_session"], "already_open": True})
        sid = new_id("s-")
        plan_date = ctx.today.isoformat() if ctx.today.isoformat() in st["plans"] else None
        res, _ = ctx.commit([ctx.ev("session_started", {"session_id": sid, "minutes_planned": int(args.minutes) if args.minutes else None,
                                                        "plan_date": plan_date})])
        return out({"ok": True, "session_id": sid, **res})
    if a == "log":
        data = read_json_arg(args.input) if args.input else {}
        items = data if isinstance(data, list) else [data]
        if not args.input:
            items = [{k: v for k, v in {"path_id": args.path_id, "exercise_id": args.exercise_id,
                                        "song_id": args.song_id, "practice_type": args.type,
                                        "minutes": args.minutes, "bpm": args.bpm, "clean_reps": args.clean_reps,
                                        "max_bpm_burst": args.burst, "rating": args.rating,
                                        "tension": args.tension, "note": args.note}.items() if v is not None}]
        events = []
        for it in items:
            it.setdefault("practice_type", "targeted")
            if st["open_session"]:
                it.setdefault("session_id", st["open_session"])
            for ref, coll in (("exercise_id", "exercises"), ("song_id", "songs"), ("path_id", "paths")):
                if it.get(ref) and it[ref] not in st[coll]:
                    raise GtError(f"Nieznane {ref} '{it[ref]}'")
            if not any(it.get(r) for r in ("exercise_id", "song_id", "path_id")) and it["practice_type"] != "warmup":
                raise GtError("Log wymaga exercise_id, song_id albo path_id (chyba że practice_type=warmup)")
            events.append(ctx.ev("item_logged", it))
        res, _ = ctx.commit(events)
        return out({"ok": True, **res, "session_id": st["open_session"]})
    if a == "cold-check":
        if args.exercise_id not in st["exercises"]:
            raise GtError(f"Nieznane ćwiczenie '{args.exercise_id}'")
        ev = ctx.ev("cold_check", {"exercise_id": args.exercise_id, "bpm": args.bpm, "clean": not args.not_clean,
                                   "session_id": st["open_session"], "note": args.note})
        res, st2 = ctx.commit([ev])
        ex = st2["exercises"][args.exercise_id]
        return out({"ok": True, **res, "clean_bpm": ex["clean_bpm"], "suggested_stage": ex["suggested_stage"]})
    if a == "end":
        if not st["open_session"]:
            raise GtError("Brak otwartej sesji")
        sid = st["open_session"]
        res, st2 = ctx.commit([ctx.ev("session_ended", {"session_id": sid, "rating": args.rating, "note": args.note})],
                              f"sesja {ctx.today.isoformat()}")
        sess = next(s for s in st2["sessions"] if s["session_id"] == sid)
        return out({"ok": True, **res, "session": sess,
                    "stage_suggestions": {e["exercise_id"]: e["suggested_stage"] for e in st2["exercises"].values()
                                          if e["suggested_stage"]}})
    if a == "pain":
        ev = ctx.ev("pain_reported", {"location": args.note or "nieokreślone", "severity": args.rating or 3})
        res, _ = ctx.commit([ev], "ból zgłoszony")
        return out({"ok": True, **res, "advice": "Przerwij granie wywołujące ból. Ból ostry, narastający, drętwienie "
                                                 "lub utrata kontroli palców → konsultacja ze specjalistą."})


def cmd_song(ctx, args):
    ctx.require_init()
    st = ctx.state()
    if args.action == "list":
        return out({"ok": True, "songs": list(st["songs"].values())})
    if args.action == "add":
        data = read_json_arg(args.input)
        items = data if isinstance(data, list) else [data]
        events = []
        for s in items:
            sid = s.get("song_id") or unique_id(slugify(f"{s['artist']}-{s['title']}"), st["songs"])
            st["songs"][sid] = {}
            if s.get("path_id") and s["path_id"] not in st["paths"]:
                raise GtError(f"Nieznana ścieżka '{s['path_id']}'")
            events.append(ctx.ev("song_added", dict(s, song_id=sid)))
        res, _ = ctx.commit(events, "utwory: nowe")
        return out({"ok": True, **res, "song_ids": [e["payload"]["song_id"] for e in events]})
    if args.action == "status":
        if args.song_id not in st["songs"]:
            raise GtError(f"Nieznany utwór '{args.song_id}'")
        res, _ = ctx.commit([ctx.ev("song_status_changed", {"song_id": args.song_id, "status": args.status,
                                                            "note": args.note})], f"utwór {args.song_id}: {args.status}")
        return out({"ok": True, **res})


def cmd_plan(ctx, args):
    ctx.require_init()
    st = ctx.state()
    if args.action == "commit":
        data = read_json_arg(args.input)
        data.setdefault("date", ctx.today.isoformat())
        if not data.get("blocks"):
            raise GtError("Plan wymaga niepustej listy 'blocks'")
        for i, b in enumerate(data["blocks"]):
            if "minutes" not in b or "kind" not in b:
                raise GtError(f"Blok {i}: wymagane 'kind' i 'minutes'")
        data.setdefault("minutes", int(sum(b["minutes"] for b in data["blocks"])))
        res, _ = ctx.commit([ctx.ev("plan_committed", data)], f"plan {data['date']}")
        return out({"ok": True, **res, "date": data["date"]})
    if args.action == "show":
        return out({"ok": True, "plan": st["plans"].get(ctx.today.isoformat())})
    only = args.paths.split(",") if args.paths else None
    out({"ok": True, **build_plan(st, ctx.store.config, ctx.today, args.minutes, only, args.ignore_volume_cap)})


def cmd_note(ctx, args):
    if args.input in (None, "-"):
        text = sys.stdin.read()
    elif len(args.input) < 255 and "\n" not in args.input and Path(args.input).is_file():
        text = Path(args.input).read_text(encoding="utf-8")
    else:
        text = args.input
    res, _ = ctx.commit([ctx.ev("mentor_note", {"text": text.strip(), "scope": args.scope})])
    out({"ok": True, **res})


def cmd_ingest(ctx, args):
    ctx.require_init()
    files = [Path(f) for f in args.files]
    if not files:
        files = sorted((ctx.store.home / "inbox").glob("*.json"))
        dl = Path.home() / "Downloads"
        if dl.exists():
            files += sorted(dl.glob("gt-events-*.json"))
    report = {"files": [], "added": 0, "skipped_duplicates": 0, "rejected": []}
    events = []
    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        items = data.get("events", []) if isinstance(data, dict) else data
        good = 0
        for ev in items:
            errs = validate_event(ev)
            if errs:
                report["rejected"].append({"file": str(f), "id": ev.get("id"), "errors": errs})
            else:
                events.append(ev)
                good += 1
        report["files"].append({"file": str(f), "events": good})
    if events:
        res, _ = ctx.commit(events, f"ingest {len(events)} zdarzeń")
        report["added"], report["skipped_duplicates"] = len(res["added"]), len(res["skipped_duplicates"])
    if not args.keep:
        done = ctx.store.home / "inbox" / "processed"
        done.mkdir(parents=True, exist_ok=True)
        for f in files:
            if f.exists() and f.parent.resolve() in ((ctx.store.home / "inbox").resolve(),
                                                     (Path.home() / "Downloads").resolve()):
                shutil.move(str(f), done / f.name)
    out({"ok": not report["rejected"], **report})
    if report["rejected"]:
        raise SystemExit(1)


def cmd_derive(ctx, args):
    ctx.require_init()
    with ctx.store.lock():
        st = ctx.state()
        render_all(ctx.store.home, st)
    out({"ok": True, "events": st["event_count"], "paths": len(st["paths"]), "exercises": len(st["exercises"])})


def cmd_state(ctx, args):
    ctx.require_init()
    st = ctx.state()
    if args.full:
        return out(st)
    out({"ok": True, "as_of": st["as_of"], "profile_initialized": st["profile"] is not None,
         "open_session": st["open_session"], "days_since_practice": st["days_since_practice"],
         "volume": st["volume"], "pending_changes": len(st["pending_changes"]),
         "open_proposals": [p["proposal_id"] for p in st["proposals"].values() if p["status"] == "open"],
         "paths": {pid: {"title": p["title"], "status": p["status"], "risk": p["metric_state"]["risk"],
                         "current": p["metric_state"]["current"], "target": p["metric_state"]["target"],
                         "deadline": p["deadline"], "days_since_touch": p["days_since_touch"],
                         "neglected": p["neglected"], "exercises": len(p["exercises"])}
                   for pid, p in st["paths"].items()}})


def cmd_validate(ctx, args):
    ctx.require_init()
    problems, ids = [], set()
    for ev in ctx.store.load_events():
        for e in validate_event(ev):
            problems.append({"id": ev.get("id"), "error": e})
        if ev["id"] in ids:
            problems.append({"id": ev["id"], "error": "duplikat id"})
        ids.add(ev["id"])
    st = ctx.state()
    for eid, ex in st["exercises"].items():
        if ex["path_id"] not in st["paths"]:
            problems.append({"id": eid, "error": f"ćwiczenie wskazuje nieznaną ścieżkę {ex['path_id']}"})
    out({"ok": not problems, "events": len(ids), "problems": problems})
    if problems:
        raise SystemExit(1)


def cmd_report(ctx, args):
    from .report import write_report
    ctx.require_init()
    st = ctx.state()
    path = write_report(ctx.store, st, ctx.today, Path(args.out) if args.out else None)
    if args.open:
        import webbrowser
        webbrowser.open(path.as_uri())
    out({"ok": True, "report": str(path)})


def cmd_serve(ctx, args):
    from .serve import serve
    ctx.require_init()
    serve(ctx, args.port, args.open)


# --- parser --------------------------------------------------------------------
def build_parser():
    def common(parser, suppress):
        d = (lambda v: argparse.SUPPRESS) if suppress else (lambda v: v)
        parser.add_argument("--date", default=d(None), help="Nadpisz dzisiejszą datę (RRRR-MM-DD)")
        parser.add_argument("--source", choices=["cli", "mcp", "html", "agent", "audio"], default=d("cli"))
        parser.add_argument("--actor", default=d("user"), help="Kto zapisuje, np. user, path-coach, orchestrator")

    p = argparse.ArgumentParser(prog="gt", description="Guitar tracker – deterministyczny rdzeń stanu.")
    common(p, False)
    shared = argparse.ArgumentParser(add_help=False)
    common(shared, True)
    _sub = p.add_subparsers(dest="cmd", required=True)

    class Sub:
        def add_parser(self, name, **kw):
            return _sub.add_parser(name, parents=[shared], **kw)

    sub = Sub()

    s = sub.add_parser("init")
    s.add_argument("--no-git", action="store_true")
    s.set_defaults(fn=cmd_init)

    s = sub.add_parser("profile")
    s.add_argument("action", choices=["show", "init", "change", "confirm", "reject", "history"])
    s.add_argument("change_id", nargs="?")
    s.add_argument("--from", dest="input", default="-")
    s.add_argument("--force", action="store_true")
    s.set_defaults(fn=cmd_profile)

    s = sub.add_parser("path")
    s.add_argument("action", choices=["list", "propose", "check", "create", "show", "pause", "resume", "close", "drop",
                                      "review", "extend", "priority", "milestone", "metric", "retro"])
    s.add_argument("path_id", nargs="?")
    s.add_argument("value", nargs="?", help="priorytet / id kamienia / wartość metryki")
    s.add_argument("--from", dest="input", default="-")
    s.add_argument("--status")
    s.add_argument("--deadline")
    s.add_argument("--reason")
    s.add_argument("--force", action="store_true")
    s.set_defaults(fn=cmd_path)

    s = sub.add_parser("exercise")
    s.add_argument("action", choices=["list", "add", "stage"])
    s.add_argument("exercise_id", nargs="?")
    s.add_argument("stage", nargs="?", choices=C.STAGES)
    s.add_argument("--path", dest="path_id")
    s.add_argument("--from", dest="input", default="-")
    s.add_argument("--reason")
    s.set_defaults(fn=cmd_exercise)

    s = sub.add_parser("session")
    s.add_argument("action", choices=["start", "log", "cold-check", "end", "pain"])
    s.add_argument("exercise_id", nargs="?")
    s.add_argument("--from", dest="input")
    s.add_argument("--path", dest="path_id")
    s.add_argument("--exercise", dest="exercise_id_opt")
    s.add_argument("--song", dest="song_id")
    s.add_argument("--type", choices=C.PRACTICE_TYPES)
    s.add_argument("--minutes", type=float)
    s.add_argument("--bpm", type=int)
    s.add_argument("--clean-reps", type=int)
    s.add_argument("--burst", type=int)
    s.add_argument("--rating", type=int)
    s.add_argument("--tension", type=int)
    s.add_argument("--not-clean", action="store_true")
    s.add_argument("--note")
    s.set_defaults(fn=cmd_session)

    s = sub.add_parser("song")
    s.add_argument("action", choices=["list", "add", "status"])
    s.add_argument("song_id", nargs="?")
    s.add_argument("status", nargs="?", choices=C.SONG_STATUSES)
    s.add_argument("--from", dest="input", default="-")
    s.add_argument("--note")
    s.set_defaults(fn=cmd_song)

    s = sub.add_parser("plan")
    s.add_argument("action", nargs="?", choices=["build", "commit", "show"], default="build")
    s.add_argument("--minutes", type=int, default=60)
    s.add_argument("--paths")
    s.add_argument("--ignore-volume-cap", action="store_true", help="Tylko na wyraźne życzenie użytkownika")
    s.add_argument("--from", dest="input", default="-")
    s.set_defaults(fn=cmd_plan)

    s = sub.add_parser("note", help="Komentarz mentora (trafia do raportu)")
    s.add_argument("input", nargs="?", default="-")
    s.add_argument("--scope", default="general")
    s.set_defaults(fn=cmd_note)

    s = sub.add_parser("ingest")
    s.add_argument("files", nargs="*")
    s.add_argument("--keep", action="store_true", help="Nie przenoś przetworzonych plików")
    s.set_defaults(fn=cmd_ingest)

    sub.add_parser("derive").set_defaults(fn=cmd_derive)
    s = sub.add_parser("state")
    s.add_argument("--full", action="store_true")
    s.set_defaults(fn=cmd_state)
    sub.add_parser("validate").set_defaults(fn=cmd_validate)

    s = sub.add_parser("report")
    s.add_argument("--out")
    s.add_argument("--open", action="store_true")
    s.set_defaults(fn=cmd_report)

    s = sub.add_parser("serve")
    s.add_argument("--port", type=int, default=8765)
    s.add_argument("--open", action="store_true")
    s.set_defaults(fn=cmd_serve)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    if getattr(args, "exercise_id_opt", None):
        args.exercise_id = args.exercise_id_opt
    if args.date:
        import os
        date.fromisoformat(args.date)
        os.environ["GT_TODAY"] = args.date
        os.environ.pop("GT_NOW", None)
    ctx = Ctx(args)
    try:
        args.fn(ctx, args)
    except GtError as e:
        out({"ok": False, "error": str(e), "details": e.details})
        sys.exit(e.code)
    except (ValueError, KeyError, json.JSONDecodeError) as e:
        out({"ok": False, "error": f"{type(e).__name__}: {e}"})
        sys.exit(1)
