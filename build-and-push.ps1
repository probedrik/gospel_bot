# PowerShell скрипт для сборки и публикации Docker образа на Docker Hub
# Использование: .\build-and-push.ps1 -Username "your_username" [-Tag "latest"]

param(
    [Parameter(Mandatory=$true)]
    [string]$Username,
    
    [Parameter(Mandatory=$false)]
    [string]$Tag = "latest"
)

# Функция для цветного вывода
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# Имя образа
$ImageName = "gospel-bot"
$FullImageName = "$Username/$ImageName"

Write-ColorOutput "🚀 Начинаем сборку и публикацию Docker образа" "Blue"
Write-ColorOutput "📦 Образ: ${FullImageName}:${Tag}" "Yellow"

# Проверка наличия Docker
try {
    docker --version | Out-Null
    Write-ColorOutput "✅ Docker найден" "Green"
} catch {
    Write-ColorOutput "❌ Docker не установлен или недоступен" "Red"
    exit 1
}

# Проверка авторизации в Docker Hub
Write-ColorOutput "🔐 Проверка авторизации в Docker Hub..." "Blue"
$dockerInfo = docker info 2>$null
if (-not ($dockerInfo -match "Username")) {
    Write-ColorOutput "⚠️  Необходима авторизация в Docker Hub" "Yellow"
    Write-ColorOutput "Выполняем docker login..." "Blue"
    docker login
    if ($LASTEXITCODE -ne 0) {
        Write-ColorOutput "❌ Ошибка авторизации" "Red"
        exit 1
    }
}

# Сборка образа
Write-ColorOutput "🔨 Сборка Docker образа..." "Blue"
docker build -t "${FullImageName}:${Tag}" .
if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput "❌ Ошибка сборки образа" "Red"
    exit 1
}

# Также создаем тег latest если это не latest
if ($Tag -ne "latest") {
    Write-ColorOutput "🏷️  Создание тега latest..." "Blue"
    docker tag "${FullImageName}:${Tag}" "${FullImageName}:latest"
}

# Показываем информацию об образе
Write-ColorOutput "📊 Информация об образе:" "Blue"
docker images $FullImageName

# Тестирование образа
Write-ColorOutput "🧪 Тестирование образа..." "Blue"
$testResult = docker run --rm "${FullImageName}:${Tag}" python -c "import sys; print('Python version:', sys.version); import aiogram; print('Aiogram imported successfully')"
if ($LASTEXITCODE -eq 0) {
    Write-ColorOutput "✅ Образ прошел базовые тесты" "Green"
} else {
    Write-ColorOutput "❌ Образ не прошел тесты" "Red"
    exit 1
}

# Публикация на Docker Hub
Write-ColorOutput "📤 Публикация образа на Docker Hub..." "Blue"
docker push "${FullImageName}:${Tag}"
if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput "❌ Ошибка публикации образа" "Red"
    exit 1
}

if ($Tag -ne "latest") {
    Write-ColorOutput "📤 Публикация тега latest..." "Blue"
    docker push "${FullImageName}:latest"
}

Write-ColorOutput "🎉 Успешно! Образ опубликован на Docker Hub" "Green"
Write-ColorOutput "📋 Для использования выполните:" "Blue"
Write-Host "   docker pull ${FullImageName}:${Tag}"
Write-Host "   docker run -d --name gospel-bot --env-file .env ${FullImageName}:${Tag}"

Write-ColorOutput "🔗 Ссылка на Docker Hub: https://hub.docker.com/r/$Username/$ImageName" "Yellow" 