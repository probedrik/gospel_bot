#!/bin/bash

# Скрипт автоматического деплоя Gospel Bot v2.5.0
# Использование: bash <(curl -s https://raw.githubusercontent.com/probedrik/gospel_bot/master/deploy-server.sh)

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_color() {
    printf "${1}${2}${NC}\n"
}

print_color $BLUE "🚀 Автоматический деплой Gospel Bot v2.5.0"

# Создание рабочей директории
WORKDIR="$HOME/gospel-bot"
print_color $BLUE "📁 Создание рабочей директории: $WORKDIR"
mkdir -p "$WORKDIR"
cd "$WORKDIR"

# Создание docker-compose.yml
print_color $BLUE "📝 Создание docker-compose.yml"
cat > docker-compose.yml << 'EOF'
services:
  bible-bot:
    image: probedrik/gospel-bot:v2.5.0
    container_name: gospel-bot
    restart: unless-stopped
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    env_file:
      - .env
    environment:
      - TZ=Europe/Moscow
EOF

# Создание .env файла если его нет
if [ ! -f .env ]; then
    print_color $YELLOW "⚠️  Создание .env файла..."
    cat > .env << 'EOF'
# ===========================================
# ОСНОВНЫЕ НАСТРОЙКИ БОТА (ОБЯЗАТЕЛЬНЫЕ)
# ===========================================

# Токен Telegram бота (получить у @BotFather)
BOT_TOKEN=ваш_токен_бота_здесь

# ID администратора бота (ваш Telegram ID)  
ADMIN_USER_ID=ваш_telegram_id

# ===========================================
# API КЛЮЧИ ДЛЯ ИИ ФУНКЦИЙ (ОПЦИОНАЛЬНО)
# ===========================================

# OpenRouter API ключ для ИИ функций
OPENROUTER_API_KEY=ваш_openrouter_токен

# ===========================================
# ДОПОЛНИТЕЛЬНЫЕ НАСТРОЙКИ
# ===========================================

# Часовой пояс
TZ=Europe/Moscow

# Уровень логирования
LOG_LEVEL=INFO
EOF
    
    print_color $RED "❌ ВНИМАНИЕ! Отредактируйте .env файл с вашими токенами:"
    print_color $YELLOW "nano .env"
    print_color $YELLOW "После редактирования запустите: docker-compose up -d"
    exit 0
else
    print_color $GREEN "✅ .env файл уже существует"
fi

# Создание директорий
print_color $BLUE "📂 Создание директорий для данных и логов"
mkdir -p data logs

# Проверка Docker
if ! command -v docker &> /dev/null; then
    print_color $RED "❌ Docker не установлен!"
    print_color $YELLOW "Установите Docker: https://docs.docker.com/engine/install/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_color $RED "❌ Docker Compose не установлен!"
    print_color $YELLOW "Установите Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Загрузка образа
print_color $BLUE "📦 Загрузка образа probedrik/gospel-bot:v2.5.0"
docker-compose pull

# Запуск бота
print_color $BLUE "🚀 Запуск бота"
docker-compose up -d

# Проверка статуса
sleep 5
if docker ps | grep -q gospel-bot; then
    print_color $GREEN "🎉 Бот успешно запущен!"
    print_color $BLUE "📊 Статус контейнера:"
    docker ps | grep gospel-bot
    
    print_color $BLUE "📋 Полезные команды:"
    echo "  Логи:           docker-compose logs -f bible-bot"
    echo "  Остановить:     docker-compose down" 
    echo "  Перезапустить:  docker-compose restart bible-bot"
    echo "  Обновить:       docker-compose pull && docker-compose up -d"
else
    print_color $RED "❌ Ошибка запуска! Проверьте логи:"
    print_color $YELLOW "docker-compose logs bible-bot"
fi

print_color $BLUE "🔗 Документация: https://github.com/probedrik/gospel_bot" 