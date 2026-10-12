"""Path rules: one path = one goal = one topic, deadline realism, active-path limit."""

import re
import unicodedata
from datetime import date

from .config import AXES, METRIC_TYPES

# Keywords hinting that a goal spans more than one taxonomy axis.
AXIS_KEYWORDS = {
    "technique-picking": ["kostk", "picking", "downpick", "tremolo", "alternate"],
    "technique-legato": ["legato", "tapping", "sweep", "hammer"],
    "rhythm-timing": ["rytm", "timing", "metrum", "metronom", "groove", "7/8", "5/4"],
    "fretboard-theory": ["teori", "gryf", "skal", "mod", "caged", "akord"],
    "ear": ["słuch", "ze słuchu", "ear"],
    "improvisation": ["improw", "solówk", "solo", "fraz"],
    "tone-gear": ["brzmien", "sprzęt", "wzmacniacz", "efekt", "tone"],
}


def slugify(text: str) -> str:
    t = unicodedata.normalize("NFKD", text.replace("ł", "l").replace("Ł", "L")).encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()
    return t[:40] or "sciezka"


def unique_id(base: str, taken) -> str:
    cand, n = base, 2
    while cand in taken:
        cand, n = f"{base}-{n}", n + 1
    return cand


def check_path(spec: dict, st: dict, config: dict, today: date) -> dict:
    """Returns {errors: [...], warnings: [...]}. Errors block creation, warnings need --force."""
    errors, warnings = [], []
    axis = spec.get("topic_axis")
    if isinstance(axis, list) or (isinstance(axis, str) and "," in axis):
        errors.append("Jedna ścieżka = jeden temat: topic_axis musi być pojedynczą osią. Rozbij cel na osobne ścieżki.")
    elif axis not in AXES:
        errors.append(f"Nieznana oś '{axis}'. Dozwolone: {', '.join(AXES)}")
    metric = spec.get("primary_metric")
    if isinstance(metric, list):
        errors.append("Jedna ścieżka = jeden cel: dokładnie jedna primary_metric. Rozbij cel na osobne ścieżki.")
    elif not isinstance(metric, dict) or metric.get("type") not in METRIC_TYPES or "target" not in metric:
        errors.append(f"primary_metric wymaga {{type: {'|'.join(METRIC_TYPES)}, target}}")
    try:
        deadline = date.fromisoformat(spec.get("deadline", ""))
        if deadline <= today:
            errors.append("Deadline musi być w przyszłości.")
    except ValueError:
        errors.append("Deadline musi być datą RRRR-MM-DD.")
        deadline = None

    goal = f"{spec.get('title', '')} {spec.get('goal', '')}".lower()
    hit = sorted(a for a, kws in AXIS_KEYWORDS.items() if any(k in goal for k in kws))
    if len(hit) > 1 and axis in AXES:
        warnings.append(f"Cel brzmi, jakby dotyczył kilku tematów ({', '.join(hit)}). "
                        "Upewnij się, że to jeden cel z jedną metryką, inaczej rozbij na ścieżki.")

    if not errors and metric["type"] == "bpm" and deadline:
        base = (spec.get("baseline") or {}).get("bpm")
        if base:
            weeks = max((deadline - today).days / 7, 0.1)
            needed = (metric["target"] / base) ** (1 / weeks) - 1
            if needed > config["max_weekly_bpm_gain_pct"]:
                warnings.append(
                    f"Deadline wymaga ~{needed * 100:.1f}% BPM tygodniowo (z {base} do {metric['target']} w "
                    f"{weeks:.1f} tyg.), a bezpieczny limit to {config['max_weekly_bpm_gain_pct'] * 100:.0f}%. "
                    "Proponuję późniejszy termin albo pośredni cel.")
        else:
            warnings.append("Brak baseline.bpm: nie da się ocenić realności terminu. Zmierz tempo na zimno.")

    active = [p for p in st["paths"].values() if p["status"] == "active"]
    queued = len(active) >= config["max_active_paths"]
    return {"errors": errors, "warnings": warnings, "queued": queued}
