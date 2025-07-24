# ✅ План миграции Gospel Bot на PostgreSQL

## 🎯 **Цель миграции**
Перенести все данные из SQLite в PostgreSQL и загрузить планы чтения в базу данных.

## 📋 **Что создано для миграции:**

### ✅ **Новые файлы:**
- `database/postgres_manager.py` - PostgreSQL менеджер базы данных
- `migrate_to_postgres.py` - скрипт автоматической миграции
- `docker-compose.postgres.yml` - Docker конфигурация с PostgreSQL
- `init-db.sql` - SQL скрипт инициализации PostgreSQL
- `MIGRATION_TO_POSTGRES.md` - полное руководство по миграции

### ✅ **Обновленные файлы:**
- `requirements.txt` - добавлен `asyncpg>=0.29.0`
- `env.example` - добавлены настройки PostgreSQL

## 🚀 **Быстрая миграция (рекомендуется)**

### 1. **Подготовка**
```bash
# Сделайте backup текущих данных
cp .env .env.backup
cp -r data data_backup

# Добавьте в .env PostgreSQL настройки:
echo "" >> .env
echo "# PostgreSQL настройки" >> .env
echo "USE_POSTGRES=true" >> .env
echo "POSTGRES_HOST=postgres" >> .env
echo "POSTGRES_PORT=5432" >> .env
echo "POSTGRES_DB=gospel_bot" >> .env
echo "POSTGRES_USER=postgres" >> .env
echo "POSTGRES_PASSWORD=gospel123" >> .env
```

### 2. **Остановите бота**
```bash
docker-compose down
```

### 3. **Запустите PostgreSQL**
```bash
docker-compose -f docker-compose.postgres.yml up -d
```

### 4. **Выполните миграцию**

#### **Если нет Python на сервере (только Docker):**
```bash
# Windows PowerShell
.\docker-migration.ps1

# Linux/macOS
./docker-migration.sh
```

#### **Если есть Python:**
```bash
# Установите asyncpg
pip install asyncpg

# Запустите миграцию
python migrate_to_postgres.py
```

### 5. **Проверьте результат**
```bash
# Подключитесь к PostgreSQL
docker exec -it gospel-bot-postgres psql -U postgres -d gospel_bot

# В psql консоли проверьте таблицы:
\dt

# Проверьте данные:
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM bookmarks;
SELECT COUNT(*) FROM reading_plans;
\q
```

## 📊 **Что будет мигрировано:**

### ✅ **Пользовательские данные:**
- Все пользователи из таблицы `users`
- Все закладки из таблицы `bookmarks`
- Лимиты ИИ из таблицы `ai_limits`
- Прогресс чтения из `reading_progress` и `reading_parts_progress`

### ✅ **Планы чтения:**
- `Евангелие-на-каждый-день` (48 дней)
- `Классический-план-чтения-Библии-за-1-год` (365 дней)
- `План-чтения-Библии-ВЗ-и-НЗ` (365 дней)

### ✅ **Новые возможности PostgreSQL:**
- **Планы чтения в БД** - больше не нужны CSV файлы
- **Расширенные закладки** - поддержка диапазонов стихов и заметок
- **Лучшая производительность** - индексы и оптимизированные запросы
- **Надежность** - ACID транзакции и репликация

## 🔧 **Альтернативный способ (без Docker)**

Если вы не используете Docker:

### 1. **Установите PostgreSQL**
```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib

# Создайте базу данных
sudo -u postgres createdb gospel_bot
sudo -u postgres createuser --interactive
```

### 2. **Настройте .env**
```bash
USE_POSTGRES=true
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=gospel_bot
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
```

### 3. **Выполните миграцию**
```bash
python migrate_to_postgres.py \
  --postgres-host localhost \
  --postgres-user your_user \
  --postgres-password your_password
```

## ⚠️ **Важные моменты:**

### **Backup:**
- Обязательно сделайте backup перед миграцией
- SQLite база сохраняется в `data/bible_bot.db`
- Настройки бота сохраняются в `.env.backup`

### **Тестирование:**
- После миграции протестируйте все функции бота
- Проверьте закладки, планы чтения, AI функции
- Убедитесь, что прогресс чтения сохранился

### **Производительность:**
- PostgreSQL может быть медленнее на старте (инициализация)
- Зато быстрее работает с большими объемами данных
- Поддерживает множественные подключения

## 🔄 **Откат (если что-то пошло не так):**

```bash
# Остановите PostgreSQL
docker-compose -f docker-compose.postgres.yml down

# Восстановите настройки
cp .env.backup .env

# Запустите старую версию
docker-compose up -d
```

## 📝 **Логи миграции:**

Миграция создает файл `migration.log` с подробными логами:
```bash
tail -f migration.log  # Просмотр логов в реальном времени
```

## 🎉 **После успешной миграции:**

1. ✅ **Все пользовательские данные перенесены**
2. ✅ **Планы чтения загружены в БД**
3. ✅ **Бот работает с PostgreSQL**
4. ✅ **Улучшенная производительность**
5. ✅ **Расширенные возможности закладок**

## 🚨 **Проблемы и решения:**

### "Connection refused"
- Убедитесь, что PostgreSQL запущен
- Проверьте настройки подключения в `.env`

### "Authentication failed"
- Проверьте пароль PostgreSQL
- Убедитесь, что пользователь имеет права на базу данных

### "Tables not found"
- PostgreSQL менеджер создает таблицы автоматически
- При проблемах посмотрите логи: `docker-compose logs postgres`

---

**🎯 Готовы к миграции? Следуйте шагам из раздела "Быстрая миграция"!** 