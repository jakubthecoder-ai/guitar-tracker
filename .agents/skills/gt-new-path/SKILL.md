---
name: gt-new-path
description: Tworzenie nowej ścieżki w guitar-trackerze z zasadą jedna ścieżka = jeden cel = jeden temat. Wywiad pogłębiający dla tematu (downpicking, alternate picking, blues, nieparzyste metrum, konkretny utwór i inne), baseline, kamienie milowe, realny deadline, gt path check/create. Używaj, gdy użytkownik podaje nowy cel albo akceptuje propozycję ścieżki.
metadata:
  project: guitar-tracker
---

# gt-new-path

Wymaga `gt-core`. Prowadzi `path-interviewer` w pętli `needs_input`.

## Przebieg
1. **Jeden cel.** Ustal `topic_axis` (jedna z 8) i `primary_metric` (`bpm` | `song_status` | `minutes` | `custom`).
   Cel złożony („szybciej i lepsze solówki”) → zaproponuj podział, użytkownik wybiera jedną ścieżkę teraz.
2. **Pytania pogłębiające** z `references/deep-dive-questions.md` dla tematu (max ~6 na rundę, max 3 rundy).
   Zawsze: baseline (najlepiej test na zimno), czas tygodniowo, termin, ograniczenia (sprzęt, ból).
3. **Szablon**: dopasuj najbliższy z `references/path-templates.md` i przytnij do baseline/terminu.
4. **Realność**: `gt path check --from '<json>'` → ostrzeżenia pokaż użytkownikowi (przesunąć termin? cel pośredni?).
5. **Zapis**: `gt --actor path-interviewer path create --from '<json>'` (z `--force` tylko po świadomej akceptacji).

## Spec ścieżki (JSON)
```json
{
  "title": "Downpicking 200 BPM",
  "goal": "Ósemki downpickingiem 200 BPM przez 60 s, luźno, z palm mute",
  "topic_axis": "technique-picking",
  "primary_metric": {"type": "bpm", "target": 200, "unit": "BPM ósemki 60 s"},
  "deadline": "2027-02-28", "priority": 4,
  "baseline": {"bpm": 150},
  "milestones": [{"id": "m1", "desc": "170 BPM 60 s", "due": "2026-11-30"},
                 {"id": "m2", "desc": "riff ze zmianą strun 180", "due": "2027-01-15"}],
  "min_touch_days": 3, "created_from": "user",
  "interview": "Zwięzły zapis: baseline 150 (test na zimno), napięcie w przedramieniu od 160, cel: Battery/MoP.",
  "exercises": [{"title": "Interwały 60/30 ósemki", "technique": "downpicking", "subdivision": "8ths",
                 "bpm_start": 150, "bpm_target": 200, "stage": "speed",
                 "description": "60 s gry / 30 s przerwy, +5 BPM gdy luźno"}]
}
```
Metryka `custom` (np. rubryka 1–5 nagrania) → `baseline: {"value": 2}` i pomiary `gt path metric <id> <wartość>`.
Metryka `song_status` → target = indeks statusu (`backlog`0 … `performance_ready`3 … `maintenance`4) i
utwór dodany z `path_id`.
