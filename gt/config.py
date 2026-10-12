"""Default configuration. Every threshold lives here and can be overridden in GT_HOME/config.json."""

import copy
import json
import os
from datetime import date, datetime
from pathlib import Path

AXES = [
    "technique-picking",
    "technique-legato",
    "rhythm-timing",
    "fretboard-theory",
    "ear",
    "repertoire",
    "improvisation",
    "tone-gear",
]

METRIC_TYPES = ["bpm", "song_status", "minutes", "custom"]
STAGES = ["learn", "stabilise", "speed", "apply", "maintain"]
SONG_STATUSES = ["backlog", "learning", "polishing", "performance_ready", "maintenance"]
PATH_STATUSES = ["proposed", "active", "paused", "review", "done", "dropped"]
PRACTICE_TYPES = ["targeted", "runthrough", "jam", "new_material", "warmup", "cold_check"]

DEFAULTS = {
    "max_active_paths": 4,
    "paths_per_session": {"30": 2, "60": 3, "90": 4},
    "warmup_share": 0.10,
    "review_share": 0.15,
    "path_shares": {"1": [0.75], "2": [0.5, 0.25], "3": [0.4, 0.22, 0.13], "4": [0.33, 0.2, 0.12, 0.1]},
    "min_warmup_minutes": 5,
    "min_session_minutes": 20,
    "rotation_minutes": [3, 5],
    "microbreak_every_minutes": 20,
    "min_touch_days": 3,
    "min_clean_reps": 3,
    "bpm_step_pct": 0.04,
    "stabilise_threshold": 0.65,
    "review_intervals_days": [1, 3, 7, 14, 30],
    "volume_jump_limit": 0.20,
    "pain_lookback_days": 3,
    "trend_window_days": 28,
    "plateau_window_days": 21,
    "plateau_min_points": 6,
    "plateau_min_weekly_gain_pct": 0.01,
    "max_weekly_bpm_gain_pct": 0.08,
    "inactivity_days": 4,
    "skipped_sessions_ratio": 0.5,
    "priority_weights": {"1": 0.6, "2": 0.8, "3": 1.0, "4": 1.3, "5": 1.6},
    "language": "pl",
}


def gt_home() -> Path:
    return Path(os.environ.get("GT_HOME") or Path.home() / ".guitar-tracker").expanduser()


def load_config(home: Path) -> dict:
    cfg = copy.deepcopy(DEFAULTS)
    f = home / "config.json"
    if f.exists():
        cfg.update(json.loads(f.read_text(encoding="utf-8")))
    return cfg


def today() -> date:
    """GT_TODAY lets tests and simulations pin the calendar."""
    v = os.environ.get("GT_TODAY")
    return date.fromisoformat(v) if v else date.today()


def now_iso() -> str:
    v = os.environ.get("GT_NOW")
    if v:
        return v
    if os.environ.get("GT_TODAY"):
        return os.environ["GT_TODAY"] + "T12:00:00"
    return datetime.now().astimezone().isoformat(timespec="seconds")
