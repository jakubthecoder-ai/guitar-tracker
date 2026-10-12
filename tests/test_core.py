import json
import os
import subprocess
import tempfile
import unittest
import urllib.error
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures"
GT = str(ROOT / "bin" / "gt")


class GtCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.day = "2026-10-12"
        self.gt("init")

    def tearDown(self):
        self.tmp.cleanup()

    def env(self, day=None):
        return dict(os.environ, GT_HOME=str(self.home), GT_TODAY=day or self.day, HOME=str(self.home))

    def gt(self, *args, day=None, ok=True, stdin=None):
        r = subprocess.run([GT, *args], capture_output=True, text=True, env=self.env(day), input=stdin)
        try:
            out = json.loads(r.stdout)
        except json.JSONDecodeError:
            self.fail(f"non-JSON output for {args}: {r.stdout}\n{r.stderr}")
        if ok:
            self.assertEqual(r.returncode, 0, f"{args} -> {out}\n{r.stderr}")
        return out

    def setup_profile_and_paths(self):
        self.gt("profile", "init", "--from", str(FIX / "profile.json"))
        self.gt("path", "create", "--from", str(FIX / "path_downpick.json"))
        self.gt("path", "create", "--from", str(FIX / "path_blues.json"))
        return "downpicking-200-bpm-interwaly-60-30-osemki"


class TestPaths(GtCase):
    def test_one_path_one_goal_one_topic(self):
        spec = json.loads((FIX / "path_downpick.json").read_text())
        spec["topic_axis"] = ["technique-picking", "rhythm-timing"]
        r = self.gt("path", "create", "--from", json.dumps(spec), ok=False)
        self.assertFalse(r["ok"])
        self.assertTrue(any("jeden temat" in e for e in r["details"]["errors"]))
        spec = json.loads((FIX / "path_downpick.json").read_text())
        spec["primary_metric"] = [spec["primary_metric"], {"type": "custom", "target": 3}]
        r = self.gt("path", "create", "--from", json.dumps(spec), ok=False)
        self.assertTrue(any("jeden cel" in e for e in r["details"]["errors"]))

    def test_unrealistic_deadline_needs_force(self):
        spec = json.loads((FIX / "path_downpick.json").read_text())
        spec["deadline"] = "2026-10-26"
        r = self.gt("path", "create", "--from", json.dumps(spec), ok=False)
        self.assertTrue(any("tygodniowo" in w for w in r["details"]["warnings"]))
        r = self.gt("path", "create", "--from", json.dumps(spec), "--force")
        self.assertEqual(r["status"], "active")

    def test_active_limit_queues_as_paused(self):
        base = json.loads((FIX / "path_blues.json").read_text())
        statuses = []
        for i in range(5):
            spec = dict(base, title=f"Ścieżka {i}", goal="cel", exercises=[])
            statuses.append(self.gt("path", "create", "--from", json.dumps(spec), "--force")["status"])
        self.assertEqual(statuses, ["active"] * 4 + ["paused"])


class TestEventsAndState(GtCase):
    def test_ingest_is_idempotent(self):
        self.setup_profile_and_paths()
        ev = {"id": str(uuid.uuid4()), "ts": "2026-10-12T18:00:00+02:00", "type": "item_logged", "source": "html",
              "actor": "user", "payload": {"path_id": "frazowanie-bluesowe", "practice_type": "jam", "minutes": 10}}
        f = self.home / "export.json"
        f.write_text(json.dumps({"events": [ev]}))
        r1 = self.gt("ingest", str(f), "--keep")
        r2 = self.gt("ingest", str(f), "--keep")
        self.assertEqual((r1["added"], r2["added"], r2["skipped_duplicates"]), (1, 0, 1))
        bad = dict(ev, id=str(uuid.uuid4()), payload={"practice_type": "jam"})
        f.write_text(json.dumps([bad]))
        r3 = self.gt("ingest", str(f), "--keep", ok=False)
        self.assertEqual(len(r3["rejected"]), 1)

    def test_rebuild_from_log_is_deterministic(self):
        ex = self.setup_profile_and_paths()
        self.gt("session", "start")
        self.gt("session", "log", "--exercise", ex, "--minutes", "10", "--bpm", "156", "--clean-reps", "4")
        self.gt("session", "end")
        s1 = (self.home / "derived" / "state.json").read_text()
        for f in (self.home / "derived").iterdir():
            f.unlink()
        self.gt("derive")
        self.assertEqual(s1, (self.home / "derived" / "state.json").read_text())

    def test_parallel_writes_do_not_lose_events(self):
        self.setup_profile_and_paths()
        before = len(self.gt("state", "--full")["sessions"])
        with ThreadPoolExecutor(8) as pool:
            list(pool.map(lambda i: self.gt("session", "log", "--path", "frazowanie-bluesowe", "--type", "jam",
                                            "--minutes", "1"), range(12)))
        self.assertEqual(self.gt("validate")["problems"], [])
        st = self.gt("state", "--full")
        self.assertEqual(st["paths"]["frazowanie-bluesowe"]["minutes_total"], 12)
        self.assertEqual(len(st["sessions"]), before)

    def test_cold_check_confirms_tempo_next_day(self):
        ex = self.setup_profile_and_paths()
        self.gt("session", "log", "--exercise", ex, "--minutes", "10", "--bpm", "160", "--clean-reps", "3")
        st = self.gt("state", "--full")
        self.assertIsNone(st["exercises"][ex]["clean_bpm"])
        plan = self.gt("plan", "--minutes", "30", day="2026-10-13")
        self.assertEqual([c["bpm"] for c in plan["slots"][0]["cold_checks"]], [160])
        self.gt("session", "cold-check", ex, "--bpm", "160", day="2026-10-13")
        st = self.gt("state", "--full", day="2026-10-13")
        self.assertEqual(st["exercises"][ex]["clean_bpm"], 160)
        self.assertEqual(st["paths"]["downpicking-200-bpm"]["metric_state"]["current"], 160)

    def test_profile_level_change_requires_confirmation(self):
        self.setup_profile_and_paths()
        r = self.gt("profile", "change", "--from", json.dumps([
            {"field": "axes.rhythm-timing.level", "new": 3, "trigger": "progress", "rationale": "timing stabilny"},
            {"field": "benchmarks.downpick_8ths_60s", "new": 160, "trigger": "progress", "rationale": "cold check"}]))
        self.assertEqual(len(r["pending"]), 1)
        prof = self.gt("profile", "show")
        self.assertEqual(prof["profile"]["axes"]["rhythm-timing"]["level"], 2)
        self.assertEqual(prof["profile"]["benchmarks"]["downpick_8ths_60s"], 160)
        self.gt("profile", "confirm", r["pending"][0])
        self.assertEqual(self.gt("profile", "show")["profile"]["axes"]["rhythm-timing"]["level"], 3)
        hist = self.gt("profile", "history")["history"]
        self.assertEqual([h["status"] for h in hist], ["applied", "applied", "applied"])


class TestPlan(GtCase):
    def test_neglected_path_is_forced_and_k_depends_on_minutes(self):
        self.setup_profile_and_paths()
        extra = dict(json.loads((FIX / "path_blues.json").read_text()), title="Nieparzyste metrum",
                     topic_axis="rhythm-timing", goal="Riff w 7/8", exercises=[], priority=1)
        self.gt("path", "create", "--from", json.dumps(extra), "--force")
        self.gt("session", "log", "--path", "downpicking-200-bpm", "--minutes", "20", day="2026-10-19")
        self.gt("session", "log", "--path", "frazowanie-bluesowe", "--minutes", "20", day="2026-10-19")
        p30 = self.gt("plan", "--minutes", "30", day="2026-10-20")
        self.assertEqual(p30["selected"][0]["path_id"], "nieparzyste-metrum")
        self.assertTrue(p30["selected"][0]["forced"])
        self.assertEqual(len(p30["selected"]), 2)
        p90 = self.gt("plan", "--minutes", "90", day="2026-10-20")
        self.assertEqual(len(p90["selected"]), 3)
        self.assertEqual(sum(s["minutes"] for s in p90["slots"]), 90)

    def test_pain_makes_light_session(self):
        self.setup_profile_and_paths()
        self.gt("session", "pain", "--note", "nadgarstek", "--rating", "4")
        plan = self.gt("plan", "--minutes", "60", day="2026-10-13")
        self.assertEqual(plan["mode"], "light")
        self.assertLessEqual(plan["minutes"], 20)

    def test_plan_commit_and_volume_cap(self):
        self.setup_profile_and_paths()
        for d in ("2026-10-06", "2026-10-07"):
            self.gt("session", "log", "--path", "frazowanie-bluesowe", "--minutes", "20", day=d)
        plan = self.gt("plan", "--minutes", "90", day="2026-10-13")
        self.assertLess(plan["minutes"], 90)
        blocks = {"blocks": [{"kind": "warmup", "minutes": 5}, {"kind": "path", "path_id": "frazowanie-bluesowe",
                                                                "minutes": 20, "title": "Call & response"}]}
        r = self.gt("plan", "commit", "--from", json.dumps(blocks), day="2026-10-13")
        self.assertEqual(r["date"], "2026-10-13")
        self.assertTrue((self.home / "plans" / "2026-10-13.json").exists())


    def test_volume_cap_uses_multi_week_baseline_after_break(self):
        self.setup_profile_and_paths()
        for d in ("2026-09-15", "2026-09-17", "2026-09-22", "2026-09-24", "2026-09-29"):
            self.gt("session", "log", "--path", "frazowanie-bluesowe", "--minutes", "40", day=d)
        # 13 days off: last week 0 min, but the 3 weeks before averaged ~67 min/week
        plan = self.gt("plan", "--minutes", "60", day="2026-10-12")
        self.assertGreaterEqual(plan["minutes"], 20)
        self.assertGreater(plan["minutes"], 18)
        forced = self.gt("plan", "--minutes", "200", "--ignore-volume-cap", day="2026-10-12")
        self.assertEqual(forced["minutes"], 200)
        self.assertTrue(any("na życzenie" in w for w in forced["warnings"]))


class TestReportAndServer(GtCase):
    def test_report_embeds_state_and_is_deterministic(self):
        ex = self.setup_profile_and_paths()
        self.gt("session", "log", "--exercise", ex, "--minutes", "10", "--bpm", "160", "--clean-reps", "3")
        self.gt("session", "cold-check", ex, "--bpm", "158", day="2026-10-13")
        a = Path(self.gt("report", "--out", str(self.home / "a.html"), day="2026-10-13")["report"]).read_text()
        b = Path(self.gt("report", "--out", str(self.home / "b.html"), day="2026-10-13")["report"]).read_text()
        self.assertEqual(a, b)
        raw = a.split('id="gt-state">', 1)[1].split("</script>", 1)[0]
        vm = json.loads(raw)
        self.assertEqual(vm["as_of"], "2026-10-13")
        self.assertEqual(len(vm["paths"]), 2)
        self.assertNotIn("/*__GT_STATE__*/", a)

    def test_server_accepts_html_events_with_token(self):
        self.setup_profile_and_paths()
        proc = subprocess.Popen([GT, "serve", "--port", "0"], stdout=subprocess.PIPE, text=True, env=self.env())
        try:
            url = json.loads(proc.stdout.readline())["url"]
            base, token = url.split("/?t=")
            self.assertIn(b"gt-state", urllib.request.urlopen(url).read())
            with self.assertRaises(urllib.error.HTTPError) as cm:
                urllib.request.urlopen(f"{base}/health?t=wrong")
            self.assertEqual(cm.exception.code, 403)
            ev = {"id": str(uuid.uuid4()), "ts": "2026-10-12T19:00:00+02:00", "type": "song_added", "source": "html",
                  "actor": "user", "payload": {"song_id": "x", "artist": "A", "title": "T"}}
            req = urllib.request.Request(f"{base}/events?t={token}", data=json.dumps({"events": [ev]}).encode(),
                                         headers={"Content-Type": "application/json"})
            self.assertTrue(json.loads(urllib.request.urlopen(req).read())["ok"])
        finally:
            proc.terminate()
            proc.wait(5)
            proc.stdout.close()
        self.assertIn("x", self.gt("state", "--full")["songs"])


if __name__ == "__main__":
    unittest.main()
