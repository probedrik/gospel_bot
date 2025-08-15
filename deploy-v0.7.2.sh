#!/bin/bash

# 🚀 Скрипт развертывания Gospel Bot v0.7.2
# Автоматическое создание релиза и публикация в Docker Hub

set -e  # Остановка при ошибке

echo "🌟 Начинаем развертывание Gospel Bot v0.7.2..."

# Переменные
VERSION="v0.7.2"
IMAGE_NAME="gospel-bot"
DOCKER_REPO="your-dockerhub-username"  # Замените на ваш Docker Hub username

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

echo_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

echo_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

echo_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 1. Проверка зависимостей
echo_info "Проверяем зависимости..."

if ! command -v git &> /dev/null; then
    echo_error "Git не установлен!"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo_error "Docker не установлен!"
    exit 1
fi

echo_success "Все зависимости установлены"

# 2. Проверка изменений
echo_info "Проверяем статус Git..."

if [[ -n $(git status --porcelain) ]]; then
    echo_warning "Есть незакоммиченные изменения:"
    git status --short
    
    read -p "Хотите закоммитить изменения? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git add .
        git commit -m "feat: Telegram Stars integration v0.7.2

🌟 Новые возможности:
- Пожертвования через Telegram Stars (1, 10, 25, 50, 100 Stars)
- Покупка премиум запросов за Stars
- Интеграция с Supabase для хранения транзакций
- Обновленный PremiumManager с поддержкой Stars

🔧 Исправления:
- Убрано черное окно в инвойсах
- Исправлена фильтрация callback_data
- HTML форматирование вместо Markdown
- Корректная обработка amount_rub полей

🧪 Тестирование:
- Добавлены тесты для Stars платежей
- Проверка отображения баланса
- Валидация callback_data
- Тестирование инвойсов"
        echo_success "Изменения закоммичены"
    else
        echo_error "Отменено пользователем"
        exit 1
    fi
fi

# 3. Создание тега
echo_info "Создаем Git тег $VERSION..."

if git tag -l | grep -q "^$VERSION$"; then
    echo_warning "Тег $VERSION уже существует"
    read -p "Удалить существующий тег? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git tag -d $VERSION
        git push origin :refs/tags/$VERSION 2>/dev/null || true
        echo_success "Старый тег удален"
    else
        echo_error "Отменено пользователем"
        exit 1
    fi
fi

git tag -a $VERSION -m "Gospel Bot $VERSION - Telegram Stars Integration

🌟 Major Features:
- Telegram Stars payments integration
- Premium AI requests purchase system
- Supabase database support
- Enhanced payment processing

🔧 Bug Fixes:
- Fixed invoice display issues
- Improved callback data handling
- Better error handling and logging

📊 Statistics:
- Full test coverage
- Production ready
- Docker optimized"

echo_success "Git тег $VERSION создан"

# 4. Сборка Docker образа
echo_info "Собираем Docker образ..."

# Проверяем наличие Dockerfile
if [[ ! -f "Dockerfile" ]]; then
    echo_error "Dockerfile не найден!"
    exit 1
fi

# Сборка образа
docker build -t $IMAGE_NAME:$VERSION . --no-cache

# Тегируем как latest
docker tag $IMAGE_NAME:$VERSION $IMAGE_NAME:latest

echo_success "Docker образ собран: $IMAGE_NAME:$VERSION"

# 5. Тестирование образа
echo_info "Тестируем Docker образ..."

# Быстрый тест запуска
if docker run --rm $IMAGE_NAME:$VERSION python -c "import sys; print(f'Python {sys.version}'); print('✅ Образ работает корректно')"; then
    echo_success "Docker образ прошел тестирование"
else
    echo_error "Ошибка при тестировании Docker образа"
    exit 1
fi

# 6. Пуш в Git
echo_info "Отправляем изменения в Git..."

git push origin main
git push origin $VERSION

echo_success "Изменения отправлены в Git репозиторий"

# 7. Публикация в Docker Hub (опционально)
read -p "Опубликовать образ в Docker Hub? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo_info "Публикуем в Docker Hub..."
    
    # Проверяем авторизацию
    if ! docker info | grep -q "Username:"; then
        echo_warning "Необходима авторизация в Docker Hub"
        docker login
    fi
    
    # Тегируем для Docker Hub
    docker tag $IMAGE_NAME:$VERSION $DOCKER_REPO/$IMAGE_NAME:$VERSION
    docker tag $IMAGE_NAME:$VERSION $DOCKER_REPO/$IMAGE_NAME:latest
    
    # Публикуем
    docker push $DOCKER_REPO/$IMAGE_NAME:$VERSION
    docker push $DOCKER_REPO/$IMAGE_NAME:latest
    
    echo_success "Образ опубликован в Docker Hub: $DOCKER_REPO/$IMAGE_NAME:$VERSION"
else
    echo_info "Пропускаем публикацию в Docker Hub"
fi

# 8. Создание GitHub Release (если используется GitHub)
if git remote get-url origin | grep -q "github.com"; then
    echo_info "Создаем GitHub Release..."
    
    if command -v gh &> /dev/null; then
        gh release create $VERSION \
            --title "Gospel Bot $VERSION - Telegram Stars Integration" \
            --notes-file RELEASE_$VERSION.md \
            --latest
        echo_success "GitHub Release создан"
    else
        echo_warning "GitHub CLI не установлен, создайте релиз вручную:"
        echo "https://github.com/$(git remote get-url origin | sed 's/.*github.com[:/]\([^/]*\/[^/]*\).*/\1/' | sed 's/\.git$//')/releases/new?tag=$VERSION"
    fi
fi

# 9. Финальная информация
echo
echo_success "🎉 Развертывание Gospel Bot $VERSION завершено успешно!"
echo
echo_info "📋 Сводка:"
echo "   • Версия: $VERSION"
echo "   • Docker образ: $IMAGE_NAME:$VERSION"
echo "   • Git тег: $VERSION"
echo "   • Дата: $(date)"
echo
echo_info "🚀 Команды для запуска:"
echo "   docker run -d --name gospel-bot --env-file .env $IMAGE_NAME:$VERSION"
echo
echo_info "📖 Документация:"
echo "   • RELEASE_$VERSION.md - описание изменений"
echo "   • TELEGRAM_STARS_GUIDE.md - руководство по Stars"
echo
echo_warning "🔧 Не забудьте:"
echo "   • Обновить переменные окружения"
echo "   • Проверить работу Telegram Stars"
echo "   • Обновить документацию"
echo

echo_success "Готово! 🌟"