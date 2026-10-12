# guitar-tracker

Mentor gitarowy dla samouka (rock, metal, blues, prog metal) zbudowany z **agentów AI, skilli i deterministycznego
CLI**. Działa w Claude Code; projektowany tak, by przenieść go do innych harnessów (Codex, Gemini CLI, OpenCode,
Cursor, Copilot, claude.ai przez MCP).

- **Wywiad wstępny** → profil w 8 osiach (L1–L5) i propozycje ścieżek.
- **Ścieżki**: jedna ścieżka = jeden cel = jeden temat, z baseline, kamieniami milowymi i realnym terminem.
- **Sesje**: skrypt wybiera ścieżki i minuty, subagenci układają ćwiczenia, orkiestrator przeplata je w jedną sesję.
- **Tracking**: tempo czyste (test na zimno), kandydaci, bursty, trend i projekcja do terminu.
- **Żywy profil**: zmiany z historią i potwierdzaniem.
- **Interaktywny raport HTML**: wykresy, plan z odhaczaniem, log, utwory, kalendarz.

## Szybki start

```bash
git clone https://github.com/jakubthecoder-ai/guitar-tracker.git
ln -s "$PWD/guitar-tracker/bin/gt" ~/.local/bin/gt   # CLI w PATH (Python 3.10+, bez zależności)
gt init                                             # dane w ~/.guitar-tracker (własny git)
cd guitar-tracker && claude --agent orchestrator    # mentor w Claude Code
```

Potem po prostu rozmawiaj: „poznajmy się”, „nowy cel: Master of Puppets w tempie”, „mam 45 minut”,
„zagrałem 15 min downpickingu, 165 czysto”, „jak mi idzie?”.

Raport: `gt report --open` (offline, zmiany eksportujesz do pliku i wczytujesz `gt ingest`) albo
`gt serve --open` (zapis z przeglądarki na żywo, tylko 127.0.0.1 z tokenem).

## Architektura

```
            ┌────────────────────────────┐
 użytkownik │ orchestrator (Opus)        │  rozmowa, routing, przeplatanie, zatwierdzanie
 ─────────► │ persona mentora            │
            └──┬──────┬──────┬──────┬────┘
               │      │      │      │      subagenci (bezstanowi, kontrakt JSON, needs_input)
     path-coach×N  placement-  path-     report-builder
       (Sonnet)    interviewer interviewer  (Haiku)
               │      │      │      │
               ▼      ▼      ▼      ▼
            ┌────────────────────────────┐
            │ gt CLI (Python stdlib)     │  jedyny zapis stanu, cała logika liczbowa
            └────────────┬───────────────┘
                         ▼
          ~/.guitar-tracker/events/*.jsonl   dziennik zdarzeń (źródło prawdy)
          → widoki .md, derived/state.json, reports/latest.html
```

- **Stan poza modelem**: dziennik zdarzeń + deterministyczne `gt`. LLM nigdy nie zmienia liczb ręcznie.
- **Skrypt decyduje *co i ile*** (wybór ścieżek, minuty, tempo następnego kroku, limity bezpieczeństwa),
  **agenci decydują *jak*** (ćwiczenia, wskazówki, kolejność rotacji).
- **Przenośność**: skille w standardzie Agent Skills (`.agents/skills`, symlink `.claude/skills`), wspólne
  instrukcje w `AGENTS.md`, prompty ról w `agents/` → `tools/sync_harnesses.py` generuje pliki per harness.

## Struktura

| Ścieżka | Zawartość |
|---|---|
| `gt/` | CLI: zdarzenia, stan, ścieżki, planowanie, raport HTML, serwer zapisu |
| `agents/` | kanoniczne prompty ról + `roster.json` (tier modelu, narzędzia, delegacje) |
| `.agents/skills/` | skille: `gt-core`, `gt-placement`, `gt-new-path`, `gt-session`, `gt-log`, `gt-report` |
| `.claude/agents/` | generowane z `agents/` – nie edytuj ręcznie |
| `tests/` | `python3 -m unittest discover tests` |
| `reports/`, `research_notes/` | raport badawczy (pedagogika, programy nauki, źródła utworów, standardy harnessów) |

## Zastrzeżenia

Progi (krok BPM, interwały powtórek, limit objętości) to rozsądne wartości domyślne, a nie wyniki badań na
gitarzystach – można je zmienić w `~/.guitar-tracker/config.json`. Narzędzie nie zastępuje lekarza ani
fizjoterapeuty: ból, drętwienie lub utrata kontroli palców to sygnał do przerwy i konsultacji.
