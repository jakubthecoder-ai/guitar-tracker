#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["mcp>=1.2,<2"]
# ///
"""Guitar-tracker MCP server: the same gt core exposed as MCP tools, prompts and resources.

For harnesses without shell access or subagents (Claude Desktop, claude.ai connectors, any MCP client).
Run: `uv run gt_mcp.py` (stdio). Data location: GT_HOME (default ~/.guitar-tracker).
"""

import json
import os
import subprocess
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

ROOT = Path(__file__).resolve().parent
SKILLS = ROOT / ".agents" / "skills"
AGENTS = ROOT / "agents"

mcp = FastMCP("guitar-tracker")


def gt(*args: str) -> dict:
    """Run the gt CLI and return its JSON result (errors are returned, not raised, so the model can react)."""
    env = dict(os.environ, PYTHONPATH=str(ROOT) + os.pathsep + os.environ.get("PYTHONPATH", ""))
    r = subprocess.run([sys.executable, "-m", "gt", "--source", "mcp", "--actor", "mcp", *args],
                       capture_output=True, text=True, env=env, cwd=ROOT, timeout=120)
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"ok": False, "error": (r.stdout + r.stderr).strip()[-2000:]}


def _j(obj) -> str:
    return obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False)


# --- state ------------------------------------------------------------------------
@mcp.tool()
def get_state(full: bool = False) -> dict:
    """Overview of the guitarist's state: profile, paths (risk, current/target, days since practice), open session,
    pending profile changes, open path proposals. full=True returns everything (exercises with BPM history etc.)."""
    return gt("state", *(["--full"] if full else []))


@mcp.tool()
def show_path(path_id: str) -> dict:
    """One path with its exercises (stage, clean/candidate BPM, history), songs and recent retros."""
    return gt("path", "show", path_id)


@mcp.tool()
def signals() -> dict:
    """Deterministic signals of progress and lack of progress (plateau, neglect, skipped sessions, deadline risk,
    health, stage readiness) for updating the living profile."""
    return gt("signals")


@mcp.tool()
def ingest_events() -> dict:
    """Import changes exported from the HTML report (inbox and ~/Downloads/gt-events-*.json). Idempotent."""
    return gt("ingest")


# --- profile -----------------------------------------------------------------------
@mcp.tool()
def init_profile(profile: dict, force: bool = False) -> dict:
    """Save the profile after the placement interview. Requires axes for all 8 taxonomy axes with level 1–5
    (see resource guitar-tracker://skill/gt-placement for the schema)."""
    return gt("profile", "init", "--from", _j(profile), *(["--force"] if force else []))


@mcp.tool()
def change_profile(changes: list[dict]) -> dict:
    """Propose profile changes: [{field, new, trigger, rationale, evidence?}]. Level (axes.*.level) and path.*
    changes wait for user confirmation; metrics apply immediately."""
    return gt("profile", "change", "--from", _j(changes))


@mcp.tool()
def confirm_profile_change(change_id: str, accept: bool = True) -> dict:
    """Accept or reject a pending profile change (only after the user decided)."""
    return gt("profile", "confirm" if accept else "reject", change_id)


# --- paths & exercises ---------------------------------------------------------------
@mcp.tool()
def propose_paths(proposals: list[dict]) -> dict:
    """Store path proposals from placement: [{title, goal, topic_axis, primary_metric?, rationale?}]."""
    return gt("path", "propose", "--from", _j(proposals))


@mcp.tool()
def check_path(spec: dict) -> dict:
    """Validate a path spec (one goal, one topic, deadline realism) without saving it."""
    return gt("path", "check", "--from", _j(spec))


@mcp.tool()
def create_path(spec: dict, force: bool = False) -> dict:
    """Create a path (one goal = one topic): title, goal, topic_axis, primary_metric{type,target,unit}, deadline,
    priority, baseline, milestones[{id,desc,due}], interview, exercises[]. force=True only after the user accepted
    the warnings returned by check_path."""
    return gt("path", "create", "--from", _j(spec), *(["--force"] if force else []))


@mcp.tool()
def update_path(path_id: str, action: str, value: str = "", reason: str = "", deadline: str = "") -> dict:
    """Change a path: action = pause | resume | close | drop | review | extend (needs deadline+reason) |
    priority (value 1–5) | milestone (value = milestone id) | metric (value = measured number)."""
    args = ["path", action, path_id] + ([value] if value else [])
    args += (["--reason", reason] if reason else []) + (["--deadline", deadline] if deadline else [])
    return gt(*args)


@mcp.tool()
def add_exercises(path_id: str, exercises: list[dict]) -> dict:
    """Add exercises to a path: [{title, technique, subdivision, bpm_start, bpm_target, stage, description}]."""
    return gt("exercise", "add", "--path", path_id, "--from", _j(exercises))


@mcp.tool()
def set_exercise_stage(exercise_id: str, stage: str, reason: str = "") -> dict:
    """Move an exercise to a stage: learn | stabilise | speed | apply | maintain (after the user agreed)."""
    return gt("exercise", "stage", exercise_id, stage, *(["--reason", reason] if reason else []))


# --- sessions ------------------------------------------------------------------------
@mcp.tool()
def plan_session(minutes: int = 60, paths: list[str] | None = None, ignore_volume_cap: bool = False) -> dict:
    """Deterministic session skeleton: which paths, minutes per slot, cold checks, next BPM per exercise,
    warnings (volume, pain, breaks). Fill the slots with exercises, interleave, then commit_plan."""
    args = ["plan", "--minutes", str(minutes)]
    if paths:
        args += ["--paths", ",".join(paths)]
    if ignore_volume_cap:
        args.append("--ignore-volume-cap")
    return gt(*args)


@mcp.tool()
def commit_plan(plan: dict) -> dict:
    """Save the agreed plan: {minutes, rationale, blocks:[{start_min, minutes, kind: warmup|path|review|music|break,
    title, path_id?, exercise_id?, song_id?, bpm?, cue?}]}."""
    return gt("plan", "commit", "--from", _j(plan))


@mcp.tool()
def start_session(minutes: int | None = None) -> dict:
    """Open a practice session."""
    return gt("session", "start", *(["--minutes", str(minutes)] if minutes else []))


@mcp.tool()
def log_items(items: list[dict]) -> dict:
    """Log practice: [{exercise_id|song_id|path_id, practice_type: targeted|new_material|runthrough|jam|warmup,
    minutes, bpm?, clean_reps?, max_bpm_burst?, rating 1–5?, tension 1–5?, note?}]. Never log estimates as data."""
    return gt("session", "log", "--from", _j(items))


@mcp.tool()
def cold_check(exercise_id: str, bpm: int, clean: bool = True, note: str = "") -> dict:
    """Record a cold check (first attempt of the day, without warming up that exercise). Only cold checks confirm
    clean tempo."""
    return gt("session", "cold-check", exercise_id, "--bpm", str(bpm), *([] if clean else ["--not-clean"]),
              *(["--note", note] if note else []))


@mcp.tool()
def end_session(rating: int | None = None, note: str = "") -> dict:
    """Close the session; returns stage suggestions and signals for the profile."""
    return gt("session", "end", *(["--rating", str(rating)] if rating else []), *(["--note", note] if note else []))


@mcp.tool()
def report_pain(location: str, severity: int) -> dict:
    """Record pain (1–5). Next sessions become light; red flags need a specialist."""
    return gt("session", "pain", "--note", location, "--rating", str(severity))


# --- songs -----------------------------------------------------------------------------
@mcp.tool()
def suggest_songs(path_id: str = "", technique: str = "", level: int | None = None) -> dict:
    """Comfort / target / stretch song candidates from the curated seed, matched to the path axis and profile level."""
    args = ["song", "suggest"] + (["--path", path_id] if path_id else []) + (["--technique", technique] if technique else [])
    return gt(*args, *(["--level", str(level)] if level else []))


@mcp.tool()
def verify_song(artist: str = "", title: str = "", song_id: str = "") -> dict:
    """Check a song exists (Songsterr, MusicBrainz): tab link, tuning, guitar-part difficulty 1–8. With song_id the
    result is saved on the song."""
    return gt("song", "verify", song_id) if song_id else gt("song", "verify", "--artist", artist, "--title", title)


@mcp.tool()
def add_songs(songs: list[dict]) -> dict:
    """Add songs: [{seed_id} or {artist, title, role, techniques, why}, path_id?, status?, sections?]."""
    return gt("song", "add", "--from", _j(songs))


@mcp.tool()
def set_song_status(song_id: str, status: str) -> dict:
    """status: backlog | learning | polishing | performance_ready | maintenance."""
    return gt("song", "status", song_id, status)


# --- report -----------------------------------------------------------------------------
@mcp.tool()
def write_mentor_note(text: str, scope: str = "weekly") -> dict:
    """Mentor commentary shown in the HTML report."""
    return gt("note", text, "--scope", scope)


@mcp.tool()
def render_report() -> dict:
    """Regenerate the interactive HTML report; returns its file path (open it in a browser)."""
    return gt("report")


@mcp.tool()
def write_path_retro(path_id: str, text: str) -> dict:
    """Save the weekly retro text for one path."""
    return gt("path", "retro", path_id, "--from", text)


# --- resources ---------------------------------------------------------------------------
@mcp.resource("guitar-tracker://skill/{name}")
def skill(name: str) -> str:
    """Skill instructions (gt-core, gt-placement, gt-new-path, gt-session, gt-log, gt-report, gt-retro, gt-songs)."""
    return (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")


@mcp.resource("guitar-tracker://reference/{skill_name}/{file}")
def reference(skill_name: str, file: str) -> str:
    """Reference files of a skill, e.g. gt-core/contracts.md, gt-placement/placement-questions.md."""
    return (SKILLS / skill_name / "references" / file).read_text(encoding="utf-8")


@mcp.resource("guitar-tracker://role/{name}")
def role(name: str) -> str:
    """Role prompt (orchestrator, path-coach, placement-interviewer, path-interviewer, song-scout, profile-keeper,
    report-builder). Without subagents, perform the role inline following this prompt."""
    return (AGENTS / f"{name}.md").read_text(encoding="utf-8")


# --- prompts -------------------------------------------------------------------------------
INLINE = """
## Tryb bez subagentów (MCP)
Nie masz shella ani subagentów: zamiast komend `gt …` używasz narzędzi MCP guitar-trackera (nazwy odpowiadają
komendom: plan_session, commit_plan, log_items, create_path…). Role subagentów wykonujesz sam, po kolei,
trzymając się ich promptów (zasób `guitar-tracker://role/<nazwa>`) i kontraktów
(`guitar-tracker://reference/gt-core/contracts.md`). Liczby wyłącznie z narzędzi. Pytania zadawaj użytkownikowi
bezpośrednio (max ~6 naraz).
"""


def _persona(*parts: str) -> str:
    return "\n\n".join([(AGENTS / "mentor.md").read_text(encoding="utf-8"), INLINE, *parts])


@mcp.prompt()
def mentor() -> str:
    """Start a conversation with the guitar mentor (routing, state check)."""
    return _persona(role("orchestrator"), "Zacznij od get_state i ingest_events, potem przywitaj się i zaproponuj "
                    "następny krok.")


@mcp.prompt()
def placement() -> str:
    """Placement interview: profile L1–L5 in 8 axes and 2–4 path proposals."""
    return _persona(role("placement-interviewer"), skill("gt-placement"),
                    reference("gt-placement", "placement-questions.md"))


@mcp.prompt()
def new_path(goal: str = "") -> str:
    """Create a new path (one goal = one topic) via a short deep-dive interview."""
    return _persona(role("path-interviewer"), skill("gt-new-path"),
                    reference("gt-new-path", "deep-dive-questions.md"),
                    f"Cel podany przez użytkownika: {goal}" if goal else "Zapytaj o cel.")


@mcp.prompt()
def practice(minutes: int = 45) -> str:
    """Plan and run a practice session that interleaves the selected paths."""
    return _persona(role("orchestrator"), skill("gt-session"), role("path-coach"),
                    f"Użytkownik ma {minutes} minut. Zacznij od plan_session(minutes={minutes}).")


@mcp.prompt()
def retro() -> str:
    """Weekly retro: signals, path retros, living-profile updates, mentor note and report."""
    return _persona(skill("gt-retro"), role("path-coach"), role("profile-keeper"), role("report-builder"))


if __name__ == "__main__":
    mcp.run()
