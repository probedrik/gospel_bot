# 🚀 Быстрый деплой Gospel Bot v2.5.0

## 📦 На сервере выполните:

### 1. Создайте рабочую директорию
```bash
mkdir -p ~/gospel-bot
cd ~/gospel-bot
```

### 2. Создайте .env файл
```bash
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
```

### 3. Создайте docker-compose.yml
```bash
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
```

### 4. Создайте необходимые директории
```bash
mkdir -p data logs
```

### 5. Отредактируйте .env файл
```bash
nano .env
# Замените BOT_TOKEN и ADMIN_USER_ID на реальные значения
```

### 6. Запустите бота
```bash
# Скачайте и запустите образ
docker-compose up -d

# Проверьте логи
docker-compose logs -f bible-bot
```

## 🔧 Управление ботом

### Остановить бота
```bash
docker-compose down
```

### Обновить до последней версии
```bash
docker-compose pull
docker-compose up -d
```

### Посмотреть логи
```bash
docker-compose logs -f bible-bot
```

### Перезапустить бота
```bash
docker-compose restart bible-bot
```

## 📊 Проверка статуса
```bash
# Проверить запущенные контейнеры
docker ps

# Проверить использование ресурсов
docker stats gospel-bot

# Проверить размер данных
du -sh data/
```

## 🎯 Новые функции в v2.5.0

- ✅ **Стили номеров стихов**: жирный, код, курсив
- ✅ **Формат глава:стих**: `2:12` вместо `12`
- ✅ **Режим цитат**: визуальные blockquote
- ✅ **Настройка пробелов**: 1-5 пробелов после номера
- ✅ **Улучшенные планы чтения**
- ✅ **Исправления форматирования**

## 🔗 Полезные ссылки

- **Docker Hub**: https://hub.docker.com/r/probedrik/gospel-bot
- **GitHub**: https://github.com/probedrik/gospel_bot
- **Документация**: README.md в репозитории

---
*Последнее обновление: $(date)* 