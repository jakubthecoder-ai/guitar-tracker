---
name: gt-core
description: Fundament guitar-trackera (mentor gitarowy rock/metal/blues/prog). Zasady stanu, ściąga komend CLI gt, kontrakty JSON między orkiestratorem a subagentami, taksonomia umiejętności L1–L5, reguły pedagogiczne i bezpieczeństwa. Ładuj przed każdą pracą z gt, ścieżkami, sesjami lub profilem gitarzysty.
metadata:
  project: guitar-tracker
---

# gt-core

## Zasady
- Stan = dziennik zdarzeń w `$GT_HOME` (domyślnie `~/.guitar-tracker`). Zapis i odczyt **tylko** przez `gt`.
  Nie edytuj plików w `$GT_HOME`, nie wymyślaj liczb.
- Jedna ścieżka = jeden cel = jeden temat (jedna `topic_axis`, jedna `primary_metric`).
- Skrypt decyduje *które ścieżki i ile minut* (`gt plan`), agent – *co i jak*.
- Każda komenda zwraca JSON z `"ok"`. Przy `"ok": false` przeczytaj `error`/`details` i popraw wejście.
- Oznaczaj autora: `gt --actor <rola> …`. `--date RRRR-MM-DD` tylko do logów z przeszłości.
- `gt` nie w PATH → `<repo guitar-tracker>/bin/gt`.

## Ściąga komend
| Cel | Komenda |
|---|---|
| Przegląd | `gt state` · pełny stan: `gt state --full` |
| Profil | `gt profile show` · `gt profile init --from '<json>'` · `gt profile change --from '<json>'` · `gt profile confirm|reject <id>` · `gt profile history` |
| Ścieżki | `gt path list` · `gt path show <id>` · `gt path propose --from '<json>'` · `gt path check --from '<json>'` · `gt path create --from '<json>' [--force]` |
| Zmiany ścieżki | `gt path pause|resume|close|drop|review <id> --reason …` · `gt path extend <id> --deadline D --reason …` · `gt path priority <id> 1-5` · `gt path milestone <id> <milestone_id>` · `gt path metric <id> <wartość>` · `gt path retro <id> --from '<json>'` |
| Ćwiczenia | `gt exercise list [--path id]` · `gt exercise add --path id --from '<json>'` · `gt exercise stage <ex_id> <stage> --reason …` |
| Plan | `gt plan --minutes N [--paths a,b]` · `gt plan commit --from '<json>'` · `gt plan show` |
| Sesja | `gt session start [--minutes N]` · `gt session log --exercise ID --minutes M --bpm B --clean-reps R [--burst X --rating 1-5 --tension 1-5 --note …]` · `gt session log --from '<json>'` (lista) · `gt session cold-check <ex_id> --bpm B [--not-clean]` · `gt session end [--rating --note]` · `gt session pain --note <gdzie> --rating <1-5>` |
| Utwory | `gt song add --from '<json>'` · `gt song status <song_id> <status>` · `gt song list` |
| Raport | `gt note -` (komentarz mentora) · `gt report [--open]` · `gt serve --open` (zapis z HTML na żywo) |
| Import | `gt ingest` (eksporty z raportu: `$GT_HOME/inbox`, `~/Downloads/gt-events-*.json`) |
| Kontrola | `gt validate` · `gt derive` |

**Przekazywanie JSON:** zawsze inline w pojedynczych cudzysłowach: `gt path create --from '{"title": "…"}'`.
Nie używaj heredoców (`<<EOF`) ani plików tymczasowych – harnessy blokują je jako ryzykowne. Apostrof w tekście
zastąp znakiem ’. `--from '<json>'` (stdin) i ścieżka pliku też działają, gdy harness na to pozwala.

## Referencje (czytaj w razie potrzeby)
- `references/contracts.md` – kontrakty wejścia/wyjścia subagentów, przykłady JSON.
- `references/taxonomy.md` – 8 osi, poziomy L1–L5, progi tempa.
- `references/pedagogy-rules.md` – struktura sesji, stadia elementów, reguły BPM, przeplatanie, powtórki, cele.
- `references/safety.md` – rozgrzewka, objętość, ból, czerwone flagi.
