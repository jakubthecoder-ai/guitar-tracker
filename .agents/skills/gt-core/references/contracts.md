# Kontrakty orkiestrator ↔ subagenci

Subagenci są **bezstanowi**: wszystko, czego potrzebują, jest w wejściu albo w `gt`. Każde wywołanie to jedno
zadanie. Subagent nie rozmawia z użytkownikiem – pytania zwraca w `questions`.

## Wejście (orkiestrator → subagent)
```json
{
  "task": "plan_block | create_exercises | retro | assess_deadline | placement | new_path | write_report",
  "path_id": "downpicking-200-bpm",
  "as_of": "2026-10-12",
  "inputs": {
    "slot": {"minutes": 25, "exercises": [{"exercise_id": "…", "stage": "speed", "bpm_next": 177}]},
    "answers": [{"q": "Najwyższe czyste tempo ósemek przez 60 s?", "a": "ok. 150"}],
    "goal_text": "chcę zagrać Master of Puppets", "proposal_id": null, "accept_warnings": false
  },
  "constraints": {"minutes": 25, "stage": null, "focus": null, "light_mode": false},
  "output_schema": "gt-contract-v1"
}
```

## Wyjście (subagent → orkiestrator) – jeden blok JSON na końcu odpowiedzi
```json
{
  "status": "ok | needs_input | error",
  "path_id": "downpicking-200-bpm",
  "actions_taken": ["gt exercise add … → ok", "gt path retro … → ok"],
  "block": {
    "minutes": 25,
    "items": [
      {"exercise_id": "…", "title": "Interwały 60/30", "minutes": 12, "mode": "interleave",
       "bpm_plan": [170, 174, 177], "cue": "Ruch z nadgarstka, kostka płytko; przy napięciu wróć o 10 BPM"},
      {"song_id": "metallica-battery", "minutes": 8, "mode": "block", "bpm_plan": [150],
       "cue": "Główny riff w pętli, 70% tempa"}
    ]
  },
  "questions": [
    {"id": "q7", "text": "Najwyższe tempo ósemek downpickingiem przez 60 s bez napięcia?", "type": "number",
     "options": null, "why": "baseline dla metryki"}
  ],
  "summary_for_user": "1–3 zdania w głosie mentora",
  "signals": [{"type": "new_path_idea", "detail": "rytm: gubisz 1 w 7/8"}]
}
```
- `block` tylko dla `plan_block`; `questions` tylko przy `needs_input`.
- `actions_taken` wymienia każdą komendę zapisującą i jej wynik (`ok`/błąd).
- `error` → `summary_for_user` wyjaśnia problem; orkiestrator nie zapisuje nic w imieniu subagenta.

## Plan commit (orkiestrator → `gt plan commit --from '<json>'`)
```json
{"minutes": 60, "rationale": "Blues zaniedbany 4 dni; downpicking blisko kamienia m1",
 "blocks": [
   {"start_min": 0, "minutes": 5, "kind": "warmup", "title": "Rozgrzewka + test na zimno 170"},
   {"start_min": 5, "minutes": 4, "kind": "path", "path_id": "…", "exercise_id": "…", "bpm": 170, "cue": "…"},
   {"start_min": 9, "minutes": 4, "kind": "path", "path_id": "…", "exercise_id": "…", "cue": "…"}
 ]}
```
`kind`: `warmup | path | review | music | break`. Bloki rotacji tej samej pary ćwiczeń powtarzaj jako osobne
bloki (każdy można odhaczyć w raporcie).
