# ADR 0001: Monolit Django zamiast mikroserwisów

## Status
Zaakceptowane.

## Kontekst
System Helpdesk dla Urzędu Gminy. Zespół: 1 osoba. Skala: ~50-200 użytkowników, 
~50 zgłoszeń miesięcznie.

## Decyzja
Budujemy monolit Django z podziałem na aplikacje (`accounts`, `tickets`, `reports`).
Bez REST API na start. HTMX do interakcji.

## Uzasadnienie
- Jedna osoba utrzymuje system — mikroserwisy to nadmiar.
- Deployment to jeden `docker compose up`.
- Łatwe backupy (jedna baza).
- Możliwość wydzielenia modułu później, gdyby był sens.

## Konsekwencje
- Skalowanie pionowe (większy serwer), nie poziome.
- Aktualizacje wymagają restartu całej aplikacji.
- Trudniej mieszać technologie.