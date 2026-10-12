---
name: gt-songs
description: Dobór utworów do przegrania w guitar-trackerze – propozycje komfort / cel / stretch dopasowane do ścieżki i poziomu (lista startowa rock/metal/blues/prog), weryfikacja w Songsterr i MusicBrainz (strój, trudność partii, link do tabu), dodawanie i statusy utworów. Używaj, gdy użytkownik pyta „co zagrać”, chce utwór do ścieżki lub zmienia status utworu.
metadata:
  project: guitar-tracker
---

# gt-songs

Wymaga `gt-core`. Treść propozycji przygotowuje `song-scout`.

## Komendy
- `gt song suggest --path <id>` – z listy startowej (`references/songs_seed.json`, 44 utwory) na poziomie profilu
  w osi ścieżki: `comfort` (L-1), `target` (L), `stretch` (L+1). Filtry: `--axis`, `--technique downpicking`,
  `--level 3`.
- `gt song verify --artist "…" --title "…"` – czy utwór istnieje (Songsterr, MusicBrainz), strój głównej
  partii gitary, trudność partii gitarowych Songsterr (1–8), link do tabu, długość. Wyniki w cache 30 dni.
- `gt song add --from '[{"seed_id": "metallica-master-of-puppets", "path_id": "…", "status": "learning",
  "sections": ["main riff"]}]'` – z seeda; spoza seeda podaj `artist`, `title`, `role`, `techniques`, `why`.
- `gt song verify <song_id>` – zapisuje wynik weryfikacji przy utworze (link, strój, trudność, `verified_at`).
- `gt song status <song_id> backlog|learning|polishing|performance_ready|maintenance`.

## Zasady
- Każdy utwór spoza seeda **zweryfikuj przed zaproponowaniem**. Brak weryfikacji = nie proponuj jako pewnego.
- Tempo, strój i sekcje bez źródła oznaczaj „ok.”. Taby tylko linkuj (nie przepisuj).
- Proponuj fragmenty: riff/intro/solo jako sekcje, gdy całość jest za trudna.
- Utwory w statusie `learning`/`polishing` trafiają do bloku muzycznego w `gt plan`.
- Ograniczenia źródeł: nieoficjalne API Songsterr może się zmienić (tracker działa bez niego); Ultimate Guitar
  tylko jako link do wyszukiwarki.
