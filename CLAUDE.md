@AGENTS.md

## Claude Code

- Persona mentora jako główny wątek: `claude --agent orchestrator` (model Opus; deleguje do subagentów na
  Sonnecie/Haiku zdefiniowanych w `.claude/agents/`, generowanych przez `tools/sync_harnesses.py`).
- Bez `--agent`: skill `gt-session` prowadzi ten sam przepływ z głównego wątku – deleguj przez narzędzie Agent
  do `path-coach` itd. zamiast generować ćwiczenia samodzielnie.
- Wywołania `path-coach` dla kilku ścieżek rób równolegle (kilka wywołań Agent w jednej wiadomości).
- Pytania z `needs_input` zadawaj przez AskUserQuestion, gdy mają zamknięte opcje; otwarte – zwykłym tekstem.
