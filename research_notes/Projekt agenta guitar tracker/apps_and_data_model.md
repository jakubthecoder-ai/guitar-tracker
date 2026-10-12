# Guitar Practice Trackers, AI Coaches, and a Data Model for an LLM-Driven Tracker (as of Oct 2026)

Research note: about 18 search and fetch calls. Most app facts come from App Store or product listings, which are vendor-written. I could not reach Reddit threads directly: searches restricted to Reddit-style phrasing returned no Reddit results. User sentiment is therefore thin and comes mostly from editorial roundups and forums.

## Which apps exist and what goal/deadline/tracking/routine-generation/song-recommendation features do they have? What do users praise/complain about?

### Takeaway
A wave of small 2025–2026 indie iOS and web trackers (Practimo, Repétude, PracticeQuest, MusMaj, Arietta, FretPulse, AxeLog, Practis) has converged on a common set of features:
- routines made of timed exercises
- BPM history for each exercise, with a target tempo
- streaks and weekly minutes
- song or repertoire status

Few of them model explicit deadlines (Practis does, with program lists for recitals, exams and auditions). Only AxeLog and Practis use an LLM to generate a plan from goals, recent sessions and repertoire. The big learning platforms (Yousician, Fender Play, Rocksmith+) teach content and are not personal trackers. Their complaints center on plateaus and beginner-only content, not on tracking.

### Cited Findings

**Practimo**
- Routines are built by dragging focus items (technique, scales, song, sight-reading) into order. A guided session has a per-item timer, a metronome and quick notes.
- "Rotation surfaces what you've been neglecting, so practice never goes stale." This is the neglect-detection pattern.
- Before/after recordings, a streak, weekly minutes, and a 12-week progress view (Pro). A Progress tab shows recent sessions and reflections.
- No goal or deadline feature is described, and no per-exercise BPM logging.
- One-time Pro unlock (CHF 18), no account, data stays on the device. v1.0 shipped in July 2026 and has no ratings yet.
- Source: [App Store – Practimo](https://apps.apple.com/ch/app/practimo-practice-tracker/id6782497348)

**Practis (any instrument)**
- "Ask Practis" builds session plans from your repertoire and goals.
- The Smart Session Planner uses repertoire status and past practice gaps, and flags neglected pieces. Its rotation means "no piece is quietly dropped."
- Program lists for recitals, exams and auditions, with "what's due". This is the clearest deadline model found.
- Each piece is tracked from early learning to performance-ready and has its own practice history. Daily goal dial and streaks.
- Free for up to 5 pieces. PRO is $3.99 a month.
- Source: [Practis listing](https://mwm.ai/apps/practis-music-practice/6787937756)

**AxeLog – AI Guitar Coach**
- One-tap AI practice plan "based on your skill profile, recent sessions, active goals, and songs". Plans are editable before starting: swap exercises, adjust time.
- An AI chat coach with persona voices (Studio Pro, Shred Dad, Metalhead).
- A six-axis "skill hexagon" (Chords, Picking, Rhythm, Lead, Ear, Theory) that sessions update.
- Each session ends with a self-rating and an AI-written report. BPM logging per exercise with a tempo chart.
- **At most 3 active long-term goals.**
- Songs move from "learning" to "mastered" with BPM, tuning notes and recordings. No song recommendation is described.
- 100+ exercises and 20+ routines, a heatmap, leagues and data export.
- $39.99 a year or $79.99 lifetime. Rated 4.6 from 34 ratings. Praised as organized and polished. Complaints were a Pro purchase bug and a request for left-handed mode.
- Source: [App Store – AxeLog](https://apps.apple.com/app/id6758068428)

**Repétude**
- Routines with a set order, automatic transitions and breaks.
- The metronome remembers BPM for each exercise. A tempo goal can be tracked over weeks and months.
- Free tier: 1 routine with up to 8 exercises. Pro: $2.99 a month, $19.99 a year or $29.99 lifetime. iCloud backup.
- Source: [App Store – Repétude](https://apps.apple.com/app/id6756016198)

**FretPulse (web)**
- Builds a daily routine for your skill level, focus areas and schedule, with on-demand regeneration.
- A "vault" of curated exercises and prebuilt routines.
- "Mastery per exercise", progressive overload for speed, analytics on BPM gains, and streaks. Pitched at plateaued guitarists.
- No user reviews yet.
- Source: [Product Hunt – FretPulse](https://www.producthunt.com/products/fretpulse)

**Other trackers**
- **MusMaj Practice** (iOS, August 2026) tracks stable BPM, peak BPM, reps and success rate for each exercise, plus progress toward a target tempo. [AppGoblin – MusMaj](https://appgoblin.info/apps/6794310768) (search snippet only)
- **Arietta** tracks BPM per section of each piece, with a chart per piece and a weekly practice goal. [App Store – Arietta](https://apps.apple.com/app/id6760299792) (search snippet only)
- **PracticeQuest** is gamified: XP, streaks, daily quests and weekly time targets. No BPM chart is evident. [App Store – PracticeQuest](https://apps.apple.com/ph/app/practicequest/id6758678759) (search snippet only)
- **Riff Quest** (web) logs sessions on a calendar chart, has levels based on real practice time, and has a song difficulty and progress system (working on / mastered). [AlternativeTo – Riff Quest](https://alternativeto.net/software/riff-quest/about)
- **Music Routine: daily practice** (iOS) is a list of exercises, each with a duration and speed, played with a built-in metronome. No account is needed. [App Store – Music Routine](https://apps.apple.com/app/id6444836642)
- **Guitar Practice Tracker** (guitaristnextdoor.com, free browser tool) logs time and shows a 30-day BPM progress chart. Data is stored locally unless you register. [guitaristnextdoor](https://guitaristnextdoor.com/?p=56696) (search snippet only)

**Modacity**
- Metronome plus drone ("metrodrone"), a timer for each practice item, and recording.
- A "Deliberate Practice" button asks questions to make your goal specific.
- The free tier limits notes per item.
- Sources: [Clarinet Chronicles](https://clarinet.org/clarinet-chronicles-four-must-apps-musicians/), [Ensemble Schools](https://www.ensembleschools.com/blog/apps-for-musicians/)
- The founder's name conflicts between sources: trustburn says Marc Gelfo, while The Strad's July 2026 preview names Michael Propper. Source quality varies, and trustburn looks unreliable. [The Strad](https://www.thestrad.com/for-subscribers/products-july-2026-modacity-practice-app/21383.article)

**Justin Guitar**
- A Daily Practice Routine combines module exercises into a 10-minute session.
- The separate Note Trainer app uses "smart repetition to reinforce weak spots", a spaced-repetition pattern.
- Sources: [educationalappstore](https://www.educationalappstore.com/best-apps/5-best-guitar-learning-apps), [JustinGuitar Note Trainer](https://apps.apple.com/om/app/id6761114951)
- A user on the JustinGuitar forum built a riff-routine app with a metronome, a timer and riff screenshots. [JustinGuitar community](https://community.justinguitar.com/t/i-made-an-app-to-keep-track-of-my-practice-routine-and-i-would-love-to-receive-your-feedback/212897)

**Troy Grady – Cracking the Code**
- Slow-motion video analysis of picking technique, courses, interviews and personalized technique critiques.
- No practice-tracker tooling was found.
- Source: [parse.gl directory](https://parse.gl/brands/troygrady-com) (low-authority directory)

**Complaints about the big learning apps**
- Recurring complaints across Yousician, Fender Play and similar apps:
  - phone-mic pitch detection that misses correct notes
  - auto-renewing subscriptions that are hard to cancel
  - lessons that "plateau and repeat"
  - libraries that stall at beginner level
  - Source: [unstar.app 2026 ranking](https://unstar.app/blog/yousician-simply-piano-flowkey-fender-play-music-learning-apps-ranked-2026) (editorial, directional)
- Yousician "feels like a game that rewards repetition, not a course that builds skill". Fender Play has "tons of beginner content and almost nothing that takes you past it". (same source)
- A Yousician forum user praised it for "taking away your worries on what to practice". Rocksmith's Riff Repeater (loop and slow down a section) is praised. [guitarchalk](https://www.guitarchalk.com/fender-play-vs-rocksmith/), [equipboard](https://equipboard.com/posts/fender-play-vs-yousician)

### Inferences
- The industry-standard minimum feature set is:
  - an exercise with a current BPM, a target BPM and its BPM history
  - a routine as an ordered list of timed items
  - a session log with notes and a self-rating
  - song status as a learning → mastered ladder
  - streaks and minutes
- What distinguishes products: neglect-aware rotation (Practimo, Practis), deadline-driven program lists (Practis), LLM plan generation from state (AxeLog, Practis), and stable vs peak BPM (MusMaj). Peak BPM is the fastest you have managed; stable BPM is the tempo you can play cleanly every time. MusMaj's split matters because one "BPM" number exaggerates progress.
- AxeLog's cap of 3 active goals and Practis's "what's due" view are both worth copying. A small number of concurrent paths keeps the routine coherent.
- Song recommendation, meaning suggesting new repertoire that fits current skills and goals, is essentially absent from the trackers. It lives in the learning platforms (Yousician, Fender Play) and in tab or chord apps. This is an opening for an LLM.
- The main frustration with the big apps is plateau and beginner-only content. That points to a personal tracker focused on intermediate goals: speed targets, specific songs, deadlines.

### Gaps
- I found no feature details for Guitar Pro, Songsterr, Chordify or Moises in this pass. From general knowledge, and not verified here, these are tab, playback, stem and loop tools, not trackers.
- I found no feature details for Rocksmith+ progress tracking.
- No Reddit threads were retrieved from r/guitar, r/Guitar_Theory or r/metalguitar, so user praise and complaints for the indie trackers are missing. Most have no or few reviews.
- I could not confirm the features of Justin Guitar's "practice assistant".

## Open-source practice trackers on GitHub: schemas and approaches

### Takeaway
Open-source projects are few and small. All use the same three-entity core: routine, exercise, and session log with BPM. The most instructive "schema" for an LLM or git workflow comes from Obsidian users, who store per-session YAML lists of song, part, BPM and status in daily notes.

### Cited Findings
- **Virtuosity** (Android, GPL-3.0-or-later, github.com/ramzan/virtuosity) organizes routines of exercises, a session timer, session logs, and BPM graphs over time. Its entities are routines, exercises and practice-session logs with BPM. Field-level schema is not documented on F-Droid. [F-Droid – Virtuosity](https://f-droid.org/ko/packages/ca.ramzan.virtuosity/)
- **Musibuk** (github.com/sghoshal/musibuk) is a Node.js and MongoDB web app with bar graphs of time and BPM achieved per session over the last 7 days. Its license is unknown. [GitHub – musibuk](https://github.com/sghoshal/musibuk) (search snippet)
- **Trackstar** (Ruby gem) is a CLI practice tracker that writes a human-readable Markdown file per log entry, with built-in stats. [rubydoc – Trackstar](https://www.rubydoc.info/gems/trackstar)
- **Obsidian music practice journal:**
  - Each daily note has frontmatter with `date` and a `practiced:` list of `{song, part, bpm, status}`, where status is for example `solid` or `weak`.
  - Each song is its own note, with sections as headings.
  - Queries use Dataview or DataviewJS, for example `mostRecentPracticed(song, part)` returning "Last played at X bpm on DATE. Status: Y".
  - Pitfalls:
    - Dataview can't query backlinks to headings.
    - Inline `[bpm:: 120]` fields were "tedious".
    - Matching needs exact, consistent song and part names.
    - Dates must be ISO for sorting to work.
  - Source: [Obsidian forum](https://forum.obsidian.md/t/music-practice-journal-with-existing-plugins/114753)

### Inferences
- The Obsidian pitfalls carry over directly to a git and LLM design:
  - use stable IDs, not display names, as foreign keys
  - use ISO 8601 dates
  - keep per-set structured data in structured fields, not prose
- A song section should be a first-class entity with an ID such as `song-id#section-id`. Repertoire progress usually means sections, not whole songs, and Arietta also tracks BPM per section.

### Gaps
- I did not inspect actual repository source for Virtuosity or Musibuk, so their field-level schemas are not captured. Next step: read the Room entities in ramzan/virtuosity.
- I found no open-source project that uses JSONL or append-only logs for practice data.

## AI/LLM-based guitar coaches and ChatGPT/Claude practice planners: what worked, pitfalls

### Takeaway
Commercial LLM coaches (AxeLog, Practis's "Ask Practis") work by feeding the model structured state: skill profile, recent sessions, active goals, repertoire and neglect gaps. The model then returns an editable plan, and a post-session AI report closes the loop. I found no guitar-specific MCP server for practice planning. The documented pitfall of plain ChatGPT is confident factual errors in music theory.

### Cited Findings
- AxeLog's plan inputs are skill profile, recent sessions, active goals and songs. Its outputs are a segmented, editable plan and a guided session. Each session ends with a self-rating and an AI-written report. [App Store – AxeLog](https://apps.apple.com/app/id6758068428)
- Practis builds session plans from repertoire status and past practice gaps, and flags neglected pieces and what's due. [Practis listing](https://mwm.ai/apps/practis-music-practice/6787937756)
- **Guitar Mentor** offers "a complete practice session built from any song". [App Store – Guitar Mentor](https://apps.apple.com/app/id6774841462) (search snippet)
- **JamFlow** is a guitar tool that runs inside ChatGPT and requires GPT Plus. [Gumroad – JamFlow](https://eyewitness6.gumroad.com/l/JamFlow) (search snippet)
- **ChatGPT prompting advice:** set a role ("You are a guitar teacher") and give your level as context. An article claims a generic chatbot "can spit out a sensible regimen once you feed it your goals, lifestyle and availability". [Soundhouse](https://www.soundhouse.co.jp/en/contents/column/index?post=3117), [unite.ai](https://www.unite.ai/?p=260208)
- **Pitfall – accuracy:** ChatGPT told a guitarist that his correct listing of E major pentatonic had an extra note. It conceded only when challenged. [Six String Sage](https://sixstringsage.substack.com/p/is-chat-gpt-a-good-music-teacher)
- A guitar shop owner tested a chatbot for student-derailing errors and closed the account after one chat. The post is paywalled. [lsaguitarshop substack](https://lsaguitarshop.substack.com/p/misc-27-interacting-with-ai-5)
- **MCP landscape:**
  - No guitar practice-plan MCP was found.
  - A "Guitar Dojo" MCP listing appears commerce-oriented. [mcpbundles](https://www.mcpbundles.com/skills/guitardojo-mcp-dc23b97ea2)
  - The closest analogue is fitness coach MCPs ("opinionated AI training coach"), with persistent logs and adaptive plans. [glama.ai](https://glama.ai/mcp/servers/jq2xq7468j)
  - A Hooktheory MCP provides chord progression and theory data. (search summary; [lobehub](https://lobehub.com/mcp?q=progress))

### Inferences
- What worked:
  - The LLM gets a compact, current state snapshot rather than raw history.
  - The plan is editable and is not executed blindly.
  - Every session closes with a self-rating and reflection, which feeds the next plan.
- Pitfalls to design around:
  1. **Theory hallucinations.** Keep scales, chord shapes and tab facts in files you have checked, or in deterministic scripts, not in model memory.
  2. **State drift.** If the LLM rewrites state files freely, numbers can be silently altered. Prefer append-only logs plus derived summaries computed by script.
  3. **Overplanning.** Cap the number of active paths, as AxeLog caps goals at 3.
- The fitness-coach MCP pattern (log → derive metrics → adapt plan) maps cleanly to guitar: BPM is "load" and progressive overload is the tempo step.

### Gaps
- I found no detailed write-ups (blogs or Hacker News) of someone building a Claude- or ChatGPT-based guitar planner with persistent files.
- I found no Reddit evidence on how well GPT-made routines work in practice.

## Data model options and proposed entities

### Takeaway
Use a hybrid:
- **Markdown with YAML frontmatter** for slowly-changing, human- and LLM-edited entities: profile, paths, exercises, songs, reviews.
- **An append-only JSONL log** (or one Markdown file per session with frontmatter) for sessions and BPM sets.
- **A disposable SQLite or derived summary file**, generated by scripts, for queries.

The log is the source of truth for numbers. Current values are derived from it, never hand-edited.

### Cited Findings
- Obsidian users successfully store structured practice entries as YAML lists in daily notes and query them with Dataview. Inline fields in prose were tedious, and ISO dates and exact IDs were needed. [Obsidian forum](https://forum.obsidian.md/t/music-practice-journal-with-existing-plugins/114753)
- Trackstar writes one Markdown file per entry, readable by humans and parsable for stats. [rubydoc – Trackstar](https://www.rubydoc.info/gems/trackstar)
- Common Markdown frontmatter conventions use title, tags, status and updated fields per file. [smithery – markdown-frontmatter](https://smithery.ai/skills/ekuris-repos/markdown-frontmatter)
- Entity fields seen in products:
  - per-exercise stable BPM, peak BPM, reps, success rate and target ([MusMaj](https://appgoblin.info/apps/6794310768))
  - per-section BPM ([Arietta](https://apps.apple.com/app/id6760299792))
  - song status from learning to mastered, with BPM, tuning and recordings ([AxeLog](https://apps.apple.com/app/id6758068428))
  - program lists with due dates ([Practis](https://mwm.ai/apps/practis-music-practice/6787937756))
  - skill axes ([AxeLog](https://apps.apple.com/app/id6758068428))
  - reflections per session ([Practimo](https://apps.apple.com/ch/app/practimo-practice-tracker/id6782497348))

### Inferences

These are design reasoning, not sourced facts.

**Tradeoffs between formats**

**Markdown + YAML frontmatter**
- Strengths:
  - the best fit for LLM reading and writing
  - line-based git diffs
  - Obsidian-compatible
  - prose notes sit next to the structured fields
- Weaknesses:
  - querying across many files needs a parser
  - YAML type ambiguities (unquoted `no`, times)
  - when an LLM rewrites a whole file it can corrupt or drift other fields

**JSONL append-only**
- Strengths:
  - each event is one line, so git diffs are pure additions
  - no merge conflicts beyond appends
  - trivially parsed with `jq` or Python
  - immutable history allows recomputation
- Weaknesses:
  - less pleasant to read as prose
  - an LLM may mis-escape JSON, so validate with a JSON Schema in a pre-commit hook

**SQLite**
- Strengths: best for queries.
- Weaknesses:
  - binary, so diffs in git are useless
  - an LLM cannot read it without tools
  - Use it only as a regenerated cache, gitignored, or via a SQL dump.

**Obsidian / Logseq journals**
- Strengths: good human UX.
- Weaknesses: Logseq's block format and Dataview inline fields are tool-specific. Keep plain frontmatter so the files stay portable.

**Proposed layout**

```
tracker/
  profile.md                # assessment: level, skill axes 1-5, gear, time budget/day, weekly schedule, constraints
  paths/<path-id>.md        # goal
  exercises/<ex-id>.md      # exercise definition
  songs/<song-id>.md        # repertoire
  log/sessions.jsonl        # append-only, 1 line per session
  log/sets.jsonl            # optional: 1 line per exercise attempt (or embed in session)
  reviews/YYYY-Www.md       # weekly retro (LLM + human), monthly milestone check
  plan/today.md             # generated routine (ephemeral; committed for history)
  derived/state.json        # script-generated: current BPMs, last-practiced, neglect scores, deadline risk
  schema/*.json             # JSON Schemas for validation
```

**Entity sketches**

**Path** (`paths/<path-id>.md`):
```yaml
id: shred-16ths-160
title: Alternate picking 16ths at 160
status: active            # active|paused|done|dropped
priority: 3               # 1-5 weight
deadline: 2027-03-01
started: 2026-10-12
milestones:
  - {id: m1, desc: "16ths @120 clean", due: 2026-11-15, metric: {exercise: ex-3nps-scale, stable_bpm: 120}, done: null}
exercises: [ex-3nps-scale, ex-string-skip]
songs: [song-trooper]
min_touch_days: 3         # neglect threshold
```
The prose body holds the rationale and teacher notes.

**Exercise** (`exercises/<ex-id>.md`):
```yaml
id: ex-3nps-scale
skill_axis: picking
subdivision: 16th
bpm_start: 90
bpm_target: 160
bpm_step: 4               # progressive overload rule
promote_rule: "3 clean reps x2 sessions"
source: "tab/ref link"
```
Current BPM is not stored here. It is derived from the log.

**Song** (`songs/<song-id>.md`):
```yaml
id: song-trooper
artist: Iron Maiden
title: The Trooper
tuning: E standard
status: learning          # backlog|learning|polishing|performance_ready|maintenance
target_bpm: 160
sections:
  - {id: intro, status: solid, bpm_stable: 140}
  - {id: solo, status: weak}
```
- Section status could alternatively be derived from the log.
- Add `recommended_by` and `why` fields for LLM song suggestions.

**Session** (one JSONL line):
```json
{"id":"2026-10-12T19:05","date":"2026-10-12","minutes":45,"plan_ref":"plan/2026-10-12.md","items":[{"ref":"ex-3nps-scale","minutes":10,"bpm_stable":112,"bpm_peak":120,"clean_reps":3,"rpe":7,"note":"tension at 120"},{"ref":"song-trooper#solo","minutes":15,"bpm_stable":100,"status":"weak"}],"rating":4,"energy":3,"reflection":"..."}
```

**Review** (`reviews/YYYY-Www.md`):
- What improved: BPM deltas, computed by script.
- Paths at risk: projected time to target versus deadline.
- Neglected items.
- Changes to path priorities.
- The LLM writes a draft and the human confirms.

**Workflow rules**
- The LLM reads `profile.md`, active `paths/*`, `derived/state.json`, the last N sessions and the latest review. It writes `plan/today.md` and, after practice, appends one session line.
- Scripts recompute `derived/` and validate against the schemas, for example in a pre-commit hook.
- Git commits act as an audit trail of every change the LLM makes.

### Gaps
- I found no published benchmark comparing how well LLMs read or write YAML versus JSON versus JSONL for this use case. The tradeoffs above are reasoning, not measured results.
- I found no existing open schema standard for practice logs.

## Patterns for interleaving multiple goals in one daily routine

### Takeaway
Shipping products use three mechanisms:
- **Rotation with neglect surfacing:** Practimo, and Practis ("no piece quietly dropped").
- **Deadline / "what's due" prioritization:** Practis program lists.
- **Weakness-targeted repetition:** Justin Guitar Note Trainer's "smart repetition to reinforce weak spots", and AxeLog's skill-profile-driven plans.

A tracker can combine them in a weighted scoring function over active paths, within a fixed daily time budget.

### Cited Findings
- Practimo: "Rotation surfaces what you've been neglecting, so practice never goes stale." [App Store – Practimo](https://apps.apple.com/ch/app/practimo-practice-tracker/id6782497348)
- Practis: rotation "so no piece is quietly dropped". Its plans use "repertoire status and past practice gaps", and Ask Practis shows "what's due" for recitals and exams. [Practis listing](https://mwm.ai/apps/practis-music-practice/6787937756)
- JustinGuitar Note Trainer: short daily exercises with "smart repetition to reinforce weak spots". [App Store – Note Trainer](https://apps.apple.com/om/app/id6761114951)
- Justin Guitar's Daily Practice Routine is a fixed 10-minute combined session drawn from modules. [educationalappstore](https://www.educationalappstore.com/best-apps/5-best-guitar-learning-apps)
- AxeLog caps active goals at 3. Its plans are generated from skill profile, recent sessions, goals and songs. [App Store – AxeLog](https://apps.apple.com/app/id6758068428)
- FretPulse plans for "skill level, focus areas, and schedule" and uses progressive overload. [Product Hunt – FretPulse](https://www.producthunt.com/products/fretpulse)
- Generic practice advice warns against practicing without a plan and inconsistently. [guitarlessons.com](https://guitarlessons.com/guitar-lessons/guitar-lessons-for-beginners/5-huge-guitar-practice-mistakes/)

### Inferences

These are a proposed algorithm, not sourced facts.

**Daily routine structure**
- A fixed warm-up block of about 10%.
- Then slots filled by a score for each active path or item:
  - `score = priority_weight × (1 + days_since_last / min_touch_days) × deadline_urgency × weakness_factor`
  - `deadline_urgency` grows as the projected BPM trajectory falls short of the milestone due date. Projection is a linear or log fit over recent `bpm_stable`.
  - `weakness_factor` is boosted for items marked `weak` or with low clean-rep rates.
- An optional "maintenance" slot for performance-ready songs, on a spaced schedule (7 → 14 → 30 days).

**Rotation modes**
- Daily round-robin of 2–3 paths when time is short.
- An A/B day split, for example technique-heavy vs repertoire-heavy.
- Weekly quotas such as path X ≥ 90 minutes a week, tracked in `derived/state.json`.

**Neglect detection**
- Flag any active path or song section where `days_since_last > min_touch_days`.
- Force it into tomorrow's plan, the Practimo/Practis behavior.

**Hard caps and boundaries**
- At most 3 active paths, following AxeLog.
- At most about 5 items per session.
- The LLM explains its choices ("why today") so the human can override them.
- Keep deterministic scoring in a script and let the LLM handle sequencing, exercise variation, coaching cues and reflection. This avoids silent drift in priorities.

### Gaps
- No product publishes its rotation or neglect algorithm, so the weighting formula above is a design proposal, not observed practice.
- I found no research-backed evidence specific to guitar on interleaved versus blocked practice scheduling in this pass. Motor-learning literature on interleaving exists but was not searched here.
