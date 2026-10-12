# Reguły pedagogiczne (ustawienia domyślne – progi kalibruje `config.json`)

Siła dowodów: przeplatanie i rozkładanie w czasie – umiarkowana/silna w uczeniu motorycznym, słaba dla gitary
wprost; reguły BPM – praktyka nauczycieli, brak badań. Traktuj liczby jako punkt startu, nie prawo.

## Struktura sesji
1. Rozgrzewka 3–5 min bez maksymalnego tempa.
2. **Test na zimno** elementów z poprzedniej sesji – bez ich wcześniejszego rozgrywania. Wynik loguj
   `gt session cold-check`. Tylko test na zimno potwierdza „czyste tempo”.
3. Elementy w stadium `learn`: blok ciągły, wolno, fragmentami (chunking).
4. Elementy `stabilise/speed/apply` z różnych ścieżek: rotacje 3–5 min, cyklicznie 2–4 elementy.
5. Mikroprzerwa co ~20 min (30–60 s, rozluźnienie rąk).
6. Blok muzyczny w każdej sesji ≥30 min: utwór albo jam z podkładem.
7. Log: BPM, czyste powtórzenia, ocena 1–5, napięcie 1–5, notatka.

## Stadia elementu
`learn` → `stabilise` (czysto przy ≥65% tempa docelowego) → `speed` → `apply` (w muzyce/utworze) → `maintain`.
`gt` liczy `suggested_stage`; zmianę zatwierdza użytkownik (`gt exercise stage`).

## Tempo
- `speed`: drabinka +3–5% po 3–5 czystych powtórzeniach; przy napięciu lub błędach cofnij o 5–10%.
- Krótkie bursty (2–4 s) 10–20% powyżej tempa roboczego – loguj jako `--burst`.
- Nowe tempo liczy się dopiero po teście na zimno następnego dnia.
- Odróżniaj: tempo czyste (na zimno), kandydat (czyste powtórzenia w sesji), burst, szczyt.

## Powtórki
Elementy `maintain` wracają po 1, 3, 7, 14, 30 dniach (`next_review`, liczy `gt`).

## Cele i nawyk
- Cel ścieżki mierzalny, termin z kamieniami co 2–4 tygodnie.
- Przyrost tempa ≤ ~8% tygodniowo; większy – ostrzeżenie przy tworzeniu ścieżki.
- Intencja „jeśli-to” (kiedy i gdzie ćwiczę) w profilu – lepsze trzymanie się planu.
- Ocena po sesji jest zaniżona przy przeplataniu (uczucie gorszej gry) – postęp oceniaj testami na zimno i
  nagraniami, nie samą oceną 1–5.
- Opuszczone sesje → mniejsza sesja o tej samej porze, bez kar.
