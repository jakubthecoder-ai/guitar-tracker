#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy>=1.26", "librosa>=0.10", "soundfile>=0.12", "PyGuitarPro>=0.9"]
# ///
"""Timing analysis of a practice recording (best: DI / clean signal) against a metronome grid or a Guitar Pro tab.

Prints one JSON object. Used by `gt analyze`; can run standalone:
  uv run gt_audio.py take.wav --bpm 160 --subdivision 8ths
  uv run gt_audio.py take.wav --gp riff.gp5 --track 0 [--bpm 160]

Approach (after mridangam-playing-analysis): detect note onsets, then measure (a) deviation from a phase-fitted grid
and (b) neighbour-relative inter-onset intervals, so a constant small rush does not accumulate into a fake drift.
"""

import argparse
import json
import sys

import numpy as np

SUBDIV = {"quarters": 1, "8ths": 2, "triplets": 3, "16ths": 4, "sextuplets": 6, "32nds": 8}


def detect_onsets(path: str):
    import librosa
    y, sr = librosa.load(path, sr=None, mono=True)
    hop = 128
    env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    frames = librosa.onset.onset_detect(onset_envelope=env, sr=sr, hop_length=hop, backtrack=False,
                                        pre_max=3, post_max=3, pre_avg=10, post_avg=10, delta=0.2, wait=6)
    times = librosa.frames_to_time(frames, sr=sr, hop_length=hop)
    rms = librosa.feature.rms(y=y, hop_length=hop)[0]
    amps = np.array([rms[min(f + 2, len(rms) - 1)] for f in frames])
    return np.asarray(times), amps, len(y) / sr


def grid_metrics(t: np.ndarray, amps: np.ndarray, bpm: float, subdiv: int) -> dict:
    period = 60.0 / bpm / subdiv
    # phase fit: circular mean of onset positions within one grid period
    ang = 2 * np.pi * (t % period) / period
    phase = (np.angle(np.mean(np.exp(1j * ang))) % (2 * np.pi)) / (2 * np.pi) * period
    dev = ((t - phase + period / 2) % period) - period / 2  # seconds, signed, relative to nearest grid line
    dev_ms = dev * 1000
    ioi = np.diff(t)
    # ignore gaps that skip grid slots (rests) for the neighbour metric
    ioi_ok = ioi[(ioi > period * 0.5) & (ioi < period * 1.5)]
    ioi_dev_ms = (ioi_ok - period) * 1000
    idx = np.round((t - t[0]) / period)
    actual_bpm = None
    if len(t) >= 4 and np.ptp(idx) > 0:
        slope = np.polyfit(idx, t, 1)[0]  # seconds per grid step
        actual_bpm = 60.0 / (slope * subdiv)
    # tempo drift: instantaneous tempo vs time
    drift = None
    if len(ioi_ok) >= 6:
        mids = t[1:][(ioi > period * 0.5) & (ioi < period * 1.5)]
        inst_bpm = 60.0 / (ioi_ok * subdiv)
        drift = float(np.polyfit(mids, inst_bpm, 1)[0] * 10)  # BPM per 10 s
    # breakdown: first 2 s window whose mean |dev| exceeds max(25 ms, 15% of period)
    thr = max(25.0, 0.15 * period * 1000)
    breakdown = None
    for start in np.arange(t[0], t[-1], 0.5):
        m = (t >= start) & (t < start + 2.0)
        if m.sum() >= 4 and np.mean(np.abs(dev_ms[m])) > thr:
            breakdown = round(float(start - t[0]), 1)
            break
    odd, even = amps[1::2], amps[0::2]
    acc = float(20 * np.log10((np.mean(odd) + 1e-9) / (np.mean(even) + 1e-9))) if len(odd) and len(even) else None
    ioi_alt = None
    if len(ioi_ok) >= 4:
        ioi_alt = float((np.mean(ioi[0::2]) - np.mean(ioi[1::2])) * 1000)
    return {
        "mode": "grid", "bpm_target": bpm, "subdivision": subdiv, "grid_period_ms": round(period * 1000, 1),
        "timing_mean_abs_ms": round(float(np.mean(np.abs(dev_ms))), 1),
        "timing_std_ms": round(float(np.std(dev_ms)), 1),
        "ioi_mean_abs_dev_ms": round(float(np.mean(np.abs(ioi_dev_ms))), 1) if len(ioi_dev_ms) else None,
        "bpm_actual": round(actual_bpm, 1) if actual_bpm else None,
        "rushing": None if actual_bpm is None else ("rush" if actual_bpm > bpm * 1.01 else
                                                     "drag" if actual_bpm < bpm * 0.99 else "steady"),
        "tempo_drift_bpm_per_10s": round(drift, 2) if drift is not None else None,
        "tempo_trend": None if drift is None else ("speeding_up" if drift > 1 else
                                                  "slowing_down" if drift < -1 else "steady"),
        "breakdown_at_s": breakdown, "breakdown_threshold_ms": round(thr, 1),
        "accent_odd_vs_even_db": round(acc, 2) if acc is not None else None,
        "alternating_ioi_bias_ms": round(ioi_alt, 1) if ioi_alt is not None else None,
    }


def gp_expected_onsets(gp_path: str, track: int, bpm: float | None) -> tuple:
    import guitarpro
    song = guitarpro.parse(gp_path)
    tempo = bpm or song.tempo
    tr = song.tracks[track]
    times, t = [], 0.0
    for measure in tr.measures:
        voice = measure.voices[0]
        for beat in voice.beats:
            q = 4.0 / beat.duration.value  # quarter notes
            if beat.duration.isDotted:
                q *= 1.5
            if beat.duration.tuplet.enters != beat.duration.tuplet.times:
                q *= beat.duration.tuplet.times / beat.duration.tuplet.enters
            if beat.notes and beat.status.name == "normal":
                times.append(t)
            t += q * 60.0 / tempo
    return np.array(times), tempo, tr.name


def tab_metrics(t: np.ndarray, expected: np.ndarray) -> dict:
    """Align detected onsets to expected ones (offset fit + nearest match), report timing, missed and extra notes."""
    best = None
    for k in range(min(5, len(t))):  # try aligning the first few detected onsets with the first expected one
        off = t[k] - expected[0]
        shifted = expected + off
        j = np.searchsorted(t, shifted)
        cand = np.clip(np.stack([j - 1, j]), 0, len(t) - 1)
        nearest = np.where(np.abs(t[cand[0]] - shifted) < np.abs(t[cand[1]] - shifted), cand[0], cand[1])
        err = t[nearest] - shifted
        score = np.median(np.abs(err))
        if best is None or score < best[0]:
            best = (score, err, nearest)
    _, err, nearest = best
    # refine the offset with the median error of plausible matches, then re-match
    shift = float(np.median(err[np.abs(err) <= 0.06])) if np.any(np.abs(err) <= 0.06) else 0.0
    shifted = expected + (t[nearest[0]] - expected[0] - err[0]) + shift
    j = np.searchsorted(t, shifted)
    cand = np.clip(np.stack([j - 1, j]), 0, len(t) - 1)
    nearest = np.where(np.abs(t[cand[0]] - shifted) < np.abs(t[cand[1]] - shifted), cand[0], cand[1])
    err = t[nearest] - shifted
    tol = 0.06
    hit = np.abs(err) <= tol
    dev_ms = err[hit] * 1000
    used = set(nearest[hit].tolist())
    return {"mode": "tab", "notes_expected": int(len(expected)), "notes_detected": int(len(t)),
            "notes_matched": int(hit.sum()), "notes_missed": int((~hit).sum()),
            "extra_onsets": int(len(t) - len(used)),
            "timing_mean_abs_ms": round(float(np.mean(np.abs(dev_ms))), 1) if len(dev_ms) else None,
            "timing_std_ms": round(float(np.std(dev_ms)), 1) if len(dev_ms) else None,
            "mean_signed_ms": round(float(np.mean(dev_ms)), 1) if len(dev_ms) else None}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("wav")
    ap.add_argument("--bpm", type=float)
    ap.add_argument("--subdivision", default="8ths", choices=sorted(SUBDIV))
    ap.add_argument("--gp")
    ap.add_argument("--track", type=int, default=0)
    a = ap.parse_args()
    try:
        t, amps, duration = detect_onsets(a.wav)
    except Exception as e:
        print(json.dumps({"ok": False, "error": f"Nie udało się wczytać nagrania: {e}"}, ensure_ascii=False))
        return 1
    base = {"ok": True, "file": a.wav, "duration_s": round(duration, 2), "onsets": int(len(t)),
            "caveat": "Analiza timingu (początki dźwięków). Najdokładniej na czystym sygnale DI; przester i pogłos "
                      "zaniżają wiarygodność. Nie ocenia brzmienia ani ekspresji."}
    if len(t) < 4:
        print(json.dumps(dict(base, ok=False, error="Za mało wykrytych dźwięków (min. 4)."), ensure_ascii=False))
        return 1
    if a.gp:
        expected, tempo, name = gp_expected_onsets(a.gp, a.track, a.bpm)
        res = dict(base, **tab_metrics(t, expected), bpm_target=tempo, gp_track=name)
    else:
        if not a.bpm:
            print(json.dumps(dict(base, ok=False, error="Podaj --bpm (tempo metronomu) albo --gp."), ensure_ascii=False))
            return 1
        res = dict(base, **grid_metrics(t, amps, a.bpm, SUBDIV[a.subdivision]))
    print(json.dumps(res, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
