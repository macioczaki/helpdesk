# ADR 0002: HTMX zamiast SPA (React/Vue)

## Status
Zaakceptowane.

## Kontekst
Interfejs to głównie formularze, listy, tabele.

## Decyzja
Serwerowy rendering Django Templates + HTMX do dynamicznych fragmentów.

## Uzasadnienie
- Mniej kodu, szybsze wdrożenie.
- Jedna osoba utrzyma całość.
- Bootstrap 5 wystarczy do UI.
- HTMX pokrywa 90% potrzeb.

## Konsekwencje
- Brak offline.
- Mniej interaktywne niż SPA (akceptowalne).