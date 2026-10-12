"""Song shortlist from a curated seed + verification against Songsterr (unofficial API) and MusicBrainz.

Policy: low rate, cached, metadata only. Tabs are linked, never copied. Ultimate Guitar is link-only.
"""

import json
import os
import re
import time
import urllib.parse
import urllib.error
import urllib.request
from pathlib import Path

SEED = Path(__file__).resolve().parents[1] / ".agents" / "skills" / "gt-songs" / "references" / "songs_seed.json"
USER_AGENT = "guitar-tracker/0.3 (+https://github.com/jakubthecoder-ai/guitar-tracker)"
NOTE = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
STD6 = [64, 59, 55, 50, 45, 40]
_last_call = {}


def load_seed() -> list:
    return json.loads(SEED.read_text(encoding="utf-8"))["songs"]


def seed_id(s: dict) -> str:
    from .paths import slugify
    return slugify(f"{s['artist']}-{s['title']}")


def suggest(st: dict, axis: str | None, technique: str | None, level: int | None, limit: int = 3) -> dict:
    """Return comfort / target / stretch candidates from the seed, excluding songs already in the library."""
    have = {(s["artist"].lower(), s["title"].lower()) for s in st["songs"].values()}
    pool = [s for s in load_seed() if (s["artist"].lower(), s["title"].lower()) not in have]
    if axis:
        pool = [s for s in pool if axis in s["axes"]]
    if technique:
        t = technique.lower()
        pool = [s for s in pool if any(t in x.lower() for x in s["techniques"])]
    lvl = level or 3
    bands = {"comfort": lvl - 1, "target": lvl, "stretch": lvl + 1}
    out = {}
    for name, band in bands.items():
        picks = [s for s in pool if s["level"] == band]
        out[name] = [dict(s, seed_id=seed_id(s)) for s in picks[:limit]]
    return {"level": lvl, "axis": axis, "technique": technique, **out,
            "note": "Lista startowa przygotowana ręcznie; poziomy orientacyjne (L1–L5). Przed dodaniem: gt song verify."}


def tuning_name(midi: list) -> str:
    if not midi:
        return "?"
    n = len(midi)
    low = midi[-1]
    std = STD6 + ([35] if n >= 7 else []) + ([30] if n >= 8 else [])
    std = std[:n]
    diffs = [a - b for a, b in zip(midi, std)]
    if len(set(diffs)) == 1:
        d = diffs[0]
        base = "standard" if n == 6 else f"standard ({n} strun)"
        return f"E {base}" if d == 0 else f"{NOTE[(low) % 12]} {base} ({d:+d} pół tonu)"
    if len(set(diffs[:-1])) == 1 and diffs[-1] == diffs[0] - 2:
        return f"Drop {NOTE[low % 12]}" + (f" ({n} strun)" if n != 6 else "")
    return " ".join(NOTE[m % 12] for m in reversed(midi))


def _cache_path(home: Path, key: str) -> Path:
    return home / "cache" / (re.sub(r"[^a-z0-9]+", "_", key.lower())[:120] + ".json")


def _get_json(home: Path, url: str, host: str, min_interval: float) -> object:
    cache = _cache_path(home, url)
    if cache.exists() and time.time() - cache.stat().st_mtime < 30 * 86400:
        return json.loads(cache.read_text(encoding="utf-8"))
    if os.environ.get("GT_OFFLINE"):
        raise ConnectionError("tryb offline (GT_OFFLINE)")
    wait = min_interval - (time.time() - _last_call.get(host, 0))
    if wait > 0:
        time.sleep(wait)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as e:
            if e.code not in (429, 503) or attempt:
                raise
            time.sleep(2.0)  # rate limited: back off once
    _last_call[host] = time.time()
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(data), encoding="utf-8")
    return data


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower().replace("&", "and"))


def verify(home: Path, artist: str, title: str) -> dict:
    """Check that the song exists; gather tab link, tuning and Songsterr guitar-part difficulty (1–8)."""
    res = {"artist": artist, "title": title, "verified": False, "sources": [], "errors": []}
    q = urllib.parse.quote(f"{artist} {title}")
    try:
        data = _get_json(home, f"https://www.songsterr.com/api/songs?pattern={q}&size=10", "songsterr", 1.0)
        match = next((s for s in data if _norm(s["artist"]) == _norm(artist) and _norm(s["title"]) == _norm(title)),
                     None)
        if match:
            guitars = [t for t in match.get("tracks", []) if "guitar" in t.get("instrument", "").lower()
                       and "bass" not in t.get("instrument", "").lower()]
            diffs = [t["difficulty"] for t in guitars if isinstance(t.get("difficulty"), int)]
            slug = re.sub(r"[^a-z0-9]+", "-", f"{match['artist']} {match['title']}".lower()).strip("-")
            main = max(guitars, key=lambda t: t.get("views", 0)) if guitars else None
            res.update(verified=True, url=f"https://www.songsterr.com/a/wsa/{slug}-tab-s{match['songId']}",
                       tuning=tuning_name(main["tuning"]) if main else None,
                       songsterr_difficulty={"min": min(diffs), "max": max(diffs)} if diffs else None,
                       guitar_parts=[{"name": t.get("name"), "difficulty": t.get("difficulty"),
                                      "tuning": tuning_name(t.get("tuning", []))} for t in guitars[:6]])
            res["sources"].append("songsterr")
    except Exception as e:  # network/API drift must not break the tracker
        res["errors"].append(f"songsterr: {type(e).__name__}: {e}")
    try:
        mq = urllib.parse.quote(f'recording:"{title}" AND artist:"{artist}"')
        data = _get_json(home, f"https://musicbrainz.org/ws/2/recording?query={mq}&fmt=json&limit=5", "musicbrainz", 1.1)
        rec = next((r for r in data.get("recordings", []) if _norm(r["title"]) == _norm(title)), None)
        if rec:
            res["verified"] = True
            res["sources"].append("musicbrainz")
            if rec.get("length"):
                res["length_s"] = round(rec["length"] / 1000)
            res["musicbrainz_id"] = rec["id"]
    except Exception as e:
        res["errors"].append(f"musicbrainz: {type(e).__name__}: {e}")
    res["ug_search"] = "https://www.ultimate-guitar.com/search.php?search_type=title&value=" + q
    return res
