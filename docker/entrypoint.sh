#!/usr/bin/env bash
set -e

echo "==> Czekam na Postgresa..."
until python -c "
import os, psycopg
psycopg.connect(
    dbname=os.environ['POSTGRES_DB'],
    user=os.environ['POSTGRES_USER'],
    password=os.environ['POSTGRES_PASSWORD'],
    host=os.environ['POSTGRES_HOST'],
    port=os.environ['POSTGRES_PORT'],
)
" 2>/dev/null; do
  sleep 1
done
echo "==> Postgres gotowy."

echo "==> Migracje..."
python manage.py migrate --noinput

case "$1" in
  web)
    if [ "${DJANGO_DEBUG}" = "True" ]; then
      exec python manage.py runserver 0.0.0.0:8000
    else
      echo "==> collectstatic..."
      python manage.py collectstatic --noinput
      exec gunicorn config.wsgi:application \
        --bind 0.0.0.0:8000 \
        --workers "${GUNICORN_WORKERS:-3}" \
        --timeout 60 \
        --access-logfile - \
        --error-logfile -
    fi
    ;;
  worker)
    exec celery -A config worker -l info
    ;;
  beat)
    exec celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    ;;
  *)
    exec "$@"
    ;;
esac