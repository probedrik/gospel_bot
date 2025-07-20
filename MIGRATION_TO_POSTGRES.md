# 🐘 Миграция Gospel Bot на PostgreSQL

Этот документ описывает процесс миграции бота с SQLite на PostgreSQL.

## 📋 **Преимущества PostgreSQL**

- ✅ **Производительность** - лучше для больших объемов данных
- ✅ **Надежность** - ACID транзакции, репликация
- ✅ **Масштабируемость** - поддержка множественных подключений
- ✅ **Расширенные типы данных** - JSON, массивы, полнотекстовый поиск
- ✅ **Планы чтения в БД** - больше не нужны CSV файлы

## 🛠️ **Новая структура данных**

### **Планы чтения теперь в базе данных:**
- `reading_plans` - информация о планах
- `reading_plan_days` - дни планов с текстом чтения
- Больше нет зависимости от CSV файлов

### **Улучшенные закладки:**
- Поддержка диапазонов стихов (`verse_start`, `verse_end`)
- Поле для заметок (`note`)
- Улучшенная производительность поиска

## 🚀 **Быстрая миграция (Docker)**

### 1. **Обновите конфигурацию**

Создайте новый `.env` файл с настройками PostgreSQL:
```bash
# Скопируйте ваш текущий .env
cp .env .env.backup

# Добавьте PostgreSQL настройки
cat >> .env << 'EOF'

# ===========================================
# НАСТРОЙКИ POSTGRESQL
# ===========================================
USE_POSTGRES=true
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=gospel_bot
POSTGRES_USER=postgres
POSTGRES_PASSWORD=gospel123
EOF
```

### 2. **Остановите текущий бот**
```bash
docker-compose down
```

### 3. **Запустите PostgreSQL и бота**
```bash
# Используем новый docker-compose файл с PostgreSQL
docker-compose -f docker-compose.postgres.yml up -d
```

### 4. **Выполните миграцию данных**
```bash
# Установите зависимости для миграции
pip install asyncpg

# Запустите миграцию
python migrate_to_postgres.py

# Или с параметрами
python migrate_to_postgres.py \
  --sqlite-db data/bible_bot.db \
  --plans-csv data/plans_csv_final \
  --postgres-host localhost \
  --postgres-port 5432 \
  --postgres-db gospel_bot \
  --postgres-user postgres \
  --postgres-password gospel123
```

## 🔧 **Ручная настройка PostgreSQL**

### 1. **Установите PostgreSQL**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# CentOS/RHEL
sudo yum install postgresql postgresql-server postgresql-contrib

# macOS
brew install postgresql
```

### 2. **Создайте базу данных**
```bash
# Переключитесь на пользователя postgres
sudo -u postgres psql

# В psql консоли:
CREATE DATABASE gospel_bot;
CREATE USER gospel_bot_user WITH PASSWORD 'gospel_bot_pass';
GRANT ALL PRIVILEGES ON DATABASE gospel_bot TO gospel_bot_user;
\q
```

### 3. **Настройте .env файл**
```bash
USE_POSTGRES=true
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=gospel_bot
POSTGRES_USER=gospel_bot_user
POSTGRES_PASSWORD=gospel_bot_pass
```

### 4. **Установите зависимости**
```bash
pip install asyncpg
```

### 5. **Выполните миграцию**
```bash
python migrate_to_postgres.py
```

## 📊 **Что мигрируется**

### ✅ **Пользовательские данные:**
- Пользователи (`users`)
- Закладки (`bookmarks`) 
- Лимиты ИИ (`ai_limits`)
- Прогресс чтения (`reading_progress`, `reading_parts_progress`)

### ✅ **Планы чтения:**
- Все CSV планы из `data/plans_csv_final/`
- Автоматическое создание таблиц `reading_plans` и `reading_plan_days`

## 🔍 **Проверка миграции**

### 1. **Проверьте подключение**
```bash
# В psql консоли:
\c gospel_bot
\dt
```

Должны быть видны таблицы:
- `users`
- `bookmarks` 
- `ai_limits`
- `reading_plans`
- `reading_plan_days`
- `reading_progress`
- `reading_parts_progress`

### 2. **Проверьте данные**
```sql
-- Количество пользователей
SELECT COUNT(*) FROM users;

-- Количество закладок
SELECT COUNT(*) FROM bookmarks;

-- Количество планов чтения
SELECT COUNT(*) FROM reading_plans;

-- Пример плана чтения
SELECT * FROM reading_plans LIMIT 1;
SELECT * FROM reading_plan_days WHERE plan_id = 'Евангелие-на-каждый-день' LIMIT 5;
```

## 🐳 **Docker Compose файлы**

### **Новая конфигурация (`docker-compose.postgres.yml`):**
```yaml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: gospel_bot
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-gospel123}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  bible-bot:
    image: probedrik/gospel-bot:latest
    depends_on:
      - postgres
    environment:
      - USE_POSTGRES=true
      - POSTGRES_HOST=postgres
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    env_file:
      - .env

volumes:
  postgres_data:
```

## ⚡ **Быстрые команды**

### **Запуск с PostgreSQL:**
```bash
docker-compose -f docker-compose.postgres.yml up -d
```

### **Просмотр логов:**
```bash
docker-compose -f docker-compose.postgres.yml logs -f bible-bot
```

### **Подключение к PostgreSQL:**
```bash
docker exec -it gospel-bot-postgres psql -U postgres -d gospel_bot
```

### **Backup PostgreSQL:**
```bash
docker exec gospel-bot-postgres pg_dump -U postgres gospel_bot > backup.sql
```

### **Restore PostgreSQL:**
```bash
docker exec -i gospel-bot-postgres psql -U postgres gospel_bot < backup.sql
```

## 🔄 **Откат на SQLite**

Если нужно вернуться к SQLite:

1. **Остановите PostgreSQL:**
```bash
docker-compose -f docker-compose.postgres.yml down
```

2. **Обновите .env:**
```bash
USE_POSTGRES=false
```

3. **Запустите старую конфигурацию:**
```bash
docker-compose up -d
```

## 🚨 **Возможные проблемы**

### **Проблема:** "Connection refused"
**Решение:** Убедитесь, что PostgreSQL запущен и доступен по указанному адресу

### **Проблема:** "Authentication failed" 
**Решение:** Проверьте пароль и права пользователя

### **Проблема:** "Database does not exist"
**Решение:** Создайте базу данных вручную

### **Проблема:** Медленная миграция
**Решение:** Миграция больших объемов данных может занимать время

## 📞 **Поддержка**

При возникновении проблем:
1. Проверьте логи: `docker-compose logs -f`
2. Проверьте файл `migration.log`
3. Убедитесь в корректности настроек `.env`

## 🎯 **Следующие шаги**

После успешной миграции:
1. Протестируйте все функции бота
2. Создайте backup PostgreSQL базы
3. Настройте мониторинг PostgreSQL
4. При необходимости оптимизируйте производительность 