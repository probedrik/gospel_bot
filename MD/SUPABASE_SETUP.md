# 🐘 Настройка Supabase для Gospel Bot

Полная инструкция по подключению Gospel Bot к облачной базе данных Supabase.

## 📋 Шаг 1: Создание проекта в Supabase

1. **Зайдите на [supabase.com](https://supabase.com)** и войдите в аккаунт
2. **Создайте новый проект:**
   - Нажмите "New Project"
   - Выберите организацию
   - Введите название проекта (например, "gospel-bot")
   - Введите надежный пароль для базы данных (сохраните его!)
   - Выберите регион (лучше ближайший к вашему серверу)
   - Нажмите "Create new project"

3. **Дождитесь завершения создания проекта** (1-2 минуты)

## 🔑 Шаг 2: Получение параметров подключения

1. **Откройте Settings → Database** в вашем проекте Supabase
2. **Найдите секцию "Connection parameters":**
   - **Host:** обычно `db.your-project-ref.supabase.co`
   - **Database name:** `postgres`
   - **Port:** `5432`
   - **User:** `postgres`
   - **Password:** тот, что вы указали при создании проекта

3. **Альтернативно** можете использовать готовую строку подключения из секции "Connection string"

## ⚙️ Шаг 3: Настройка переменных окружения

1. **Скопируйте файл-пример:**
   ```bash
   cp env.supabase.example .env
   ```

2. **Отредактируйте `.env` файл:**
   ```env
   # Telegram Bot Configuration
   BOT_TOKEN=your_telegram_bot_token_here
   
   # Database Configuration - Supabase
   USE_POSTGRES=true
   POSTGRES_HOST=db.your-project-ref.supabase.co
   POSTGRES_PORT=5432
   POSTGRES_DB=postgres
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=your_supabase_database_password
   POSTGRES_SSL=require
   
   # Остальные настройки...
   ```

3. **Важно:** Замените `your-project-ref` на реальный идентификатор вашего проекта

## 🗄️ Шаг 4: Создание таблиц в Supabase

1. **Откройте SQL Editor** в Supabase Dashboard
2. **Скопируйте содержимое файла `supabase_tables.sql`**
3. **Вставьте в SQL Editor и выполните** (нажмите "Run")
4. **Проверьте результат** - должно быть создано 8 таблиц

Или выполните SQL прямо здесь:

```sql
-- Просто скопируйте и выполните весь код из supabase_tables.sql
```

## 🧪 Шаг 5: Проверка подключения

**Протестируйте подключение локально:**

```bash
# Установите зависимости (если еще не установлены)
pip install asyncpg python-dotenv

# Запустите тест подключения
python test_supabase_connection.py
```

**Ожидаемый результат:**
```
🚀 Тестирование подключения к Supabase для Gospel Bot
============================================================
🔍 Проверка параметров подключения к Supabase:
   Хост: db.your-project-ref.supabase.co
   Порт: 5432
   База: postgres
   Пользователь: postgres
   SSL: require
   Пароль: установлен

🔄 Попытка подключения к Supabase...
✅ Подключение к Supabase успешно!
📊 Версия PostgreSQL: PostgreSQL 15.x ...

📋 Найдено таблиц Gospel Bot: 8/8
   ✅ ai_limits
   ✅ bookmarks
   ✅ reading_plan_days
   ✅ reading_plans
   ✅ reading_parts_progress
   ✅ reading_progress
   ✅ user_reading_plans
   ✅ users

🎉 Проверка завершена успешно!

✅ Готово! Можете запускать бота с Supabase:
   docker-compose -f docker-compose.supabase.yml up -d
```

## 🚀 Шаг 6: Запуск бота

**Запустите бота с Supabase:**

```bash
# Остановите предыдущие контейнеры (если запущены)
docker-compose down

# Запустите с Supabase конфигурацией
docker-compose -f docker-compose.supabase.yml up -d

# Проверьте логи
docker-compose -f docker-compose.supabase.yml logs -f bible-bot
```

**В логах должно быть:**
```
INFO:database.postgres_manager:Инициализация PostgreSQL: db.your-project-ref.supabase.co:5432/postgres (SSL: require)
INFO:database.universal_manager:🐘 Инициализация PostgreSQL менеджера
INFO:database.postgres_manager:SSL соединение: require
INFO:database.postgres_manager:Пул соединений PostgreSQL создан
INFO:database.postgres_manager:Все таблицы PostgreSQL созданы
INFO:database.postgres_manager:База данных PostgreSQL инициализирована
INFO:__main__:🗄️ Используется база данных: PostgreSQL
INFO:__main__:✅ Инициализация БД успешна
```

## 🔧 Шаг 7: Миграция данных (опционально)

Если у вас есть данные в SQLite, которые нужно перенести:

```bash
# Запустите миграцию
python migrate_to_postgres.py --postgres-host db.your-project-ref.supabase.co --yes
```

## 🛠️ Возможные проблемы и решения

### ❌ "Name or service not known"
- **Причина:** Неверный хост в POSTGRES_HOST
- **Решение:** Проверьте хост в Supabase Settings → Database

### ❌ "Invalid password"
- **Причина:** Неверный пароль
- **Решение:** Проверьте пароль базы данных в Supabase

### ❌ "SSL connection required"
- **Причина:** Supabase требует SSL
- **Решение:** Убедитесь что `POSTGRES_SSL=require` в .env

### ❌ "Connection timeout"
- **Причина:** Проблемы с сетью или firewall
- **Решение:** Проверьте интернет-соединение, попробуйте другой порт

### ❌ Таблицы не создаются
- **Причина:** Ошибки в SQL или нет прав
- **Решение:** Выполните `supabase_tables.sql` вручную в SQL Editor

## 📊 Мониторинг в Supabase

После настройки можете использовать Supabase Dashboard для:

- **Table Editor:** Просмотр и редактирование данных
- **SQL Editor:** Выполнение запросов
- **Database → Logs:** Мониторинг подключений
- **API → Logs:** Логи API запросов

## 🎯 Преимущества Supabase

- ✅ **Облачное хранение** - данные в безопасности
- ✅ **Автоматические бэкапы** 
- ✅ **Масштабируемость**
- ✅ **Мониторинг и аналитика**
- ✅ **SSL/TLS защита**
- ✅ **Географическое распределение**

---

## 📞 Поддержка

Если возникли проблемы:
1. Проверьте логи: `docker-compose -f docker-compose.supabase.yml logs -f bible-bot`
2. Запустите тест: `python test_supabase_connection.py`
3. Проверьте настройки в Supabase Dashboard 