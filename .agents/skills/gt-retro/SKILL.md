---
name: gt-retro
description: Retro i żywy profil w guitar-trackerze – sygnały postępu i braku postępu (gt signals), tygodniowe retro ścieżek przez path-coach, aktualizacja profilu przez profile-keeper z potwierdzaniem zmian poziomów i terminów. Używaj po sesji, przy powrocie po przerwie, raz w tygodniu lub gdy użytkownik pyta o postępy i plateau.
metadata:
  project: guitar-tracker
---

# gt-retro

Wymaga `gt-core`.

## Kiedy
- **Po każdej sesji**: `gt session end` zwraca `signals`. Jeśli są ostrzeżenia lub postęp → `profile-keeper`.
- **Start rozmowy po przerwie** (`days_since_practice ≥ 4` w `gt state`): `gt signals` → `profile-keeper`
  → zaproponuj „sesję powrotną” (krótsza, tempo od czystego).
- **Raz w tygodniu** (lub na prośbę): pełne retro poniżej.

## Pełne retro tygodniowe
1. `gt signals` i `gt state`.
2. Równolegle `path-coach` z `task: "retro"` dla każdej aktywnej ścieżki (zapisują `gt path retro`).
3. `profile-keeper` z sygnałami i podsumowaniami coachów → `gt profile change`.
4. Oczekujące zmiany (`pending_changes`: poziomy, terminy, priorytety) przedstaw użytkownikowi do decyzji:
   `gt profile confirm <id>` / `gt profile reject <id>` (albo przyciski w raporcie HTML).
5. `report-builder` → komentarz tygodnia + `gt report`.

## Reakcje (zasady)
| Sygnał | Reakcja |
|---|---|
| `progress` | pochwała z liczbą; `stage_ready` → zaproponuj `gt exercise stage` |
| `plateau` | zmiana bodźca, nie obniżanie poziomu: inne ćwiczenie, bursty, diagnoza mechaniki (nagranie), sekcja utworu |
| `neglect` | ścieżka wchodzi do planu automatycznie; przy uporczywym zaniedbaniu zapytaj o pauzę (`gt path pause`) |
| `skipped_sessions` / `inactivity` | mniejsza sesja o tej samej porze (intencja „jeśli-to”), bez kar i bez nadrabiania objętości |
| `deadline_risk` | uczciwa rozmowa: przesunięcie terminu z uzasadnieniem z trendu albo cel pośredni |
| `health_risk` | tryb lekki, `safety.md`, czerwone flagi → konsultacja |
| `timing_trend` | z analizy nagrań – poprawa = postęp, pogorszenie = wolniej i więcej klika |
