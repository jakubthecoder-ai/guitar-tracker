"""Human/LLM-readable views (markdown + YAML frontmatter) regenerated from derived state. Never edited by hand."""

import json
from pathlib import Path

from .config import AXES
from .store import atomic_write

HEADER = "<!-- GENEROWANE przez gt z dziennika zdarzeń. Nie edytuj ręcznie: zmiany przez `gt`. -->\n"

AXIS_PL = {
    "technique-picking": "Technika: kostkowanie",
    "technique-legato": "Technika: legato/tapping/sweep",
    "rhythm-timing": "Rytm i timing",
    "fretboard-theory": "Gryf i teoria",
    "ear": "Słuch",
    "repertoire": "Repertuar",
    "improvisation": "Improwizacja",
    "tone-gear": "Brzmienie i sprzęt",
}


def to_yaml(obj, indent: int = 0) -> str:
    """Minimal YAML emitter. Scalars are JSON-encoded, which is valid YAML."""
    pad = "  " * indent
    lines = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (dict, list)) and v:
                lines.append(f"{pad}{k}:")
                lines.append(to_yaml(v, indent + 1))
            else:
                lines.append(f"{pad}{k}: {json.dumps(v, ensure_ascii=False)}")
    elif isinstance(obj, list):
        for v in obj:
            if isinstance(v, (dict, list)) and v:
                inner = to_yaml(v, indent + 1).lstrip()
                lines.append(f"{pad}- {inner}")
            else:
                lines.append(f"{pad}- {json.dumps(v, ensure_ascii=False)}")
    else:
        lines.append(f"{pad}{json.dumps(obj, ensure_ascii=False)}")
    return "\n".join(lines)


def frontmatter_doc(meta: dict, body: str) -> str:
    return f"---\n{to_yaml(meta)}\n---\n{HEADER}\n{body.rstrip()}\n"


def render_all(home: Path, st: dict) -> None:
    atomic_write(home / "derived" / "state.json", json.dumps(st, ensure_ascii=False, indent=1, sort_keys=True))
    if st["profile"] is not None:
        atomic_write(home / "profile.md", render_profile(st))
    atomic_write(home / "profile_history.jsonl",
                 "".join(json.dumps(h, ensure_ascii=False, sort_keys=True) + "\n" for h in st["profile_history"]))
    for pid, path in st["paths"].items():
        d = home / "paths" / pid
        atomic_write(d / "path.md", render_path(path, st))
        if path.get("interview"):
            atomic_write(d / "interview.md", f"{HEADER}\n# Wywiad: {path['title']}\n\n{path['interview']}\n")
    for r in st["retros"]:
        target = home / "paths" / r["path_id"] / "retro" if r.get("path_id") else home / "retro"
        atomic_write(target / f"{r['week']}.md", f"{HEADER}\n# Retro {r['week']}\n\n{r['text']}\n")
    for eid, ex in st["exercises"].items():
        body = f"# {ex['title']}\n\n{ex.get('description', '')}\n"
        meta = {k: v for k, v in ex.items() if k not in ("history", "description")}
        atomic_write(home / "exercises" / f"{eid}.md", frontmatter_doc(meta, body))
    for sid, song in st["songs"].items():
        body = f"# {song['artist']} – {song['title']}\n\n{song.get('why', '')}\n"
        atomic_write(home / "songs" / f"{sid}.md", frontmatter_doc(song, body))
    for day, plan in st["plans"].items():
        atomic_write(home / "plans" / f"{day}.json", json.dumps(plan, ensure_ascii=False, indent=2))


def render_profile(st: dict) -> str:
    prof = st["profile"]
    meta = {k: v for k, v in prof.items() if k not in ("answers", "notes")}
    lines = ["# Profil gitarzysty", "", "| Oś | Poziom | Notatka |", "|---|---|---|"]
    for axis in AXES:
        a = prof.get("axes", {}).get(axis, {})
        lines.append(f"| {AXIS_PL[axis]} | {a.get('level') or '–'} | {a.get('note', '')} |")
    if st["pending_changes"]:
        lines += ["", "## Zmiany czekające na potwierdzenie", ""]
        for c in st["pending_changes"]:
            lines.append(f"- `{c['change_id']}` {c['field']} → {json.dumps(c['new'], ensure_ascii=False)}: "
                         f"{c['rationale']}")
    if prof.get("notes"):
        lines += ["", "## Notatki mentora", "", prof["notes"]]
    if prof.get("answers"):
        lines += ["", "## Odpowiedzi z wywiadu", ""]
        for a in prof["answers"]:
            lines.append(f"- **{a.get('q', '')}** {a.get('a', '')}")
    return frontmatter_doc(meta, "\n".join(lines))


def render_path(path: dict, st: dict) -> str:
    meta = {k: v for k, v in path.items() if k not in ("interview", "observations", "status_history")}
    ms = path["metric_state"]
    m = path["primary_metric"]
    lines = [f"# {path['title']}", "", f"**Cel:** {path['goal']}", "",
             f"**Metryka:** {m['type']} → {m['target']} {m.get('unit', '')} · teraz: {ms['current']} · "
             f"trend/tydz.: {ms['slope_per_week']} · projekcja: {ms['projection_at_deadline']} · ryzyko: {ms['risk']}",
             "", f"**Deadline:** {path['deadline']} ({ms['days_left']} dni) · status: {path['status']}", "",
             "## Kamienie milowe", ""]
    for mi in path["milestones"]:
        mark = "x" if mi.get("reached") else " "
        lines.append(f"- [{mark}] `{mi['id']}` {mi.get('desc', '')} (do {mi.get('due', '?')})")
    lines += ["", "## Ćwiczenia", ""]
    for eid in path["exercises"]:
        ex = st["exercises"][eid]
        lines.append(f"- `{eid}` {ex['title']} – stadium {ex['stage']}, czyste {ex['clean_bpm']}, "
                     f"kandydat {ex['candidate_bpm']}, cel {ex.get('bpm_target')}")
    if path["songs"]:
        lines += ["", "## Utwory", ""]
        for sid in path["songs"]:
            s = st["songs"][sid]
            lines.append(f"- `{sid}` {s['artist']} – {s['title']} ({s['status']})")
    return frontmatter_doc(meta, "\n".join(lines))
