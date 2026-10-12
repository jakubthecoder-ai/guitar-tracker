# Song-recommendation data sources & methods for a guitar practice coach (rock / metal / blues / prog), as of Oct 2026

## Songsterr: API endpoints, difficulty/tuning fields, status in 2026, ToS, MCP servers

### Takeaway
Songsterr's **legacy documented API (`/a/ra/songs.json?pattern=`) and its docs page (`/a/wa/api/`) both return HTTP 404 as of 2026-10-12**, so treat them as dead. The **unofficial `/api/songs?pattern=` endpoint works** and returns per-track `difficulty` (integer, roughly 1-8) and `tuning` (MIDI note numbers) — the best free difficulty signal found, but it is undocumented, can change without notice, and commercial use/reuse needs written permission.

### Cited Findings
- Live test 2026-10-12: `GET https://www.songsterr.com/api/songs?pattern=master%20of%20puppets&size=2` returned JSON. Song-level fields: `songId, artistId, artist, title, hasChords, hasPlayer, defaultTrack, popularTrack, isJunk, popularTrackGuitar, popularTrackBass, popularTrackDrum, popularTrackVocals`. Each entry in `tracks[]` has `instrumentId, instrument, views, name, difficulty, tuning, hash`. Example: Metallica "Master of Puppets" (songId 455118). The rhythm guitar track (James Hetfield, 627,682 views) has difficulty 4. Kirk Hammett's lead track has difficulty 4, the "Delay" guitar track 7, the clean guitar track 2, and the bass track 6. Tuning `[64,59,55,50,45,40]` is E standard, listed high to low. Vocal tracks have no difficulty. — [Songsterr /api/songs (live fetch)](https://www.songsterr.com/api/songs?pattern=master%20of%20puppets&size=2)
- Live test 2026-10-12: `https://www.songsterr.com/a/ra/songs.json?pattern=...` returned **HTTP 404**, and the docs page `https://www.songsterr.com/a/wa/api/` also returned **404**. — [songs.json (404)](https://www.songsterr.com/a/ra/songs.json?pattern=master%20of%20puppets); [api docs (404)](https://www.songsterr.com/a/wa/api/)
- Directory listings disagree. APIBouncer marks the Songsterr API as **dead** (last verified Apr 1, 2026). public-api.org found no real API endpoint. publicapis.io still shows the old `songs.json?pattern=` example. — [API Bouncer](https://www.apibouncer.com/apis/1307/songsterr); [public-api.org](https://public-api.org/api/916/songsterr); [publicapis.io](https://publicapis.io/songsterr-music-api)
- Songsterr rates tablatures automatically on a **1-8 scale** and does not say how the rating is computed. — [D'Hooge PhD thesis, Univ. Lille 2025, ch. 5](https://pepite-depot.univ-lille.fr/LIBRE/EDMADIS/2025/2025ULILB017.pdf)
- Other endpoints in use by community tools: `/api/meta/{id}/revisions`, plus a revision `source` URL that points to the underlying Guitar Pro file. These are **unofficial and "can change without notice."** The MCP project claims Songsterr "permits non-commercial API use; commercial use requires their approval." I found no primary Songsterr source for that claim. — [jaegerpicker/SongsterrMCP (Glama)](https://glama.ai/mcp/servers/jaegerpicker/SongsterrMCP)
- Existing MCP servers:
  - **jaegerpicker/SongsterrMCP**: GPL-3.0. Tools include `songsterr_get_tab` (per-track index, name, strings, tuning), `songsterr_list_tunings`, and `songsterr_transpose` (outputs ASCII or .gp5). Status is "pending live API verification" and maintenance is "Inactive"; Glama first observed v0.1.0 on Jul 15, 2026. — [Glama](https://glama.ai/mcp/servers/jaegerpicker/SongsterrMCP)
  - **gumluke/songsterr-mcp**: search, artist lookup and tab-fetch tools. It needs no key and returns **metadata only, not notation**; each result links to the Songsterr page. — [Glama](https://glama.ai/mcp/servers/skpfepl5w8)
- An Apify actor, "songsterr tab catalog metadata scraper," exists. It is third-party scraping. — [apify radar listing](https://godberrystudios.com/apify-radar/actor/jungle_synthesizer/songsterr-tab-catalog-metadata-scraper)
- **Songsterr ToS:** "You may not distribute, modify, transmit, reuse, download, repost, copy, or use said Content ... for commercial purposes or for personal gain, without express advance written permission." Content is the property of Guitartabs LLC. The ToS forbids using "any automated tool, script, browser extension, or AI agent" to bypass Plus features or to "modify, automate, or interfere with the Service or its tab player." Downloading Guitar Pro, MIDI, MP3 and WAV files is a **Plus (paid) feature**. — [Songsterr Terms](https://www.songsterr.com/a/wa/terms)
- Songsterr publishes **ai.txt**, a policy for AI agents. It allows agents to open and view a tab (title, artist, **tuning, notes**), explain how to play it, and build "independent tools that don't modify, automate, or interfere with the site." It prohibits emulating Plus features such as loop or slow-down, faking entitlements, or rewriting API responses. — [songsterr.com/ai.txt](https://www.songsterr.com/ai.txt)

### Inferences
- Using `/api/songs` for **metadata and difficulty lookup** on behalf of one user (personal, non-commercial, low rate, cached, identifying User-Agent) looks consistent with ai.txt's "viewing on a user's behalf / independent tools." **Bulk-harvesting** difficulty into a redistributed catalog, or downloading GP files through the revision `source` URL (a Plus feature), is high risk. Fetching GP files that way could be read as circumventing Plus.
- Songsterr difficulty is **per track**, not per song. Pick `popularTrackGuitar` or the track whose name contains "Rhythm" or "Lead" depending on the goal. The same song can be easy as rhythm and hard as lead.
- `isJunk` and `views` help filter out low-quality or user-cover entries such as "Misc Covers."
- Build behind an adapter with graceful failure, because the legacy endpoint already died.

### Gaps
- Exact semantics of the Songsterr difficulty scale (1-8 per the thesis, but the bounds observed live are unconfirmed), and whether it is derived from note density or tempo.
- I did not test `/api/meta/{id}/revisions` live.
- I found no primary Songsterr statement on API terms. The "non-commercial OK" claim comes only from a third-party MCP page.

## Ultimate Guitar: difficulty ratings, access methods, ToS

### Takeaway
Ultimate Guitar shows a **4-category difficulty** label, but there is **no public API**. Access is only through scraping or its private mobile API. The ToS restricts content to personal, non-commercial use and says that any unauthorized copy "shall constitute an act of copyright infringement," so legal risk is **high** for any automated use.

### Cited Findings
- UG "classifies songs in four difficulty categories" and does not disclose how the ratings are obtained. — [D'Hooge thesis 2025](https://pepite-depot.univ-lille.fr/LIBRE/EDMADIS/2025/2025ULILB017.pdf)
- A community Node scraper's output schema includes a `difficulty` field, for example "intermediate," which can be null. Another (Go) scraper targets UG's **mobile API**. One project warns that you get IP-blocked "every 2-8 hours" depending on aggressiveness. — [ultimate-guitar npm README](https://cdn.jsdelivr.net/npm/ultimate-guitar@2.0.6/README.md); [Pilfer (GitHub)](https://www.github.com/Pilfer); [tab-yoinker README](https://git.beefslab.com/michael/tab-yoinker/raw/branch/master/README.md)
- **UG ToS:** §6.3 says content "may be accessed for your personal, non-commercial use only." §6.4 says "any copy or use of any portion of the Service [not authorized] shall constitute an act of copyright infringement." §5.3 bars "accessing data not intended for you." §14(b) allows linking but not replicating content. The ToS covers the site, apps and "APIs," but no public API terms exist. — [UG Terms of Service](https://www.ultimate-guitar.com/about/tos.htm)
- The D'Hooge thesis notes that UG's chord diagrams can differ from the true diagrams, a quality concern with user-submitted content. — [D'Hooge thesis 2025, list of figures](https://pepite-depot.univ-lille.fr/LIBRE/EDMADIS/2025/2025ULILB017.pdf)

### Inferences
- Use UG only as a **deep link** ("search UG for X") and never scrape it. Linking is explicitly permitted by §14(b).

### Gaps
- I could not confirm the exact names of the 4 UG levels from a primary source (likely "absolute beginner / beginner / intermediate / advanced" — unverified).

## Guitar Pro file parsing (PyGuitarPro, alphaTab, others) to compute difficulty metrics

### Takeaway
Parse GP files the user owns (exported from Guitar Pro or bought) to compute tempo, note density, technique ratios and tuning. PyGuitarPro covers **GP3-5 only**. alphaTab (JS/.NET) and ApolloTab (Python, unverified maturity) cover GPX/GP7/GP8.

### Cited Findings
- **PyGuitarPro** reads and writes GP3, GP4 and GP5; "Support for GPX (Guitar Pro 6) files is out of scope of the project." It began as a Python port of alphaTab. Its models include `NoteEffect`, `BendEffect`, `BeatEffect` and a harmonic effect, plus a tapping enum. — [PyGuitarPro API docs](https://pyguitarpro.readthedocs.io/en/latest/pyguitarpro/api.html); [PyPI](https://pypi.org/project/PyGuitarPro/0.9.2)
- **alphaTab** loads Guitar Pro 3-5, GP6, GP7, AlphaTex and MusicXML. It renders palm mute, bends, and tap/slap/pop effects. — [alphaTab effects showcase](https://alphatab.net/docs/showcase/effects); [alphaTab features](https://demo.alphatab.net/features.html)
- **guitarpro-parser** (npm) parses .gp, .gpx and .gp5 and exposes note flags: bend, slide, harmonic, vibrato, hammerOn, pullOff, palmMute, letRing, tapped, muted. — [guitarpro-parser README](https://cdn.jsdelivr.net/npm/guitarpro-parser@1.2.0/README.md)
- **ApolloTab** (Python) claims full GP3/4/5/GPX/GP7/GP8 support and 18 playing techniques. — [PyPI apollotab](https://pypi.org/project/apollotab/)
- The **DadaGP** tokenizer handles only gp3-5 and needs PyGuitarPro 0.6, because newer versions break it. — [DadaGP repo mirror](https://gitblind.noratr.app/dada-bots/dadaGP)
- Feature groups validated against human difficulty ratings in the TPD dataset (D'Hooge, ch. 5) are a ready feature spec:
  - **Speed:** max/avg/std horizontal velocity, average inter-onset interval (IOI), smallest duration.
  - **Stamina:** number of notes, song duration.
  - **Structure/Repetition:** Lempel-Ziv complexity and entropy rate of string-fret and pitch sets.
  - **Technicity:** ratio of expressive techniques, bends, slides, hammer-on/pull-off; chord difficulty.
  - **Rhythm:** syncopation, onset entropy, number of distinct durations, duration entropy.

  — [D'Hooge thesis 2025, Table 5.4](https://pepite-depot.univ-lille.fr/LIBRE/EDMADIS/2025/2025ULILB017.pdf)

### Inferences
- A practical metric set from a GP parse:
  - BPM, including tempo changes.
  - Notes per second at the fastest passage. Subdivision × BPM gives "picking speed demand"; for example, 16ths at 180 BPM is 12 notes per second.
  - Presence of sextuplets or triplets.
  - Fret range and position shifts.
  - Per-technique counts: PM, bend, slide, HO/PO, tapping, harmonics, vibrato, and sweeps (detected heuristically as consecutive one-note-per-string arpeggios in one pick direction).
  - Time-signature changes and odd meters, for prog.
  - Tuning and number of strings.
- Run this per section (markers in the GP file) to produce "section difficulty."

### Gaps
- I did not verify PyGuitarPro's exact palm-mute and slide attribute names. Its source shows `NoteEffect` fields, but I did not confirm them in the docs I fetched.
- I did not verify ApolloTab's maturity.

## Rocksmith+, Yousician, MusicBrainz, Spotify, GetSongBPM (metadata)

### Takeaway
None of the learning apps expose difficulty data. **Spotify audio-features (tempo/key) returns 403 for apps created after 27 Nov 2024.** Use **MusicBrainz** for IDs and canonical metadata and **GetSongBPM** for tempo and key, which is free but requires a mandatory backlink.

### Cited Findings
- **Rocksmith+:** I found no public API. Ubisoft's dev diary describes internal "skill profiles," with skills grouped by difficulty, as a design detail only. Dynamic difficulty data exists inside the game and custom DLC files; community tools such as the Rocksmith Custom Toolkit can generate DD. — [Ubisoft dev diary, skill profiles](https://www.ubisoft.com/en-us/game/rocksmith/plus/news-updates/3S8q6DNIp3JdcjedymA6xp/rocksmith-dev-diary-late-march-2022-skill-profiles); [CustomsForge forum](https://customsforge.com/topic/66794-how-to-change-difficulty-on-downloaded-cdlcs/)
- **Spotify:** `GET /v1/audio-features`, `/audio-analysis` and `/recommendations` return 403 for new apps (created after 2024-11-27). Grandfathered extended-quota apps keep access. A further Feb 2026 change removed about 15 more endpoints, per press reports. — [Spotify Community](https://community.spotify.com/t5/Spotify-for-Developers/Web-API-v1-audio-features-returns-403-for-all-requests-other/m-p/7101554/highlight/true); [Digital Music News](https://www.digitalmusicnews.com/?p=308667); [Headphonesty, Feb 2026](https://www.headphonesty.com/2026/02/spotify-crackdown-thousands-third-party-music-apps/)
- **GetSongBPM API:** Free, with a required backlink to getsongbpm.com; without it the account can be suspended, for any use type including private use. Base URL `https://api.getsong.co/`, API key passed as a parameter or `X-API-KEY`, limit 3000 requests per hour. — [GetSongBPM API](https://getsongbpm.com/api)
- **MusicBrainz:** About 1 request per second per IP. Every request needs a descriptive User-Agent such as `App/1.0 ( contact )`; anonymous or generic User-Agents are throttled. — [MusicBrainz rate limiting](https://musicbrainz.org/doc/MusicBrainz_API/Rate_Limiting)
- **Soundcharts** sells a commercial audio-features API (tempo, key, mode, time signature). — [Soundcharts](https://soundcharts.com/audio-features-api)

### Inferences
- Tempo from GetSongBPM or MusicBrainz is the song's *recording* tempo, not the riff's subdivision. Combine it with the technique tag ("16th-note downpicking at 180") to estimate difficulty.
- Yousician: I found no data source; it is closed.

### Gaps
- Yousician offers no public data or API; I found nothing citable either way.
- I did not obtain an official Spotify changelog page for the exact dates. The sources are community and press.

## Academic work on automatic guitar tab difficulty estimation

### Takeaway
The key reference is **Alexandre D'Hooge's PhD thesis (Univ. Lille, defended 9 Oct 2025)**. It covers both difficulty-adjusted song suggestion with a "challenge fit" formula, and explainable tablature difficulty features (TPD dataset, about 60% accuracy on 5 classes). Supporting work includes Vélez Vásquez et al. (ISMIR 2023, chord-ease rubric), Ramoneda et al. (ISMIR 2024, RubricNet, piano), and Ariga et al. (ISMIR 2017).

### Cited Findings
- **D'Hooge thesis, "Assisting Western Popular Music Guitar Practice and Tablature Composition with Machine Learning":** defended 9 Oct 2025, co-directed by Louis Bigo. — [SCRIME seminar page](https://scrime.u-bordeaux.fr/scrime/evenements/seminaire-tad-assisting-western-popular-music-guitar-practice-and-tablature-composition-machine-learning); [Thesis PDF](https://pepite-depot.univ-lille.fr/LIBRE/EDMADIS/2025/2025ULILB017.pdf)
  - **Ch. 4 (song suggestion):** Songs are split into **parts** (intro, verse, bridge) and into **versions** a-e, from whole-note chords up to the original rhythm, giving 989 rated versions. Ratings cover chords, rhythm and global difficulty. A learner's level per criterion is estimated from songs they have already practised. The "challenge fit" is F_g(v) = Σ α_k · C_k(g,v), with C_k = exp(β_k·|ℓ_k(v) − ℓ_k(g) − γ_k|) − 1. A positive γ_k deliberately targets **above-level ("stretch")** material. The system offers *several options of varying difficulty* to preserve learner agency. Example: the R.E.M. "Losing My Religion" bridge is harder than the verse because of the F barre and fast changes.
  - **Ch. 5 (TPD dataset):** Data comes from a 10-year online community competition with Beginner/Intermediate/Advanced/Master leagues, grades 1-10, and expert-rated weekly songs. It contains 1,293 lead guitar, 973 rhythm guitar and 1,297 bass GP files, from 370 transcribers and 765 artists. The source is anonymised for legal reasons, with a public release promised after publication.
  - The best features are Lempel-Ziv complexity of the string-fret set (Kendall τ ≈ 0.75 with ratings), entropy rates, presence of sextuplets or triplets, pitch and fret range, and the HO/PO ratio. A Gaussian Naive Bayes model on 6 features reaches **0.601 accuracy** on 5 classes (chance is 0.20). The thesis also uses RubricNet.
- **Vélez Vásquez et al., ISMIR 2023, "Quantifying the ease of playing song chords on the guitar":** a rubric from guitar teachers, a dataset, and a rule-based baseline from chord annotations and timings. — [UvA DARE](https://dare.uva.nl/id/6b0a80e9-7387-4cf8-8952-a28cef06a8ea)
- **Ramoneda, Eremenko, D'Hooge et al., ISMIR 2024:** explainable difficulty estimation for piano; 41.4% accuracy and MSE 1.7 across 9 classes. — [UPF repository](https://repositori.upf.edu/items/ce1b8e99-9d5a-4b83-97a7-0c7e15d22a0b/full)
- **Ariga et al., ISMIR 2017 (Song2Guitar):** difficulty-aware tab arrangement from audio, based on a survey of what makes tabs hard. — [ISMIR 2017 paper](https://archives.ismir.net/ismir2017/paper/000041.pdf)
- **De La Salle University bachelor thesis:** linear regression on hand-built tab features, with low R² (about 24-28%; sources differ). — [DLSU repository](https://animorepository.dlsu.edu.ph/etd_bachelors/10738)
- **DadaGP (ISMIR 2021):** 26,181 GP songs across 739 genres. Available for research **on request** from Dadabots or Pedro Sarmento. — [arXiv 2107.14653](https://arxiv.org/abs/2107.14653); [Zenodo](https://zenodo.org/records/5624597)

### Inferences
- Even the best explainable models reach only about 55-60% exact-class accuracy. Treat computed difficulty as a ±1-band estimate and let user feedback ("too hard / too easy") correct it.

### Gaps
- I did not confirm whether the TPD dataset has been publicly released as of Oct 2026.

## Curated "songs by technique and level" lists (rock/metal/blues/prog)

### Takeaway
Web lists exist for downpicking, blues phrasing and prog techniques, but they are sparse and seldom give BPM or levels. A hand-curated seed list (about 100-200 entries) verified against Songsterr metadata is the realistic path.

### Cited Findings
- **Downpicking:**
  - Metallica "Master of Puppets": match the rhythm part including accents; RoadieMusic tags the article "Level_Intermediate."
  - Metallica "Welcome Home (Sanitarium)."
  - Megadeth "Symphony of Destruction": timing and muting.
  - Slipknot "Duality": fast downpicking, "special challenge."

  — [RoadieMusic](https://www.roadiemusic.com/blog/best-songs-to-practice-downpicking/)
- One "Master of Puppets" riff is all downstrokes at about 220 BPM, used as a benchmark. Start at roughly 40-50% speed. "Creeping Death" and "Blackened" are given for all-downstroke practice, and "Battery" for gallops. — [GuitarGearFinder, Metallica lessons](https://guitargearfinder.com/lessons/learn-metallica-songs-on-guitar/)
- **Blues (beginner):** B.B. King "Lucille" (12/8 feel); Screamin' Jay Hawkins "I Put a Spell On You." — [Fender, 10 easy blues songs](https://fender.com/articles/songs/10-easy-blues-songs-to-learn-on-guitar)
- **Blues (phrasing, bends, vibrato):** B.B. King "The Thrill Is Gone" (emphasis on bends and vibrato); "Boom Boom"; "Texas Flood"; "Statesboro Blues." — [Killer Guitar Rigs, 40 blues songs](https://killerguitarrigs.com/famous-easy-blues-songs-on-guitar/)
- **Blues method repertoire:** Hal Leonard's Blues Guitar Method uses "Boom Boom," "Sweet Home Chicago" and "Killing Floor" and covers bends and vibrato. — [Hal Leonard method listing](https://www.musicjunction.com.au/products/hal-leonard-guitar-method-blues-guitar)
- **Prog (sweep and legato):**
  - Dream Theater "Overture 1928": sweep-picked arpeggios, legato, alternate picking.
  - Dream Theater "Erotomania": sweeps in the arpeggio sections, extensive legato.

  — [LickLibrary Overture 1928](https://www.licklibrary.com/learn/lessons/dream-theater/overture-1928); [LickLibrary Erotomania](https://www.licklibrary.com/learn/lessons/dream-theater/erotomania-1)
- **Prog (Petrucci-style material):** shifting time signatures, alternate-picked riffs, legato, sweeps, tapping. Songs cited: "In the Presence of Enemies Pt. 1," "This Dying Soul," "In the Name of God." — [Premier Guitar](https://www.premierguitar.com/lessons/obsessive-progressive-john-petrucci)
- **Odd-meter practice:** take a 4/4 riff and play it in 5/4; listen to Dream Theater and Opeth. — [Riffhard prog guide](https://www.riffhard.com/progressive-metal-guitar-lessons/)
- **Songsterr example:** "Master of Puppets" rhythm track has difficulty 4 and lead track 4. — [Songsterr /api/songs](https://www.songsterr.com/api/songs?pattern=master%20of%20puppets&size=2)

### Inferences
- The thin sourcing confirms that the coach needs its **own curated JSON seed list** with fields: artist, title, part/section, techniques[], level band, approx BPM, tuning, and source/verification. LLM-proposed additions should go into this list only after automated verification (see below).
- Candidate seed entries from general guitar knowledge, **not verified in this research; verify before use:**
  - **Alternate picking:** Megadeth "Tornado of Souls" solo; Metallica "Fade to Black" solo; Iron Maiden "The Trooper" gallop and harmonies.
  - **Legato:** Joe Satriani "Satch Boogie"; Dream Theater "Erotomania."
  - **Tapping:** Van Halen "Eruption"; Extreme "Get the Funk Out."
  - **Blues bends:** SRV "Pride and Joy"; Eric Clapton/Cream "Crossroads"; Gary Moore "Still Got the Blues."
  - **Odd time:** Tool "Schism"; Dream Theater "The Dance of Eternity"; Rush "YYZ"; Meshuggah "Bleed" (polymeter, extended range).
  - **Rock beginner:** Deep Purple "Smoke on the Water"; AC/DC "Back in Black" riff; Black Sabbath "Paranoid."

### Gaps
- I found no Reddit thread with a structured technique-by-level list; search returned only blogs.
- No source gives verified BPM per riff, except about 220 BPM for "Master of Puppets."

## Recommendation design: technique tags, difficulty bands, stretch songs, section splitting, hallucination control

### Takeaway
Recommend **song sections, not whole songs**. Tag them by technique, place them in difficulty bands, and score candidates with a challenge-fit function biased slightly above the learner's level (D'Hooge). Verify every LLM-generated suggestion against a curated list or a live metadata lookup (Songsterr `/api/songs`, MusicBrainz) before showing it.

### Cited Findings
- Splitting into parts and versions, using a per-criterion learner level estimated from practised songs, a positive γ for stretch, and offering several options of varying difficulty all come from the D'Hooge thesis, ch. 4. — [D'Hooge thesis 2025](https://pepite-depot.univ-lille.fr/LIBRE/EDMADIS/2025/2025ULILB017.pdf)
- Difficulty differs by part and league: the same song is rated differently for rhythm vs lead, and different features matter (chord difficulty for rhythm, speed and LZ for lead). — [D'Hooge thesis 2025, Table 5.3](https://pepite-depot.univ-lille.fr/LIBRE/EDMADIS/2025/2025ULILB017.pdf); per-track Songsterr difficulty confirms this in practice — [Songsterr /api/songs](https://www.songsterr.com/api/songs?pattern=master%20of%20puppets&size=2)
- Slow-tempo practice (40-50% speed, then build up) is standard advice. — [GuitarGearFinder](https://guitargearfinder.com/lessons/learn-metallica-songs-on-guitar/)

### Inferences (proposed design)
1. **Data model:** `SongPart {artist, title, part (intro/verse/riff/solo), role (rhythm/lead), techniques[], level 1-10, bpm, subdivision, tuning, time_signatures[], source, verified_at}`.
   - Technique taxonomy: downpicking, alternate picking, gallop, palm muting, power chords, barre chords, string bends, vibrato, legato (HO/PO), tapping, sweep picking, economy picking, hybrid picking, pinch harmonics, odd meter/polymeter, drop/extended tuning, blues phrasing (12-bar, shuffle).
2. **Level bands:** Map Songsterr 1-8 and TPD grades 1-10 (Beginner 1-3, Intermediate 4-5, Advanced 6-7, Master 8-9, Expert 10) to one internal 1-10 scale.
3. **Learner model:**
   - Keep a per-technique skill level plus clean BPM per technique, taken from practice logs.
   - Update it with user feedback after each attempt (nailed / struggling / too hard).
4. **Scoring:**
   - Use D'Hooge-style challenge fit per technique, targeting **+0.5 to +1.5 levels** on 1-2 target techniques and **at or below level** on everything else.
   - Return 3 options: comfortable, target, stretch.
   - Also give a starting BPM: the user's clean BPM for that technique, or 50-70% of the recording tempo.
5. **Offline mode:** use the curated JSON seed list plus LLM knowledge, with each LLM suggestion flagged "unverified" until checked.
6. **Hallucination control:**
   - (a) Prefer the curated list.
   - (b) For LLM-proposed songs, check existence via Songsterr `/api/songs?pattern=` (artist and title match, `isJunk=false`, guitar track present). Read the per-track `difficulty` and `tuning` as a sanity check on the claimed level and tuning. Or check via MusicBrainz recording search, at 1 request per second with a User-Agent.
   - (c) Never state BPMs or time signatures as fact unless they come from a source (GetSongBPM or a GP file parse). Otherwise label them "approx."
   - (d) Store `verified_at` and the source per entry.
7. **Legal posture:**
   - Link out to tabs on Songsterr or UG rather than reproducing them.
   - Analyse only GP files the user supplies.
   - Make metadata calls on the user's behalf at low rate, with caching and no redistribution.
   - Request written permission before any commercial use.

### Gaps
- No empirical study was found on how far above level a "stretch" should be for guitar. The γ values in D'Hooge are tunable parameters, not validated constants.
