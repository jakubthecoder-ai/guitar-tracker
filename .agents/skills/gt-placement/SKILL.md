---
name: gt-placement
description: Wywiad wstępny guitar-trackera – ustala poziom gitarzysty L1–L5 osobno w 8 osiach (rundy pytań + mikrotesty), zapisuje profil (gt profile init) i proponuje 2–4 ścieżki, każda z jednym celem. Używaj przy pierwszym kontakcie, braku profilu lub prośbie o ponowną ocenę.
metadata:
  project: guitar-tracker
---

# gt-placement

Wymaga `gt-core`. Prowadzi go `placement-interviewer` w pętli `needs_input` (orkiestrator zadaje pytania).

## Przebieg
1. `gt state` – jeśli profil istnieje, to re-placement: pytaj tylko o osie z niską pewnością lub zmienione.
2. Rundy pytań z `references/placement-questions.md` (R1 tło i cele → R2 technika i rytm → R3 gryf, teoria,
   słuch, improwizacja → R4 sprzęt i nawyki). Pomijaj pytania z odpowiedzią. Max ~6 pytań na rundę.
3. Mikrotesty, gdy liczba jest niepewna (ćwiczenie + metronom + kryterium „czysto i luźno”).
4. Profil → `gt --actor placement-interviewer profile init --from '<json>'` (schemat niżej).
5. Propozycje ścieżek → `gt --actor placement-interviewer path propose --from '<json>'`.

## Schemat profilu (JSON)
```json
{
  "name": "opcjonalnie", "years_playing": 6, "genres": ["metal", "blues"],
  "weekly_minutes": 300, "sessions_per_week": 5,
  "intention": "Pn–pt po kolacji, 60 min, w pokoju z ampem",
  "gear": {"guitar": "7-string", "tuning": "B standard", "amp": "modeller"},
  "axes": {
    "technique-picking": {"level": 3, "note": "16-tki ~130 na jednej strunie, zmiana strun słabsza"},
    "technique-legato": {"level": 2}, "rhythm-timing": {"level": 2, "note": "rzadko z metronomem"},
    "fretboard-theory": {"level": 2}, "ear": {"level": 1}, "repertoire": {"level": 3},
    "improvisation": {"level": 2}, "tone-gear": {"level": 3}
  },
  "benchmarks": {"downpick_8ths_60s": 150, "alt_16ths_one_string": 130, "alt_16ths_crossing": 115},
  "goals_text": "Thrash rhythm na poziomie Metalliki + bluesowe solówki",
  "risks": ["ból nadgarstka po długim downpickingu"],
  "answers": [{"q": "…", "a": "…"}],
  "notes": "Mocny repertuar, słaby rytm i słuch – typowy profil samouka."
}
```
Wszystkie 8 osi muszą mieć `level` 1–5. Niepewność → niższy poziom + `note: "do weryfikacji testem"`.

## Propozycje ścieżek (JSON lista)
```json
[{"title": "Downpicking 200 BPM", "goal": "Ósemki downpickingiem 200 BPM przez 60 s, luźno",
  "topic_axis": "technique-picking", "primary_metric": {"type": "bpm", "target": 200, "unit": "BPM 8ths 60s"},
  "rationale": "Twój cel #1 (thrash) + baseline 150"}]
```
Mieszaj: 1–2 cele deklarowane + 1 luka (np. `rhythm-timing`, `ear`). Każda propozycja = jeden cel, jedna oś.
