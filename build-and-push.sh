#!/bin/bash

# Скрипт для сборки и публикации Docker образа на Docker Hub
# Использование: ./build-and-push.sh [username] [tag]

set -e  # Остановка при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода цветного текста
print_color() {
    printf "${1}${2}${NC}\n"
}

# Проверка аргументов
DOCKER_USERNAME=${1:-""}
TAG=${2:-"latest"}

if [ -z "$DOCKER_USERNAME" ]; then
    print_color $RED "Ошибка: Не указан Docker Hub username"
    echo "Использование: $0 <docker_hub_username> [tag]"
    echo "Пример: $0 myusername latest"
    exit 1
fi

# Имя образа
IMAGE_NAME="gospel-bot"
FULL_IMAGE_NAME="${DOCKER_USERNAME}/${IMAGE_NAME}"

print_color $BLUE "🚀 Начинаем сборку и публикацию Docker образа"
print_color $YELLOW "📦 Образ: ${FULL_IMAGE_NAME}:${TAG}"

# Проверка наличия Docker
if ! command -v docker &> /dev/null; then
    print_color $RED "❌ Docker не установлен или недоступен"
    exit 1
fi

# Проверка авторизации в Docker Hub
print_color $BLUE "🔐 Проверка авторизации в Docker Hub..."
if ! docker info | grep -q "Username"; then
    print_color $YELLOW "⚠️  Необходима авторизация в Docker Hub"
    print_color $BLUE "Выполните: docker login"
    docker login
fi

# Сборка образа
print_color $BLUE "🔨 Сборка Docker образа..."
docker build -t ${FULL_IMAGE_NAME}:${TAG} .

# Также создаем тег latest если это не latest
if [ "$TAG" != "latest" ]; then
    print_color $BLUE "🏷️  Создание тега latest..."
    docker tag ${FULL_IMAGE_NAME}:${TAG} ${FULL_IMAGE_NAME}:latest
fi

# Показываем информацию об образе
print_color $BLUE "📊 Информация об образе:"
docker images ${FULL_IMAGE_NAME}

# Тестирование образа
print_color $BLUE "🧪 Тестирование образа..."
if docker run --rm ${FULL_IMAGE_NAME}:${TAG} python -c "import sys; print('Python version:', sys.version); import aiogram; print('Aiogram imported successfully')"; then
    print_color $GREEN "✅ Образ прошел базовые тесты"
else
    print_color $RED "❌ Образ не прошел тесты"
    exit 1
fi

# Публикация на Docker Hub
print_color $BLUE "📤 Публикация образа на Docker Hub..."
docker push ${FULL_IMAGE_NAME}:${TAG}

if [ "$TAG" != "latest" ]; then
    print_color $BLUE "📤 Публикация тега latest..."
    docker push ${FULL_IMAGE_NAME}:latest
fi

print_color $GREEN "🎉 Успешно! Образ опубликован на Docker Hub"
print_color $BLUE "📋 Для использования выполните:"
echo "   docker pull ${FULL_IMAGE_NAME}:${TAG}"
echo "   docker run -d --name gospel-bot --env-file .env ${FULL_IMAGE_NAME}:${TAG}"

print_color $YELLOW "🔗 Ссылка на Docker Hub: https://hub.docker.com/r/${DOCKER_USERNAME}/${IMAGE_NAME}" 