# Deployment Scripts Documentation

This document describes the automated deployment scripts for Gospel Bot.

## Overview

The deployment process consists of two scripts:
1. **`deploy-update.sh`** - Local script for building and pushing updates
2. **`update-server.sh`** - Server script for pulling and deploying updates

## Scripts Location

Both scripts are now included in the Git repository:
- `deploy-update.sh` - Run locally on development machine
- `update-server.sh` - Run on production server (included in repo)

## Quick Setup

### On Development Machine
```bash
# Make script executable
chmod +x deploy-update.sh

# Run deployment
./deploy-update.sh
```

### On Production Server
```bash
# Update repository to get the latest scripts
git pull origin master

# Make script executable
chmod +x update-server.sh

# Run server update (Docker only)
./update-server.sh

# Run server update with forced Git refresh
./update-server.sh --force-git
```

## Script Options

### `update-server.sh` Options:
- **No arguments**: Update Docker containers only
- **`--force-git`**: Force Git repository refresh + Docker update

## 📝 Что делает `deploy-update.sh`:

1. ✅ **Проверяет окружение** (Git, Docker, авторизация)
2. 📝 **Автоматически генерирует новую версию** (увеличивает patch)
3. 💬 **Запрашивает сообщение коммита**
4. 📊 **Показывает статус Git** и добавляет изменения
5. 💾 **Создает коммит** с указанным сообщением
6. 🏷️ **Создает и отправляет тег** версии в GitHub
7. 📤 **Отправляет изменения** в GitHub
8. 🔨 **Собирает Docker образ** с новой версией
9. 🧪 **Тестирует образ** (базовые проверки)
10. 📤 **Публикует на Docker Hub** (версия + latest)
11. 🎉 **Показывает ссылки** и команды для обновления сервера

## 📝 Что делает `update-server.sh`:

**Обычный режим:**
1. ✅ **Проверяет окружение** (Docker, docker-compose)
2. 📥 **Загружает новый образ** с Docker Hub
3. ⏹️ **Останавливает текущую версию**
4. ▶️ **Запускает новую версию**
5. 📊 **Показывает статус** и логи
6. 🎯 **Предлагает полезные команды**

**С опцией `--force-git`:**
1. 💾 **Сохраняет .env и docker-compose.yml**
2. 🔄 **Принудительно обновляет код** из Git (git reset --hard)
3. ♻️ **Восстанавливает локальные настройки**
4. ✅ **Далее выполняет обычный процесс Docker обновления**

## 🎯 Рабочий процесс

### 1. Разработка и тестирование
```bash
# Внесите изменения в код
nano handlers/text_messages.py

# Протестируйте локально
python bot.py

# Зафиксируйте изменения
./deploy-update.sh v2.5.1 "Fix: Исправлена кнопка в темах"
```

### 2. Обновление на сервере
```bash
# Обычное обновление (только Docker)
./update-server.sh

# Полное обновление (Git + Docker)
./update-server.sh --force-git

# Альтернативный способ через git pull
git pull origin master
./update-server.sh
```

### 3. Решение проблем с Git на сервере
```bash
# Если есть конфликты или проблемы с Git
./update-server.sh --force-git

# Или вручную сбросить к состоянию репозитория
git fetch origin
git reset --hard origin/master
./update-server.sh
```

## 🔍 Полезные команды на сервере

```bash
# Статус контейнеров
docker-compose ps

# Логи в реальном времени
docker-compose logs -f bible-bot

# Перезапуск без обновления
docker-compose restart bible-bot

# Остановка
docker-compose down

# Принудительное обновление (пересоздание контейнера)
docker-compose up -d --force-recreate
```

## 🆘 Устранение проблем

### Проблема: "Docker не авторизован"
```bash
docker login
# Введите логин и пароль Docker Hub
```

### Проблема: "Образ не найден"
```bash
# Проверьте доступность образа
docker pull probedrik/gospel-bot:latest

# Посмотрите доступные версии
curl -s https://registry.hub.docker.com/v2/repositories/probedrik/gospel-bot/tags/ | jq .
```

### Проблема: "Контейнер не запускается"
```bash
# Посмотрите подробные логи
docker-compose logs bible-bot

# Запустите в интерактивном режиме для отладки
docker run -it --rm --env-file .env probedrik/gospel-bot:latest bash
```

### Проблема: "Конфликты Git или устаревший код"
```bash
# Быстрое решение - принудительное обновление
./update-server.sh --force-git

# Или полное перескачивание проекта
cd ..
rm -rf gospel/
git clone https://github.com/probedrik/gospel_bot.git gospel
cd gospel/
# Восстановите .env и docker-compose.yml из бэкапа
```

### Проблема: "Изменения не применяются"
```bash
# Проверьте версию Docker образа
docker images | grep gospel-bot

# Принудительно пересоздайте контейнер
docker-compose up -d --force-recreate

# Или с обновлением кода
./update-server.sh --force-git
```

## 📋 Переменные окружения

Убедитесь, что файл `.env` содержит все необходимые переменные:

```bash
# Обязательные
BOT_TOKEN=your_bot_token
ADMIN_USER_ID=your_telegram_id

# Опциональные
OPENROUTER_API_KEY=your_openrouter_key
TZ=Europe/Moscow
LOG_LEVEL=INFO
```

## 🔗 Ссылки

- **GitHub**: https://github.com/probedrik/gospel_bot
- **Docker Hub**: https://hub.docker.com/r/probedrik/gospel-bot
- **Releases**: https://github.com/probedrik/gospel_bot/releases 