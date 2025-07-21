#!/bin/bash

# Скрипт для миграции данных в PostgreSQL через Docker
# Использование: ./docker-migration.sh

set -e

echo "🚀 Миграция Gospel Bot в PostgreSQL через Docker"
echo "=================================================="

# Проверяем, что PostgreSQL запущен
echo "📡 Проверяем PostgreSQL..."
if ! docker ps | grep -q gospel-bot-postgres; then
    echo "❌ PostgreSQL контейнер не запущен!"
    echo "Запустите сначала: docker-compose -f docker-compose.postgres.yml up -d postgres"
    exit 1
fi

echo "✅ PostgreSQL контейнер найден"

# Получаем IP адрес PostgreSQL контейнера
POSTGRES_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' gospel-bot-postgres)
echo "🔗 PostgreSQL IP: $POSTGRES_IP"

# Запускаем миграцию в временном Python контейнере
echo "🔄 Запускаем миграцию..."
docker run --rm \
    --network gospel_new_default \
    -v "$(pwd)":/workspace \
    -w /workspace \
    -e POSTGRES_HOST=postgres \
    -e POSTGRES_PORT=5432 \
    -e POSTGRES_DB=gospel_bot \
    -e POSTGRES_USER=postgres \
    -e POSTGRES_PASSWORD=gospel123 \
    python:3.11-slim bash -c "
        pip install asyncpg pandas &&
        python migrate_to_postgres.py --postgres-host postgres --yes
    "

echo "🎉 Миграция завершена!"
echo "Проверьте результат: docker exec -it gospel-bot-postgres psql -U postgres -d gospel_bot" 