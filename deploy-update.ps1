# PowerShell скрипт для автоматического обновления Gospel Bot
# Обновляет Git репозиторий и Docker Hub одной командой
# Использование: .\deploy-update.ps1 [версия] [сообщение_коммита]

param(
    [string]$Version = "",
    [string]$CommitMessage = "",
    [switch]$Help
)

# Настройки
$DOCKER_USERNAME = "probedrik"
$IMAGE_NAME = "gospel-bot"
$GITHUB_REPO = "gospel_bot"

# Функция для вывода цветного текста
function Write-ColorOutput($Message, $ForegroundColor = "White") {
    Write-Host $Message -ForegroundColor $ForegroundColor
}

# Функция для отображения заголовка
function Write-Header($Title) {
    Write-Host ""
    Write-ColorOutput "================================================================" -ForegroundColor Magenta
    Write-ColorOutput "  $Title" -ForegroundColor Magenta
    Write-ColorOutput "================================================================" -ForegroundColor Magenta
    Write-Host ""
}

# Функция для получения текущей версии
function Get-CurrentVersion {
    try {
        $lastTag = git describe --tags --abbrev=0 2>$null
        if (-not $lastTag) {
            return "v2.6.1"
        }
        return $lastTag
    }
    catch {
        return "v2.6.1"
    }
}

# Функция для генерации новой версии
function Get-NextVersion {
    $currentVersion = Get-CurrentVersion
    # Убираем 'v' и разбиваем на части
    $versionNum = $currentVersion -replace '^v', ''
    $parts = $versionNum -split '\.'
    $major = [int]$parts[0]
    $minor = [int]$parts[1]
    $patch = [int]$parts[2]
    
    # Увеличиваем patch версию
    $patch++
    return "v$major.$minor.$patch"
}

# Показать справку
if ($Help) {
    Write-Header "🚀 GOSPEL BOT - АВТОМАТИЧЕСКОЕ ОБНОВЛЕНИЕ"
    Write-Host "Использование:"
    Write-Host "  .\deploy-update.ps1 [версия] [сообщение]"
    Write-Host ""
    Write-Host "Параметры:"
    Write-Host "  версия        Версия для создания тега (например: v2.7.0)"
    Write-Host "  сообщение     Сообщение коммита"
    Write-Host "  -Help         Показать эту справку"
    Write-Host ""
    Write-Host "Примеры:"
    Write-Host "  .\deploy-update.ps1 v2.7.0 'Add PostgreSQL support'"
    Write-Host "  .\deploy-update.ps1  # Автоматическая версия"
    exit 0
}

Write-Header "🚀 GOSPEL BOT - АВТОМАТИЧЕСКОЕ ОБНОВЛЕНИЕ"

# Если версия не указана, генерируем автоматически
if (-not $Version) {
    $currentVersion = Get-CurrentVersion
    $Version = Get-NextVersion
    Write-ColorOutput "🏷️  Текущая версия: $currentVersion" -ForegroundColor Yellow
    Write-ColorOutput "🏷️  Новая версия: $Version" -ForegroundColor Cyan
    Write-Host ""
    $userVersion = Read-Host "Подтвердите новую версию (Enter для продолжения или введите свою)"
    if ($userVersion) {
        $Version = $userVersion
    }
}

# Если сообщение коммита не указано, запрашиваем
if (-not $CommitMessage) {
    Write-Host ""
    Write-ColorOutput "💬 Введите сообщение коммита:" -ForegroundColor Cyan
    $CommitMessage = Read-Host ">"
    if (-not $CommitMessage) {
        $CommitMessage = "Update to $Version"
    }
}

Write-Header "📋 ПАРАМЕТРЫ ОБНОВЛЕНИЯ"
Write-ColorOutput "🏷️  Версия: $Version" -ForegroundColor Blue
Write-ColorOutput "💬 Коммит: $CommitMessage" -ForegroundColor Blue
Write-ColorOutput "🐳 Docker: $DOCKER_USERNAME/$IMAGE_NAME`:$Version" -ForegroundColor Blue
Write-Host ""

# Подтверждение
$confirm = Read-Host "Продолжить? (y/N)"
if ($confirm -notmatch "^[Yy]$") {
    Write-ColorOutput "❌ Отменено пользователем" -ForegroundColor Red
    exit 1
}

Write-Header "🔍 ПРОВЕРКА ОКРУЖЕНИЯ"

# Проверяем Git
try {
    $gitVersion = git --version
    Write-ColorOutput "✅ Git: $gitVersion" -ForegroundColor Green
}
catch {
    Write-ColorOutput "❌ Git не найден!" -ForegroundColor Red
    exit 1
}

# Проверяем Docker
try {
    $dockerVersion = docker --version
    Write-ColorOutput "✅ Docker: $dockerVersion" -ForegroundColor Green
}
catch {
    Write-ColorOutput "❌ Docker не найден!" -ForegroundColor Red
    exit 1
}

Write-Header "📝 ОБНОВЛЕНИЕ GIT РЕПОЗИТОРИЯ"

try {
    # Добавляем все изменения
    Write-ColorOutput "📤 Добавление изменений..." -ForegroundColor Yellow
    git add .
    
    # Создаем коммит
    Write-ColorOutput "💾 Создание коммита..." -ForegroundColor Yellow
    git commit -m $CommitMessage
    
    # Создаем тег
    Write-ColorOutput "🏷️  Создание тега $Version..." -ForegroundColor Yellow
    git tag $Version
    
    # Пушим изменения
    Write-ColorOutput "🚀 Отправка в GitHub..." -ForegroundColor Yellow
    git push origin master
    git push origin $Version
    
    Write-ColorOutput "✅ Git репозиторий обновлен" -ForegroundColor Green
}
catch {
    Write-ColorOutput "❌ Ошибка обновления Git: $_" -ForegroundColor Red
    exit 1
}

Write-Header "🐳 СБОРКА DOCKER ОБРАЗА"

try {
    # Сборка образа
    Write-ColorOutput "🔨 Сборка Docker образа..." -ForegroundColor Yellow
    docker build -t "${DOCKER_USERNAME}/${IMAGE_NAME}:${Version}" .
    docker build -t "${DOCKER_USERNAME}/${IMAGE_NAME}:latest" .
    
    Write-ColorOutput "✅ Docker образ собран" -ForegroundColor Green
}
catch {
    Write-ColorOutput "❌ Ошибка сборки Docker образа: $_" -ForegroundColor Red
    exit 1
}

Write-Header "📤 ОТПРАВКА В DOCKER HUB"

try {
    # Отправка в Docker Hub
    Write-ColorOutput "🚀 Отправка в Docker Hub..." -ForegroundColor Yellow
    docker push "${DOCKER_USERNAME}/${IMAGE_NAME}:${Version}"
    docker push "${DOCKER_USERNAME}/${IMAGE_NAME}:latest"
    
    Write-ColorOutput "✅ Docker образ отправлен в Docker Hub" -ForegroundColor Green
}
catch {
    Write-ColorOutput "❌ Ошибка отправки в Docker Hub: $_" -ForegroundColor Red
    exit 1
}

Write-Header "🎉 ОБНОВЛЕНИЕ ЗАВЕРШЕНО"

Write-ColorOutput "✅ Версия: $Version" -ForegroundColor Green
Write-ColorOutput "✅ GitHub: https://github.com/probedrik/$GITHUB_REPO/releases/tag/$Version" -ForegroundColor Green
Write-ColorOutput "✅ Docker Hub: https://hub.docker.com/r/$DOCKER_USERNAME/$IMAGE_NAME/tags" -ForegroundColor Green
Write-Host ""
Write-ColorOutput "🚀 Для обновления на сервере выполните:" -ForegroundColor Cyan
Write-ColorOutput "   git pull origin master" -ForegroundColor White
Write-ColorOutput "   docker-compose -f docker-compose.postgres.yml pull" -ForegroundColor White
Write-ColorOutput "   docker-compose -f docker-compose.postgres.yml up -d" -ForegroundColor White

Write-Host ""
Write-ColorOutput "🎯 Готово!" -ForegroundColor Green 