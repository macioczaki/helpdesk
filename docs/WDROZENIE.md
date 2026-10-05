# Wdrożenie produkcyjne

## Wymagania
- Ubuntu Server 22.04 / 24.04 LTS
- 2 vCPU, 4 GB RAM, 40 GB SSD
- Docker + Docker Compose
- (opcjonalnie) domena wewnętrzna, np. helpdesk.gmina.local

## Kroki

1. Sklonuj repo na serwer do `/opt/helpdesk`:
   git clone git@github.com:macioczaki/helpdesk.git /opt/helpdesk
   cd /opt/helpdesk

2. Uruchom `deploy/install.sh`.

3. Skopiuj `.env.prod.example` do `.env` i uzupełnij:
   - DJANGO_SECRET_KEY (wygeneruj: `python3 -c "import secrets;print(secrets.token_urlsafe(64))"`)
   - POSTGRES_PASSWORD (mocne)
   - DJANGO_ALLOWED_HOSTS
   - EMAIL_* (SMTP urzędu)

4. Certyfikaty TLS do `certs/`:
   - `fullchain.pem`
   - `privkey.pem`
   Jeśli używasz domeny wewnętrznej, certyfikat z CA urzędu. Alternatywnie Let's Encrypt.

5. Start:
   docker compose -f docker-compose.prod.yml up -d --build

6. Superuser:
   docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

7. Dane startowe:
   docker compose -f docker-compose.prod.yml exec web python manage.py seed_sla

8. Backup — dodaj do crona:
   0 2 * * * cd /opt/helpdesk && ./deploy/backup.sh >> /var/log/helpdesk-backup.log 2>&1

## Aktualizacja
./deploy/update.sh

## Podgląd logów
docker compose -f docker-compose.prod.yml logs -f web