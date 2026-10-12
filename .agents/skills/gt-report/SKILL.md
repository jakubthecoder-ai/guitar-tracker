---
name: gt-report
description: Interaktywny raport HTML guitar-trackera – cele, ścieżki, trendy tempa z projekcją do deadline'u, plan dnia z odhaczaniem, formularz logu, utwory, regularność, historia profilu z potwierdzaniem zmian, komentarz mentora. Używaj, gdy użytkownik pyta „jak mi idzie”, chce raport, podsumowanie tygodnia lub odhaczać ćwiczenia w przeglądarce.
metadata:
  project: guitar-tracker
---

# gt-report

Wymaga `gt-core`.

## Generowanie
1. (Opcjonalnie) komentarz mentora: `report-builder` albo samodzielnie 4–8 zdań na bazie `gt state` →
   `gt --actor report-builder note --scope weekly '<tekst>'`.
2. `gt report` → `$GT_HOME/reports/latest.html` (plik samowystarczalny; `--open` otwiera przeglądarkę).

## Tryby zapisu z raportu
- **Na żywo (zalecane):** `gt serve --open` – lokalny serwer 127.0.0.1 z tokenem; kliknięcia (odhaczenie,
  log, status utworu, kamień milowy, potwierdzenie zmiany profilu, zgłoszenie bólu) zapisują się od razu.
  Serwer działa w tle – uruchamiaj go w tle w harnessie albo poproś użytkownika o osobny terminal.
- **Offline:** otwarty plik `latest.html` kolejkuje zmiany w przeglądarce → „Eksportuj zmiany” → plik
  `gt-events-*.json` w Pobranych → `gt ingest` (orkiestrator robi to na starcie rozmowy).

## Co pokazuje raport
Alerty (ból, objętość, zaniedbania, ryzyko terminu, zmiany do potwierdzenia) · plan dnia (zatwierdzony lub
podgląd) · formularz logu · karty ścieżek z wykresem tempa (czyste na zimno, czyste powtórzenia, burst, cel,
projekcja do celu), kamienie milowe, ćwiczenia ze stadiami · radar profilu L1–L5 · kalendarz 12 tygodni ·
dni od ostatniego ćwiczenia per ścieżka · utwory ze statusem · historia profilu · notatki mentora.
