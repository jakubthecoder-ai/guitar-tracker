---
name: gt-log
description: Logowanie ćwiczeń gitarowych do guitar-trackera z opisu w języku naturalnym („grałem 15 min downpicking, 160 czysto, burst 175”) oraz import zmian z raportu HTML (gt ingest). Używaj zawsze, gdy użytkownik relacjonuje, co zagrał, lub zgłasza ból.
metadata:
  project: guitar-tracker
---

# gt-log

Wymaga `gt-core`.

## Mapowanie wypowiedzi → komenda
| Użytkownik mówi | Komenda |
|---|---|
| „15 min interwałów, 160 czysto 4 razy, burst 175, napięcie 3” | `gt session log --exercise <id> --minutes 15 --bpm 160 --clean-reps 4 --burst 175 --tension 3` |
| „na zimno 165 weszło czysto” | `gt session cold-check <id> --bpm 165` |
| „na zimno 170 się sypało” | `gt session cold-check <id> --bpm 170 --not-clean` |
| „pół godziny jamowałem bluesa” | `gt session log --path <id> --type jam --minutes 30` |
| „przegrałem Battery całe z nagraniem” | `gt session log --song <id> --type runthrough --minutes 6 --rating 4` |
| „rozgrzewka 5 min” | `gt session log --type warmup --minutes 5` |
| kilka pozycji naraz | `gt session log --from '<json>'` z listą obiektów (`exercise_id`/`song_id`/`path_id`, `practice_type`, `minutes`, …) |
| „boli mnie nadgarstek” | `gt session pain --note "nadgarstek" --rating <1-5>` + zalecenia z `safety.md` |
| „wczoraj grałem…” | dodaj `--date RRRR-MM-DD` |

- ID ćwiczeń/utworów/ścieżek bierz z `gt state --full` lub `gt path show`; nie zgaduj – przy dwuznaczności dopytaj.
- „Czysto” = bez błędów i bez napięcia; `--clean-reps` to liczba takich powtórzeń w najwyższym tempie.
- Brak liczby → zapytaj albo pomiń pole; nigdy nie wpisuj szacunku jako pomiaru.

## Import z raportu HTML
`gt ingest` wczytuje `$GT_HOME/inbox/*.json` i `~/Downloads/gt-events-*.json` (duplikaty ignorowane, pliki
przenoszone do `inbox/processed`). Zgłoś `added` i ewentualne `rejected`.
