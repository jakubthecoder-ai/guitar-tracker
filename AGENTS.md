# Guitar Tracker – instrukcje dla agentów

Mentor gitarowy dla samouka (rock, metal, blues, prog metal): wywiad wstępny → ścieżki (jedna ścieżka = jeden
cel = jeden temat) → sesje przeplatające ścieżki → tracking, ćwiczenia, utwory, żywy profil, raport HTML.
Ten plik czytają wszystkie harnessy (Claude Code, Codex, Gemini CLI, OpenCode, Cursor, Copilot).

## Zasady nadrzędne

1. **Stan tylko przez `gt`.** Wszystkie dane żyją w `$GT_HOME` (domyślnie `~/.guitar-tracker`) jako dziennik
   zdarzeń. Nigdy nie edytuj plików w `$GT_HOME` ręcznie, nie wymyślaj liczb (BPM, minuty, poziomy) – zapisuj je
   komendami `gt`, a odczytuj z `gt state`, `gt path show`, `gt plan`. Pliki `.md` w `$GT_HOME` są widokami
   generowanymi z dziennika.
2. **Jedna ścieżka = jeden cel = jeden temat.** Jedna metryka główna, jedna oś taksonomii. Cel złożony rozbij na
   kilka ścieżek. `gt path create` to egzekwuje.
3. **Decyzje liczbowe podejmuje skrypt.** Które ścieżki i ile minut – `gt plan`. Agenci decydują *co* grać i *jak*
   (ćwiczenia, wskazówki, kolejność rotacji).
4. **Bez zmyślania faktów muzycznych.** Tempo/strój/sekcje utworu, których nie potwierdziło źródło, oznaczaj
   „ok.”/„do weryfikacji”. Nie dawaj tabulatur z pamięci – linkuj.
5. **Bezpieczeństwo przed ambicją.** Rozgrzewka, mikroprzerwy, limit przyrostu objętości, reakcja na ból
   (szczegóły: `.agents/skills/gt-core/references/safety.md`).
6. **Język:** po polsku, terminologia techniczna po angielsku (palm mute, alternate picking, sweep, legato).

## Uruchamianie `gt`

`gt` to CLI w Pythonie (stdlib). Jeśli nie ma go w PATH, użyj `<repo>/bin/gt`. Instalacja globalna:
`ln -s <repo>/bin/gt ~/.local/bin/gt`. Każda komenda zwraca JSON (`"ok": true/false`). Opcja `--actor <rola>`
oznacza, kto zapisał zdarzenie (np. `--actor path-coach`). Ściąga komend: `.agents/skills/gt-core/SKILL.md`.

## Architektura wieloagentowa

Drogi model tylko orkiestruje; pracę wykonują tańsi subagenci. Topologia płaska: orkiestrator deleguje
bezpośrednio, subagenci nie wołają innych subagentów.

| Rola | Prompt | Tier | Zadanie |
|---|---|---|---|
| orchestrator | `agents/orchestrator.md` | top | rozmowa, routing, `gt plan`, przeplatanie bloków, zatwierdzanie |
| path-coach | `agents/path-coach.md` | mid | jedna ścieżka (podana jako `path_id`): blok na dziś, ćwiczenia, retro |
| placement-interviewer | `agents/placement-interviewer.md` | mid | wywiad wstępny → profil + propozycje ścieżek |
| path-interviewer | `agents/path-interviewer.md` | mid | wywiad tematyczny nowej ścieżki → `gt path create` |
| song-scout | `agents/song-scout.md` | mid | dobór utworów (komfort / cel / stretch) z weryfikacją |
| profile-keeper | `agents/profile-keeper.md` | low | sygnały postępu/braku postępu → zmiany profilu |
| report-builder | `agents/report-builder.md` | low | komentarz mentora + raport HTML |
| audio-analyst | `agents/audio-analyst.md` | low | analiza timingu nagrań (`gt analyze`) |

Kontrakt przekazania (wejście/wyjście JSON): `.agents/skills/gt-core/references/contracts.md`.
Subagenci nie rozmawiają z użytkownikiem bezpośrednio: gdy potrzebują odpowiedzi, zwracają
`status: "needs_input"` z pytaniami, a orkiestrator je zadaje i woła subagenta ponownie z odpowiedziami.

**Harness bez subagentów** (claude.ai, Desktop, inline): orkiestrator wykonuje rolę sam – czyta
`agents/<rola>.md` i stosuje go w miejscu wywołania, zachowując ten sam kontrakt.

**Codex:** subagentów uruchamiaj jawnie – przy każdej sesji planowania wywołaj `path-coach` osobno dla każdej
wybranej ścieżki (równolegle), zamiast samemu generować ćwiczenia.

## Skille

W `.agents/skills/` (Claude Code widzi je przez symlink `.claude/skills`):
`gt-core` (zasady, kontrakty, taksonomia, pedagogika), `gt-placement`, `gt-new-path`, `gt-session`, `gt-log`,
`gt-report`, `gt-retro` (sygnały, żywy profil), `gt-songs` (dobór i weryfikacja utworów), `gt-analyze` (analiza nagrań).

## Dla deweloperów

- Testy: `python3 -m unittest discover tests`
- Prompty ról edytuj w `agents/*.md` + `agents/roster.json`, potem `python3 tools/sync_harnesses.py`
  (generuje `.claude/agents/*.md`). Nie edytuj plików generowanych.
- Kod rdzenia: `gt/` (stdlib only). Logika liczbowa należy do `gt`, nie do promptów.
