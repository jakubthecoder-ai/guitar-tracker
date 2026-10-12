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

## Co umie

| Chcesz… | Powiedz mentorowi | Pod spodem |
|---|---|---|
| zacząć | „poznajmy się” | wywiad wstępny w rundach → profil L1–L5 w 8 osiach → propozycje ścieżek |
| nowy cel | „nowy cel: Master of Puppets w tempie” | wywiad tematyczny → baseline, kamienie milowe, realny termin |
| ćwiczyć | „mam 45 minut” | `gt plan` + coach każdej ścieżki → przeplatana sesja z testem na zimno |
| zalogować | „160 czysto 4 razy, napięcie 2” | `gt session log` / `cold-check` |
| utwór do grania | „co zagrać do downpickingu?” | lista startowa 44 utworów + weryfikacja Songsterr/MusicBrainz |
| ocenić nagranie | „oceń to nagranie: take.wav, 150 BPM” | `gt analyze`: timing ±ms, przyspieszanie, moment rozjazdu, porównanie z tabem GP |
| podsumowanie | „jak mi idzie?”, „retro tygodnia” | sygnały postępu/plateau/zaniedbań → żywy profil, raport HTML |

## Harnessy

| Harness | Jak uruchomić | Uwagi |
|---|---|---|
| **Claude Code** | `claude --agent orchestrator` | pełna orkiestracja: Opus + subagenci Sonnet/Haiku (`.claude/agents`) |
| **Codex CLI** | `codex` w katalogu repo | czyta `AGENTS.md`, `.agents/skills`, `.codex/agents/*.toml`; subagentów trzeba prosić jawnie |
| **Gemini CLI** | `gemini` w katalogu repo | `.gemini/settings.json` ładuje `AGENTS.md`; subagenci w `.gemini/agents` (bez zagnieżdżania) |
| **OpenCode** | `opencode`, agent `orchestrator` (Tab) | `.opencode/agents`; modele Claude ustawione per rola |
| **Cursor** | agent w katalogu repo | czyta `.claude/agents` i `.agents/skills` bezpośrednio |
| **GitHub Copilot** | custom agent `orchestrator` | `.github/agents/*.agent.md` |
| **Claude Desktop / inne MCP** | serwer `gt_mcp.py` (niżej) | bez shella i subagentów: prompty `mentor`, `placement`, `new_path`, `practice`, `retro` |

Modele per rola i harness: `agents/roster.json` → `python3 tools/sync_harnesses.py` (pliki agentów są generowane;
nie edytuj ich ręcznie).

### MCP (Claude Desktop, claude.ai przez lokalny serwer, dowolny klient MCP)

Wymaga [uv](https://docs.astral.sh/uv/). Konfiguracja (np. `claude_desktop_config.json`, `.cursor/mcp.json`,
`.gemini/settings.json` → `mcpServers`):

```json
{"mcpServers": {"guitar-tracker": {
  "command": "uv", "args": ["run", "--quiet", "/ścieżka/do/guitar-tracker/gt_mcp.py"],
  "env": {"GT_HOME": "/home/ty/.guitar-tracker"}}}}
```

Codex (`~/.codex/config.toml`):

```toml
[mcp_servers.guitar-tracker]
command = "uv"
args = ["run", "--quiet", "/ścieżka/do/guitar-tracker/gt_mcp.py"]
env = { GT_HOME = "/home/ty/.guitar-tracker" }
```

27 narzędzi (stan, profil, ścieżki, plan, sesja, utwory, raport), 5 promptów i zasoby z treścią skilli i ról.

### Analiza nagrań

`gt analyze take.wav --exercise <id> --bpm 160` (albo `--gp riff.gp5`). Pierwsze uruchomienie instaluje przez
`uv` numpy/librosa/PyGuitarPro. Nagrywaj czysty sygnał DI, klik tylko w słuchawkach. Mierzy timing (początki
dźwięków), nie brzmienie.

## Architektura

```
            ┌────────────────────────────┐
 użytkownik │ orchestrator (Opus)        │  rozmowa, routing, przeplatanie, zatwierdzanie
 ─────────► │ persona mentora            │
            └──┬──────┬──────┬──────┬────┘
               │      │      │      │      subagenci (bezstanowi, kontrakt JSON, needs_input)
     path-coach×N  placement-/path-  song-scout  profile-keeper, report-builder,
       (Sonnet)    interviewer       (Sonnet)    audio-analyst (Haiku)
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
| `.agents/skills/` | skille: `gt-core`, `gt-placement`, `gt-new-path`, `gt-session`, `gt-log`, `gt-report`, `gt-retro`, `gt-songs`, `gt-analyze` |
| `.claude/agents/`, `.codex/agents/`, `.gemini/agents/`, `.opencode/agents/`, `.github/agents/` | generowane z `agents/` – nie edytuj ręcznie |
| `gt_mcp.py`, `gt_audio.py` | serwer MCP i analiza nagrań (skrypty uv z zależnościami inline) |
| `tests/` | `python3 -m unittest discover tests` (testy audio i MCP wymagają `uv`; pominiesz je: `GT_TEST_AUDIO=0 GT_TEST_MCP=0`) |
| `reports/`, `research_notes/` | raport badawczy (pedagogika, programy nauki, źródła utworów, standardy harnessów) |

## Zastrzeżenia

Progi (krok BPM, interwały powtórek, limit objętości) to rozsądne wartości domyślne, a nie wyniki badań na
gitarzystach – można je zmienić w `~/.guitar-tracker/config.json`. Narzędzie nie zastępuje lekarza ani
fizjoterapeuty: ból, drętwienie lub utrata kontroli palców to sygnał do przerwy i konsultacji.
