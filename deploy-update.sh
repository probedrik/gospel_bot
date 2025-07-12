#!/bin/bash

# Скрипт для автоматического обновления Gospel Bot
# Обновляет Git репозиторий и Docker Hub одной командой
# Использование: ./deploy-update.sh [версия] [сообщение_коммита]

set -e  # Остановка при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Настройки
DOCKER_USERNAME="probedrik"
IMAGE_NAME="gospel-bot"
GITHUB_REPO="gospel_bot"

# Функция для вывода цветного текста
print_color() {
    printf "${1}${2}${NC}\n"
}

# Функция для отображения заголовка
print_header() {
    echo
    print_color $PURPLE "════════════════════════════════════════════════════════════════"
    print_color $PURPLE "  $1"
    print_color $PURPLE "════════════════════════════════════════════════════════════════"
    echo
}

# Функция для получения текущей версии
get_current_version() {
    # Получаем последний тег
    local last_tag=$(git describe --tags --abbrev=0 2>/dev/null || echo "v2.5.0")
    echo $last_tag
}

# Функция для генерации новой версии
generate_next_version() {
    local current_version=$(get_current_version)
    # Убираем 'v' и разбиваем на части
    local version_num=${current_version#v}
    local major=$(echo $version_num | cut -d. -f1)
    local minor=$(echo $version_num | cut -d. -f2)
    local patch=$(echo $version_num | cut -d. -f3)
    
    # Увеличиваем patch версию
    patch=$((patch + 1))
    echo "v$major.$minor.$patch"
}

# Проверка аргументов
VERSION=${1:-""}
COMMIT_MESSAGE=${2:-""}

print_header "🚀 GOSPEL BOT - АВТОМАТИЧЕСКОЕ ОБНОВЛЕНИЕ"

# Если версия не указана, генерируем автоматически
if [ -z "$VERSION" ]; then
    CURRENT_VERSION=$(get_current_version)
    VERSION=$(generate_next_version)
    print_color $YELLOW "🏷️  Текущая версия: $CURRENT_VERSION"
    print_color $CYAN "🏷️  Новая версия: $VERSION"
    echo
    read -p "Подтвердите новую версию (Enter для продолжения или введите свою): " user_version
    if [ ! -z "$user_version" ]; then
        VERSION=$user_version
    fi
fi

# Если сообщение коммита не указано, запрашиваем
if [ -z "$COMMIT_MESSAGE" ]; then
    echo
    print_color $CYAN "💬 Введите сообщение коммита:"
    read -p "> " COMMIT_MESSAGE
    if [ -z "$COMMIT_MESSAGE" ]; then
        COMMIT_MESSAGE="Update to $VERSION"
    fi
fi

print_header "📋 ПАРАМЕТРЫ ОБНОВЛЕНИЯ"
print_color $BLUE "🏷️  Версия: $VERSION"
print_color $BLUE "💬 Коммит: $COMMIT_MESSAGE"
print_color $BLUE "🐳 Docker: $DOCKER_USERNAME/$IMAGE_NAME:$VERSION"
echo

# Подтверждение
read -p "Продолжить? (y/N): " confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    print_color $RED "❌ Отменено пользователем"
    exit 1
fi

print_header "🔍 ПРОВЕРКА ОКРУЖЕНИЯ"

# Проверка Git
if ! command -v git &> /dev/null; then
    print_color $RED "❌ Git не установлен"
    exit 1
fi
print_color $GREEN "✅ Git найден"

# Проверка Docker
if ! command -v docker &> /dev/null; then
    print_color $RED "❌ Docker не установлен"
    exit 1
fi
print_color $GREEN "✅ Docker найден"

# Проверка авторизации в Docker Hub
print_color $BLUE "🔐 Проверка авторизации в Docker Hub..."
if ! docker info | grep -q "Username"; then
    print_color $YELLOW "⚠️  Необходима авторизация в Docker Hub"
    docker login
fi
print_color $GREEN "✅ Docker Hub авторизация OK"

print_header "📝 ОБНОВЛЕНИЕ GIT РЕПОЗИТОРИЯ"

# Проверка статуса Git
if ! git status &> /dev/null; then
    print_color $RED "❌ Не Git репозиторий"
    exit 1
fi

# Показываем статус
print_color $BLUE "📊 Статус репозитория:"
git status --short

# Добавляем все изменения
print_color $BLUE "📝 Добавляем изменения..."
git add .

# Проверяем, есть ли изменения для коммита
if git diff --cached --quiet; then
    print_color $YELLOW "⚠️  Нет изменений для коммита"
    read -p "Продолжить только с тегом? (y/N): " continue_tag
    if [[ ! $continue_tag =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    # Создаем коммит
    print_color $BLUE "💾 Создаем коммит..."
    git commit -m "$COMMIT_MESSAGE"
    print_color $GREEN "✅ Коммит создан"
fi

# Создаем тег
print_color $BLUE "🏷️  Создаем тег $VERSION..."
if git tag -l | grep -q "^$VERSION$"; then
    print_color $YELLOW "⚠️  Тег $VERSION уже существует"
    read -p "Удалить существующий тег? (y/N): " delete_tag
    if [[ $delete_tag =~ ^[Yy]$ ]]; then
        git tag -d $VERSION
        git push origin :refs/tags/$VERSION 2>/dev/null || true
    else
        exit 1
    fi
fi

git tag -a $VERSION -m "Release $VERSION: $COMMIT_MESSAGE"
print_color $GREEN "✅ Тег $VERSION создан"

# Отправляем на GitHub
print_color $BLUE "📤 Отправляем в GitHub..."
git push origin master
git push origin $VERSION
print_color $GREEN "✅ Изменения отправлены в GitHub"

print_header "🐳 СБОРКА И ПУБЛИКАЦИЯ DOCKER ОБРАЗА"

# Сборка образа
print_color $BLUE "🔨 Сборка Docker образа..."
docker build -t $DOCKER_USERNAME/$IMAGE_NAME:$VERSION .

# Создаем тег latest
print_color $BLUE "🏷️  Создание тега latest..."
docker tag $DOCKER_USERNAME/$IMAGE_NAME:$VERSION $DOCKER_USERNAME/$IMAGE_NAME:latest

# Показываем информацию об образе
print_color $BLUE "📊 Информация об образе:"
docker images $DOCKER_USERNAME/$IMAGE_NAME

# Тестирование образа
print_color $BLUE "🧪 Тестирование образа..."
if docker run --rm $DOCKER_USERNAME/$IMAGE_NAME:$VERSION python -c "import sys; print('Python version:', sys.version); import aiogram; print('Aiogram imported successfully')"; then
    print_color $GREEN "✅ Образ прошел базовые тесты"
else
    print_color $RED "❌ Образ не прошел тесты"
    exit 1
fi

# Публикация на Docker Hub
print_color $BLUE "📤 Публикация образа на Docker Hub..."
docker push $DOCKER_USERNAME/$IMAGE_NAME:$VERSION
docker push $DOCKER_USERNAME/$IMAGE_NAME:latest

print_header "🎉 ОБНОВЛЕНИЕ ЗАВЕРШЕНО УСПЕШНО!"

print_color $GREEN "✅ Git репозиторий обновлен"
print_color $GREEN "✅ Тег $VERSION создан и отправлен"
print_color $GREEN "✅ Docker образ собран и опубликован"
echo

print_color $CYAN "🔗 Ссылки:"
echo "   📂 GitHub: https://github.com/$DOCKER_USERNAME/$GITHUB_REPO"
echo "   🐳 Docker Hub: https://hub.docker.com/r/$DOCKER_USERNAME/$IMAGE_NAME"
echo "   🏷️  Релиз: https://github.com/$DOCKER_USERNAME/$GITHUB_REPO/releases/tag/$VERSION"
echo

print_color $YELLOW "📋 Команды для обновления на сервере:"
echo "   docker pull $DOCKER_USERNAME/$IMAGE_NAME:$VERSION"
echo "   docker-compose down && docker-compose up -d"
echo

print_color $BLUE "🎯 Следующие шаги:"
echo "   1. Проверьте релиз на GitHub"
echo "   2. Обновите сервер командами выше"
echo "   3. Протестируйте бота"
echo 