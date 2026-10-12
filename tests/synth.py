"""Synthetic plucked-note WAVs with known timing (stdlib only) for audio-analysis tests."""

import math
import random
import struct
import wave


def pluck_wav(path, onsets, sr=44100, freq=110.0, dur=None, amp_pattern=None, seed=1):
    rnd = random.Random(seed)
    total = int(sr * (dur or (max(onsets) + 1.0)))
    buf = [0.0] * total
    for i, t0 in enumerate(onsets):
        a = amp_pattern[i % len(amp_pattern)] if amp_pattern else 1.0
        start = int(t0 * sr)
        for n in range(int(0.12 * sr)):
            k = start + n
            if k >= total:
                break
            env = math.exp(-n / (0.03 * sr))
            buf[k] += a * env * (0.6 * math.sin(2 * math.pi * freq * n / sr) + 0.3 * math.sin(4 * math.pi * freq * n / sr)
                                 + 0.1 * (rnd.random() * 2 - 1))
    peak = max(1e-9, max(abs(x) for x in buf))
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(b"".join(struct.pack("<h", int(32000 * x / peak)) for x in buf))


def grid_onsets(bpm, subdiv, seconds, jitter_ms=0.0, start=0.5, rush_after=None, rush_ms_per_note=0.0, seed=2):
    rnd = random.Random(seed)
    period = 60.0 / bpm / subdiv
    out, drift = [], 0.0
    t = start
    while t < start + seconds:
        if rush_after is not None and t - start > rush_after:
            drift -= rush_ms_per_note / 1000
        out.append(t + drift + rnd.gauss(0, jitter_ms / 1000))
        t += period
    return out
