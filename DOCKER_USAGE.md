# 🐳 Использование Docker образа Gospel Bot

## 📦 Готовый образ на Docker Hub

Образ доступен по адресу: **`probedrik/gospel-bot`**

🔗 **Docker Hub**: https://hub.docker.com/r/probedrik/gospel-bot

## 🚀 Быстрый запуск

### 1. Создайте файл с переменными окружения

```bash
# Создайте .env файл
cat > .env << EOF
BOT_TOKEN=ваш_токен_бота_здесь
ADMIN_USER_ID=ваш_telegram_id
EOF
```

### 2. Запустите бот

```bash
# Простой запуск
docker run -d \
  --name gospel-bot \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  --restart unless-stopped \
  probedrik/gospel-bot:latest
```

### 3. Или используйте Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  bible-bot:
    image: probedrik/gospel-bot:latest
    container_name: bible-bot
    restart: unless-stopped
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    env_file:
      - .env
    environment:
      - TZ=Europe/Moscow
```

Запуск:
```bash
docker-compose up -d
```

## 📋 Управление контейнером

```bash
# Просмотр логов
docker logs bible-bot

# Логи в реальном времени
docker logs -f bible-bot

# Остановка
docker stop bible-bot

# Перезапуск
docker restart bible-bot

# Удаление
docker rm bible-bot
```

## 🔧 Обновление

```bash
# Остановка и удаление старого контейнера
docker stop bible-bot && docker rm bible-bot

# Загрузка новой версии
docker pull probedrik/gospel-bot:latest

# Запуск новой версии
docker run -d \
  --name gospel-bot \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  --restart unless-stopped \
  probedrik/gospel-bot:latest
```

## 📊 Мониторинг

```bash
# Статус контейнера
docker ps

# Использование ресурсов
docker stats bible-bot

# Проверка здоровья
docker inspect --format='{{.State.Health.Status}}' bible-bot
```

## ⚙️ Переменные окружения

| Переменная | Описание | Обязательная |
|------------|----------|--------------|
| `BOT_TOKEN` | Токен Telegram бота | ✅ |
| `ADMIN_USER_ID` | ID администратора | ✅ |
| `OPENAI_API_KEY` | Ключ OpenAI API | ❌ |
| `BIBLE_API_KEY` | Ключ Bible API | ❌ |
| `LOG_LEVEL` | Уровень логирования | ❌ |

## 🔗 Полезные ссылки

- 📖 [Полная документация по развертыванию](DOCKER_DEPLOYMENT.md)
- 🐳 [Docker Hub репозиторий](https://hub.docker.com/r/probedrik/gospel-bot)
- 📋 [Основная документация проекта](README.md) 