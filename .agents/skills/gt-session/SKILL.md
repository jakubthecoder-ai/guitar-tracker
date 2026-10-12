---
name: gt-session
description: Prowadzenie sesji ćwiczeń w guitar-trackerze – plan dnia z gt plan, równoległe wywołania path-coach dla każdej ścieżki, przeplatanie bloków, zatwierdzenie (gt plan commit), start/log/test na zimno/koniec sesji. Używaj, gdy gitarzysta chce teraz ćwiczyć („mam 45 minut”, „zagrajmy”).
metadata:
  project: guitar-tracker
---

# gt-session

Wymaga `gt-core`. Wykonuje orkiestrator; generowanie treści bloków deleguje do `path-coach`.

## 1. Przygotowanie
- `gt ingest` (eksporty z raportu) → `gt state`. Otwarta sesja z wczoraj → zapytaj, czy ją zamknąć (`gt session end`).
- Ustal czas (domyślnie 60 min) i ewentualne preferencje („dziś tylko blues” → `--paths`).

## 2. Szkielet
`gt plan --minutes N` zwraca: `selected` (ścieżki + powody), `slots` (rozgrzewka z `cold_checks`, sloty ścieżek
z ćwiczeniami, `bpm_next`, `needs_exercises`, slot powtórek/muzyki), `warnings`, `mode` (`light` przy bólu).
Ostrzeżenia przekaż użytkownikowi na początku. Skrócenie przez limit objętości można pominąć tylko na wyraźne
życzenie użytkownika: `gt plan --minutes N --ignore-volume-cap` (innych flag „force” plan nie ma).

## 3. Bloki od coachów (równolegle)
Dla każdego slotu `path` jedno wywołanie `path-coach`:
`{"task": "plan_block", "path_id": …, "as_of": …, "inputs": {"slot": <slot z gt plan>}, "constraints": {"minutes": …, "light_mode": mode == "light"}}`.
Bez subagentów: wykonaj `agents/path-coach.md` inline dla każdej ścieżki po kolei.

## 4. Złożenie osi czasu
- 0′: rozgrzewka 3–5 min → test na zimno pozycji z `cold_checks` (bez wcześniejszego rozgrywania).
- Elementy `mode: block` (`learn`) w całości, jeden po drugim.
- Elementy `interleave` z różnych ścieżek: rotacje 3–5 min (A→B→C→A…), 2–4 elementy w cyklu.
- Mikroprzerwa co ~20 min. Na końcu powtórki `maintain` + blok muzyczny.
- Suma minut = plan. Przedstaw tabelką (start, min, co, BPM, wskazówka) + 1–2 zdania „dlaczego dziś”.

## 5. Zatwierdzenie i start
Po akceptacji/edycji: `gt plan commit --from '<json>'` – JSON inline w pojedynczych cudzysłowach (format:
`gt-core/references/contracts.md`). Potem
`gt session start --minutes N`. Zaproponuj `gt serve --open` (odhaczanie w raporcie na żywo) albo logowanie
w czacie.

## 6. W trakcie i na koniec
- Test na zimno: `gt session cold-check <ex_id> --bpm B` (`--not-clean`, gdy się nie udało).
- Log: `gt session log` (skill `gt-log`), dopytaj o brakujące liczby (BPM, czyste powtórzenia, napięcie).
- Ból → `gt session pain` i przerwij intensywne bloki.
- `gt session end --rating R` → przedstaw `stage_suggestions`; po zgodzie `gt exercise stage …`.
- Krótkie podsumowanie: co poszło, co jutro na zimno.
