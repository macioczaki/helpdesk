#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

echo "==> git pull..."
git pull --ff-only

echo "==> build..."
docker compose -f docker-compose.prod.yml build

echo "==> migrate..."
docker compose -f docker-compose.prod.yml run --rm web python manage.py migrate --noinput

echo "==> up -d..."
docker compose -f docker-compose.prod.yml up -d

echo "==> czyszczenie..."
docker image prune -f

echo "==> status..."
docker compose -f docker-compose.prod.yml ps