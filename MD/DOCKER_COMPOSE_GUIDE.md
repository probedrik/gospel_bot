# 🐳 Запуск Gospel Bot через Docker Compose

## 🚀 Быстрый старт

### 1. Подготовка файлов

Убедитесь, что у вас есть следующие файлы:
- `docker-compose.yml` ✅
- `.env` (создадим ниже)

### 2. Создание .env файла

```bash
# Скопируйте пример и отредактируйте
cp env.docker.example .env
```

Или создайте `.env` файл вручную:

```bash
# Создайте .env файл
cat > .env << EOF
# Основные настройки (ОБЯЗАТЕЛЬНЫЕ)
BOT_TOKEN=ваш_токен_бота_здесь
ADMIN_USER_ID=ваш_telegram_id

# ИИ функции (ОПЦИОНАЛЬНО)
OPENROUTER_API_KEY=ваш_новый_openrouter_токен

# Дополнительные настройки
TZ=Europe/Moscow
LOG_LEVEL=INFO
EOF
```

### 3. Получение токенов

#### Telegram Bot Token
1. Напишите @BotFather в Telegram
2. Создайте нового бота: `/newbot`
3. Скопируйте токен

#### Ваш Telegram ID
1. Напишите @userinfobot в Telegram
2. Скопируйте ваш ID

#### OpenRouter API Key (для ИИ функций)
1. Зайдите на https://openrouter.ai/
2. Зарегистрируйтесь/войдите
3. Создайте новый API ключ
4. Скопируйте ключ

### 4. Запуск бота

```bash
# Запуск в фоновом режиме
docker compose up -d

# Или запуск с выводом логов
docker compose up
```

## 📋 Управление ботом

### Основные команды

```bash
# Запуск
docker compose up -d

# Остановка
docker compose down

# Перезапуск
docker compose restart

# Просмотр логов
docker compose logs bible-bot

# Логи в реальном времени
docker compose logs -f bible-bot

# Статус сервисов
docker compose ps

# Обновление образа
docker compose pull
docker compose up -d
```

### Проверка состояния

```bash
# Статус контейнера
docker compose ps

# Использование ресурсов
docker stats bible-bot

# Проверка здоровья
docker inspect --format='{{.State.Health.Status}}' bible-bot
```

## 🔧 Настройка и отладка

### Просмотр конфигурации

```bash
# Показать итоговую конфигурацию
docker compose config

# Проверить переменные окружения
docker compose exec bible-bot env | grep -E "(BOT_TOKEN|ADMIN_USER_ID|OPENROUTER)"
```

### Отладка

```bash
# Подключиться к контейнеру
docker compose exec bible-bot bash

# Проверить логи приложения
docker compose exec bible-bot cat logs/bot.log

# Перезапуск с пересборкой (если нужно)
docker compose up -d --force-recreate
```

### Проблемы и решения

#### Бот не запускается
```bash
# Проверьте логи
docker compose logs bible-bot

# Проверьте переменные окружения
docker compose exec bible-bot env | grep BOT_TOKEN
```

#### Проблемы с правами доступа
```bash
# Создайте директории с правильными правами
mkdir -p data logs
chmod 755 data logs
```

#### Обновление образа
```bash
# Остановите бота
docker compose down

# Загрузите новую версию
docker compose pull

# Запустите обновленную версию
docker compose up -d
```

## 📊 Мониторинг

### Логирование

Логи автоматически ротируются:
- Максимальный размер файла: 10MB
- Количество файлов: 3
- Логи сохраняются в `./logs/`

### Health Check

Встроенная проверка здоровья:
- Интервал: 30 секунд
- Таймаут: 10 секунд
- Повторы: 3
- Время запуска: 40 секунд

```bash
# Проверка здоровья
docker compose exec bible-bot python -c "import asyncio; print('Bot is healthy')"
```

## 🔒 Безопасность

### Переменные окружения

**НИКОГДА не включайте секреты в docker-compose.yml!**

✅ **Правильно** (через .env файл):
```yaml
env_file:
  - .env
```

❌ **Неправильно** (секреты в коде):
```yaml
environment:
  - BOT_TOKEN=1234567890:ABC...  # НЕ ДЕЛАЙТЕ ТАК!
```

### Файл .env

Убедитесь, что `.env` файл:
- Не попадает в Git (добавлен в `.gitignore`)
- Имеет правильные права доступа: `chmod 600 .env`
- Содержит актуальные токены

## 📁 Структура файлов

```
gospel/
├── docker-compose.yml          # Конфигурация Docker Compose
├── .env                        # Переменные окружения (создать)
├── env.docker.example          # Пример .env файла
├── data/                       # База данных (создается автоматически)
├── logs/                       # Логи приложения (создается автоматически)
└── DOCKER_COMPOSE_GUIDE.md     # Эта инструкция
```

## 🎯 Примеры использования

### Разработка

```bash
# Запуск с выводом логов для отладки
docker compose up

# В другом терминале - просмотр логов
docker compose logs -f bible-bot
```

### Продакшн

```bash
# Запуск в фоновом режиме
docker compose up -d

# Настройка автозапуска (systemd)
sudo systemctl enable docker
```

### Обновление

```bash
# Обновление до новой версии
docker compose down
docker compose pull
docker compose up -d

# Проверка, что все работает
docker compose ps
docker compose logs bible-bot
```

## 🔗 Полезные ссылки

- 📖 [Основная документация](README.md)
- 🐳 [Docker Hub образ](https://hub.docker.com/r/probedrik/gospel-bot)
- 📋 [Полная документация по Docker](DOCKER_DEPLOYMENT.md)
- 🚀 [Краткая инструкция](DOCKER_USAGE.md)

---

**🎉 Готово! Ваш Gospel Bot запущен через Docker Compose!** 