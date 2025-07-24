# 🎉 Gospel Bot v2.5.0 - Успешно развернут!

## ✅ Что сделано:

### 📦 **Docker образ опубликован**
- **Образ**: `probedrik/gospel-bot:v2.5.0`
- **Docker Hub**: https://hub.docker.com/r/probedrik/gospel-bot
- **Размер**: 781MB (оптимизирован)
- **Тэги**: `v2.5.0`, `latest`

### 🏷️ **Git релиз**
- **Тэг**: `v2.5.0`
- **GitHub**: https://github.com/probedrik/gospel_bot
- **Коммит**: `3de1dad`

---

## 🚀 Как развернуть на сервере:

### Метод 1: Автоматический деплой (одна команда)
```bash
bash <(curl -s https://raw.githubusercontent.com/probedrik/gospel_bot/master/deploy-server.sh)
```

### Метод 2: Ручной деплой
```bash
# 1. Создать директорию
mkdir -p ~/gospel-bot && cd ~/gospel-bot

# 2. Скачать docker-compose.yml
curl -O https://raw.githubusercontent.com/probedrik/gospel_bot/master/docker-compose.yml

# 3. Создать .env файл (заменить токены на реальные)
curl -O https://raw.githubusercontent.com/probedrik/gospel_bot/master/env.docker.example
mv env.docker.example .env
nano .env

# 4. Запустить
docker-compose up -d
```

### Метод 3: Docker команда
```bash
docker run -d \
  --name gospel-bot \
  --restart unless-stopped \
  -v ~/gospel-bot/data:/app/data \
  -v ~/gospel-bot/logs:/app/logs \
  -e BOT_TOKEN="7915703119:AAFMqfiFwYw6p-deMgrVghRBcXXtGKMCs8g" \
  -e ADMIN_USER_ID="2040516595" \
  -e OPENROUTER_API_KEY="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" \
  -e TZ="Europe/Moscow" \
  probedrik/gospel-bot:v2.5.0
```

---

## 🆕 Новые функции в v2.5.0:

### 🎨 **Стили номеров стихов**
- **Жирный**: **12** Текст стиха...
- **Код**: `12` Текст стиха...
- **Курсив**: _12_ Текст стиха...
- **Команда**: `/set_verse_style`

### 📊 **Формат "глава:стих"**
- **Включить**: `/toggle_chapter_numbers`
- **Пример**: `2:12` вместо `12`
- **Работает**: со всеми стилями

### 💬 **Режим цитат**
- **Визуальные blockquote** в Telegram
- **Команда**: `/toggle_quote`
- **Применяется**: к стихам и толкованиям

### ⚙️ **Настройка пробелов**
- **1-5 пробелов** после номера стиха
- **Команда**: `/set_spacing`
- **По умолчанию**: 1 пробел

### 🔧 **Исправления**
- Синхронизация форматирования стихов и планов чтения
- Исправлен MarkdownV2 режим для ИИ-ответов
- Улучшена функция `format_ai_or_commentary`

---

## 🔧 Управление ботом на сервере:

### Проверить статус
```bash
docker ps | grep gospel-bot
docker logs gospel-bot
```

### Перезапустить
```bash
docker restart gospel-bot
# или
docker-compose restart bible-bot
```

### Обновить до новой версии
```bash
docker pull probedrik/gospel-bot:latest
docker stop gospel-bot
docker rm gospel-bot
# Затем запустить заново
```

### Остановить
```bash
docker stop gospel-bot
# или
docker-compose down
```

### Посмотреть использование ресурсов
```bash
docker stats gospel-bot
```

---

## 📋 Административные команды:

### Форматирование стихов
- `/set_format` - HTML/Markdown/MarkdownV2
- `/set_verse_style` - жирный/код/курсив
- `/toggle_chapter_numbers` - глава:стих
- `/set_spacing` - количество пробелов
- `/toggle_quote` - режим цитат
- `/toggle_verses` - включить/выключить номера

### Форматирование толкований
- `/set_commentary_format` - HTML/Markdown/MarkdownV2

### Общие настройки
- `/admin` - панель администратора
- `/settings` - подробные настройки

---

## 📊 Системные требования:

- **ОС**: Linux (Ubuntu 20.04+, CentOS 8+, Debian 11+)
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **RAM**: минимум 512MB, рекомендуется 1GB
- **Диск**: 2GB свободного места
- **Сеть**: доступ к api.telegram.org

---

## 📞 Поддержка:

- **GitHub Issues**: https://github.com/probedrik/gospel_bot/issues
- **Документация**: README.md в репозитории
- **Docker Hub**: https://hub.docker.com/r/probedrik/gospel-bot

---

## 📈 Следующие обновления:

Планируется:
- Поддержка баз данных (PostgreSQL, MySQL)
- Веб-интерфейс администратора
- Метрики и мониторинг
- Кэширование ИИ-ответов
- Поддержка тем оформления

---

*Создано: $(date)*
*Версия: v2.5.0* 