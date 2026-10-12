---
name: gt-analyze
description: Analiza nagrań ćwiczeń gitarowych w guitar-trackerze – timing względem metronomu (odchylenie w ms, przyspieszanie/zwalnianie, moment rozjazdu, nierówność down/up) albo względem tabulatury Guitar Pro (pominięte i dodatkowe nuty). Używaj, gdy użytkownik nagrał ćwiczenie lub riff i chce obiektywnej oceny.
metadata:
  project: guitar-tracker
---

# gt-analyze

Wymaga `gt-core` i `uv` (pierwsze uruchomienie instaluje numpy/librosa – może potrwać minutę).

## Jak nagrywać (powiedz użytkownikowi)
- Najlepiej **czysty sygnał DI** (wyjście interfejsu/modelera przed przesterem albo czysty kanał); przester i
  pogłos rozmazują początki dźwięków.
- **Znane tempo klika** (to samo co w ćwiczeniu); klik w słuchawkach, nie w nagraniu.
- 20–90 s jednego ćwiczenia, bez gadania na początku. Format WAV/FLAC (MP3 też działa).

## Komendy
- Metronom: `gt analyze <plik> --exercise <id> --bpm 160 [--subdivision 8ths|16ths|triplets|quarters]`
  (podział domyślnie z ćwiczenia).
- Tabulatura: `gt analyze <plik> --exercise <id> --gp riff.gp5 [--track 0] [--bpm 160]` (GP3–5).
- Wynik zapisuje się jako zdarzenie `recording_analyzed`; raport HTML pokazuje tabelę nagrań w karcie ścieżki,
  a `gt signals` – `timing_trend` przy kolejnych nagraniach tego samego ćwiczenia.

## Interpretacja
Prowadzi `audio-analyst` (`agents/audio-analyst.md`). Progi orientacyjne: ±10 ms bardzo dobrze, 10–20 ms
dobrze, >25 ms słyszalne przy szybkich podziałach. Analiza ≠ test na zimno: czyste tempo nadal potwierdza
`gt session cold-check`.
