"""File storage: append-only JSONL event log, atomic writes, lock, git commits."""

import fcntl
import json
import os
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path

from .config import load_config

GITIGNORE = "derived/\ncache/\n.lock\ninbox/processed/\ndrafts/\n"


class Store:
    def __init__(self, home: Path):
        self.home = Path(home)
        self.events_dir = self.home / "events"

    # --- setup -------------------------------------------------------------
    def is_initialized(self) -> bool:
        return self.events_dir.is_dir()

    def init(self, git: bool = True) -> dict:
        for d in ["events", "paths", "exercises", "songs", "plans", "recordings", "inbox", "drafts", "derived", "reports"]:
            (self.home / d).mkdir(parents=True, exist_ok=True)
        if not (self.home / "config.json").exists():
            atomic_write(self.home / "config.json", "{}\n")
        if not (self.home / ".gitignore").exists():
            atomic_write(self.home / ".gitignore", GITIGNORE)
        git_status = "skipped"
        if git and not (self.home / ".git").exists():
            r = subprocess.run(["git", "init", "-q"], cwd=self.home, capture_output=True)
            git_status = "initialized" if r.returncode == 0 else "unavailable"
        return {"home": str(self.home), "git": git_status}

    @property
    def config(self) -> dict:
        return load_config(self.home)

    # --- lock ----------------------------------------------------------------
    @contextmanager
    def lock(self):
        self.home.mkdir(parents=True, exist_ok=True)
        with open(self.home / ".lock", "w") as fh:
            fcntl.flock(fh, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(fh, fcntl.LOCK_UN)

    # --- events ------------------------------------------------------------
    def load_events(self) -> list:
        events = []
        if not self.events_dir.exists():
            return events
        for f in sorted(self.events_dir.glob("*.jsonl")):
            for line in f.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    events.append(json.loads(line))
        # stable sort keeps file order for equal timestamps
        events.sort(key=lambda e: e["ts"])
        return events

    def append_events(self, new_events: list) -> dict:
        """Append events, skipping ids already present. Caller must hold the lock."""
        existing = {e["id"] for e in self.load_events()}
        added, skipped = [], []
        for ev in new_events:
            if ev["id"] in existing:
                skipped.append(ev["id"])
                continue
            existing.add(ev["id"])
            f = self.events_dir / f"{ev['ts'][:7]}.jsonl"
            f.parent.mkdir(parents=True, exist_ok=True)
            with open(f, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(ev, ensure_ascii=False, sort_keys=True) + "\n")
                fh.flush()
                os.fsync(fh.fileno())
            added.append(ev["id"])
        return {"added": added, "skipped_duplicates": skipped}

    # --- git ---------------------------------------------------------------
    def commit(self, message: str) -> str:
        if not (self.home / ".git").exists():
            return "no-git"
        subprocess.run(["git", "add", "-A"], cwd=self.home, capture_output=True)
        r = subprocess.run(
            ["git", "-c", "user.name=gt", "-c", "user.email=gt@localhost", "commit", "-q", "-m", message],
            cwd=self.home,
            capture_output=True,
        )
        return "committed" if r.returncode == 0 else "nothing-to-commit"


def atomic_write(path: Path, text: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(tmp, path)
