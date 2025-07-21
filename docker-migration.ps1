# Скрипт для миграции данных в PostgreSQL через Docker (Windows PowerShell)
# Использование: .\docker-migration.ps1

Write-Host "🚀 Миграция Gospel Bot в PostgreSQL через Docker" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green

# Проверяем, что PostgreSQL запущен
Write-Host "📡 Проверяем PostgreSQL..." -ForegroundColor Yellow
$postgresContainer = docker ps --filter "name=gospel-bot-postgres" --format "{{.Names}}"
if (-not $postgresContainer) {
    Write-Host "❌ PostgreSQL контейнер не запущен!" -ForegroundColor Red
    Write-Host "Запустите сначала: docker-compose -f docker-compose.postgres.yml up -d postgres" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ PostgreSQL контейнер найден: $postgresContainer" -ForegroundColor Green

# Получаем сеть Docker Compose
$network = "gospel_default"
Write-Host "🔗 Используем сеть: $network" -ForegroundColor Cyan

# Запускаем миграцию в временном Python контейнере
Write-Host "🔄 Запускаем миграцию..." -ForegroundColor Yellow

$currentPath = (Get-Location).Path
docker run --rm `
    --network $network `
    -v "${currentPath}:/workspace" `
    -w /workspace `
    -e POSTGRES_HOST=postgres `
    -e POSTGRES_PORT=5432 `
    -e POSTGRES_DB=gospel_bot `
    -e POSTGRES_USER=postgres `
    -e POSTGRES_PASSWORD=gospel123 `
    python:3.11-slim bash -c "
        pip install asyncpg pandas &&
        python migrate_to_postgres.py --postgres-host postgres --yes
    "

if ($LASTEXITCODE -eq 0) {
    Write-Host "🎉 Миграция завершена успешно!" -ForegroundColor Green
    Write-Host "Проверьте результат:" -ForegroundColor Yellow
    Write-Host "docker exec -it gospel-bot-postgres psql -U postgres -d gospel_bot" -ForegroundColor Cyan
} else {
    Write-Host "❌ Ошибка при миграции!" -ForegroundColor Red
    exit 1
} 