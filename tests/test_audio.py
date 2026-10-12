import json
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from synth import grid_onsets, pluck_wav  # noqa: E402
from test_core import GtCase  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
EX = "downpicking-200-bpm-interwaly-60-30-osemki"


@unittest.skipUnless(shutil.which("uv") and os.environ.get("GT_TEST_AUDIO", "1") == "1", "uv not available")
class TestAudio(GtCase):
    def analyze(self, wav, *extra):
        r = subprocess.run(["uv", "run", "--quiet", str(ROOT / "gt_audio.py"), str(wav), *extra],
                           capture_output=True, text=True, timeout=900)
        return json.loads(r.stdout.strip().splitlines()[-1])

    def test_grid_metrics_match_synthetic_truth(self):
        steady, rush = self.home / "steady.wav", self.home / "rush.wav"
        pluck_wav(steady, grid_onsets(120, 2, 12, jitter_ms=10))
        pluck_wav(rush, grid_onsets(120, 2, 16, jitter_ms=3, rush_after=8, rush_ms_per_note=4))
        a = self.analyze(steady, "--bpm", "120", "--subdivision", "8ths")
        self.assertAlmostEqual(a["timing_mean_abs_ms"], 8.0, delta=3.0)  # E|N(0,10)| = 8 ms
        self.assertAlmostEqual(a["bpm_actual"], 120, delta=0.5)
        self.assertIsNone(a["breakdown_at_s"])
        self.assertEqual(a["tempo_trend"], "steady")
        b = self.analyze(rush, "--bpm", "120", "--subdivision", "8ths")
        self.assertEqual(b["tempo_trend"], "speeding_up")
        self.assertGreaterEqual(b["breakdown_at_s"], 8.0)
        self.assertLess(b["ioi_mean_abs_dev_ms"], 8.0)  # gradual rush is not local jitter

    def test_gt_analyze_records_event_and_signal(self):
        self.setup_profile_and_paths()
        w1, w2 = self.home / "t1.wav", self.home / "t2.wav"
        pluck_wav(w1, grid_onsets(150, 2, 10, jitter_ms=20, seed=3))
        pluck_wav(w2, grid_onsets(150, 2, 10, jitter_ms=5, seed=4))
        r1 = self.gt("analyze", str(w1), "--exercise", EX, "--bpm", "150")
        self.gt("analyze", str(w2), "--exercise", EX, "--bpm", "150")
        self.assertGreater(r1["metrics"]["timing_mean_abs_ms"], 10)
        st = self.gt("state", "--full")
        self.assertEqual(len(st["recordings"]), 2)
        sig = [s for s in self.gt("signals")["signals"] if s["type"] == "timing_trend"]
        self.assertEqual(sig[0]["severity"], "info")  # improved
        missing = self.gt("analyze", str(self.home / "nope.wav"), ok=False)
        self.assertFalse(missing["ok"])


if __name__ == "__main__":
    unittest.main()
