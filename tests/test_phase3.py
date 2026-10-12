import json
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gt.songs import _cache_path, tuning_name  # noqa: E402
from tests.test_core import FIX, GtCase  # noqa: E402

DP = "downpicking-200-bpm"
EX = "downpicking-200-bpm-interwaly-60-30-osemki"


class TestSignals(GtCase):
    def types(self, day):
        return {s["type"] for s in self.gt("signals", day=day)["signals"]}

    def test_progress_and_stage_ready(self):
        self.setup_profile_and_paths()
        self.gt("session", "cold-check", EX, "--bpm", "155", day="2026-10-13")
        self.gt("session", "cold-check", EX, "--bpm", "165", day="2026-10-24")
        sig = self.gt("signals", day="2026-10-26")["signals"]
        prog = [s for s in sig if s["type"] == "progress"]
        self.assertEqual(prog[0]["data"]["bpm"], 165)
        self.assertEqual(prog[0]["data"]["previous"], 155)

    def test_plateau_neglect_skipped_inactivity(self):
        self.setup_profile_and_paths()
        for d in ("2026-10-13", "2026-10-15", "2026-10-17", "2026-10-20", "2026-10-22", "2026-10-24"):
            self.gt("session", "cold-check", EX, "--bpm", "160", day=d)
        t = self.types("2026-10-25")
        self.assertIn("plateau", t)
        self.assertIn("neglect", t)  # blues untouched since creation
        self.assertNotIn("skipped_sessions", t)  # 6 practice days in 13 vs declared 5/week: not skipping
        self.assertIn("inactivity", self.types("2026-10-30"))

    def test_skipped_sessions(self):
        self.setup_profile_and_paths()
        for d in ("2026-10-13", "2026-10-20"):
            self.gt("session", "log", "--path", DP, "--minutes", "20", day=d)
        self.assertIn("skipped_sessions", self.types("2026-10-26"))

    def test_health_signals(self):
        self.setup_profile_and_paths()
        self.gt("session", "pain", "--note", "nadgarstek", "--rating", "3")
        sig = self.gt("signals")["signals"]
        self.assertEqual(sig[0]["type"], "health_risk")
        self.assertEqual(sig[0]["severity"], "critical")

    def test_session_end_returns_signals(self):
        self.setup_profile_and_paths()
        self.gt("session", "start")
        self.gt("session", "cold-check", EX, "--bpm", "170")
        r = self.gt("session", "end")
        self.assertTrue(any(s["type"] == "progress" for s in r["signals"]))


class TestSongs(GtCase):
    def setUp(self):
        super().setUp()
        os.environ["GT_OFFLINE"] = "1"

    def tearDown(self):
        os.environ.pop("GT_OFFLINE", None)
        super().tearDown()

    def env(self, day=None):
        return dict(super().env(day), GT_OFFLINE="1")

    def test_suggest_bands_follow_profile_level(self):
        self.setup_profile_and_paths()
        r = self.gt("song", "suggest", "--path", DP)
        self.assertEqual(r["level"], 3)  # technique-picking L3 in fixture profile
        self.assertTrue(all(s["level"] == 2 for s in r["comfort"]))
        self.assertTrue(all(s["level"] == 4 for s in r["stretch"]))
        self.assertTrue(all("technique-picking" in s["axes"] for s in r["target"]))

    def test_add_from_seed_excluded_from_next_suggestions(self):
        self.setup_profile_and_paths()
        r = self.gt("song", "add", "--from", json.dumps([{"seed_id": "metallica-master-of-puppets", "path_id": DP}]))
        sid = r["song_ids"][0]
        song = self.gt("state", "--full")["songs"][sid]
        self.assertEqual((song["artist"], song["source"]), ("Metallica", "seed"))
        titles = [s["title"] for s in self.gt("song", "suggest", "--path", DP)["stretch"]]
        self.assertNotIn("Master of Puppets", titles)
        bad = self.gt("song", "add", "--from", json.dumps([{"seed_id": "nope"}]), ok=False)
        self.assertFalse(bad["ok"])

    def test_verify_from_cache_records_event(self):
        self.setup_profile_and_paths()
        sid = self.gt("song", "add", "--from", json.dumps([{"seed_id": "soundgarden-outshined"}]))["song_ids"][0]
        url = "https://www.songsterr.com/api/songs?pattern=Soundgarden%20Outshined&size=10"
        cache = _cache_path(self.home, url)
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps([{"songId": 1, "artist": "Soundgarden", "title": "Outshined", "tracks": [
            {"instrument": "Distortion Guitar", "views": 10, "difficulty": 3, "tuning": [64, 59, 55, 50, 45, 38]},
            {"instrument": "Electric Bass (finger)", "difficulty": 2, "tuning": [43, 38, 33, 26]}]}]))
        r = self.gt("song", "verify", sid)
        self.assertTrue(r["verified"])
        self.assertEqual(r["tuning"], "Drop D")
        self.assertEqual(r["songsterr_difficulty"], {"min": 3, "max": 3})
        self.assertTrue(any("offline" in e for e in r["errors"]))  # musicbrainz not cached
        song = self.gt("state", "--full")["songs"][sid]
        self.assertEqual(song["verification"], "ok")
        self.assertIsNotNone(song["verified_at"])

    def test_tuning_names(self):
        self.assertEqual(tuning_name([64, 59, 55, 50, 45, 40]), "E standard")
        self.assertEqual(tuning_name([64, 59, 55, 50, 45, 38]), "Drop D")
        self.assertTrue(tuning_name([63, 58, 54, 49, 44, 39]).startswith("Eb standard"))
        self.assertTrue(tuning_name([64, 59, 55, 50, 45, 40, 35]).startswith("E standard (7"))


if __name__ == "__main__":
    unittest.main()
