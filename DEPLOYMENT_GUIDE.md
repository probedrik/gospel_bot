# 🚀 Руководство по развертыванию Gospel Bot

## 📦 Доступные версии

### GitHub Repository
```bash
git clone https://github.com/probedrik/gospel_bot.git
cd gospel_bot
```

### DockerHub Images
- **Latest:** `probedrik/gospel-bot:latest`
- **Version 2.0.0:** `probedrik/gospel-bot:v2.0.0`

## 🐳 Быстрый запуск с Docker

### 1. Создайте .env файл
```bash
# Обязательные переменные
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_USER_ID=your_telegram_user_id

# Supabase (рекомендуется)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key

# YooKassa (опционально)
YOOKASSA_SHOP_ID=your_shop_id
YOOKASSA_SECRET_KEY=your_secret_key

# OpenRouter API (для ИИ)
OPENROUTER_API_KEY=your_openrouter_api_key
```

### 2. Запустите контейнер
```bash
docker run -d \
  --name gospel-bot \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  --restart unless-stopped \
  probedrik/gospel-bot:latest
```

### 3. Проверьте логи
```bash
docker logs -f gospel-bot
```

## 🔧 Развертывание из исходного кода

### 1. Клонируйте репозиторий
```bash
git clone https://github.com/probedrik/gospel_bot.git
cd gospel_bot
```

### 2. Установите зависимости
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

### 3. Настройте переменные окружения
Создайте файл `.env` с необходимыми переменными (см. выше).

### 4. Запустите бота
```bash
python bot.py
```

## 📱 Android приложение

### Требования
- Android Studio Arctic Fox или новее
- JDK 11 или новее
- Android SDK 34

### Сборка
```bash
cd android
./gradlew assembleDebug
```

APK файл будет создан в `android/app/build/outputs/apk/debug/`

## 🌟 Новые возможности v2.0.0

### ✨ Основные функции
- 📱 **Android приложение** с Supabase интеграцией
- 💳 **YooKassa платежи** для пожертвований и премиум ИИ
- 🌟 **Telegram Stars** поддержка
- 🤖 **Премиум ИИ запросы** с расширенными возможностями
- ☁️ **Supabase backend** для кроссплатформенности

### 🔧 Технические улучшения
- 🗄️ Миграция с Room Database на Supabase
- 🔄 Универсальный менеджер БД
- 📊 Улучшенная система платежей
- 🛡️ Повышенная безопасность и обработка ошибок

### 🐛 Исправления
- ✅ Исправлены кнопки главного меню
- 🔀 Правильный порядок регистрации роутеров
- 📝 Убрано избыточное логирование

## 🔒 Безопасность

### Рекомендации
- Используйте сильные пароли для всех сервисов
- Регулярно обновляйте токены и ключи API
- Настройте HTTPS для webhook'ов
- Используйте переменные окружения для секретов

### Переменные окружения
Никогда не коммитьте файлы с секретными данными в репозиторий!

## 📞 Поддержка

- **GitHub Issues:** https://github.com/probedrik/gospel_bot/issues
- **Telegram:** @Const_AI
- **Email:** support@gospelbot.com

## 📄 Лицензия

MIT License - см. файл LICENSE для деталей.

---

**Версия:** 2.0.0  
**Дата обновления:** $(date)  
**Статус:** ✅ Стабильная версия