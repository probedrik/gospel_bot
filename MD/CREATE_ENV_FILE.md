# 🔧 Создание .env файла для работы с Supabase

## ❌ Проблема
Скрипт показывает:
```
📊 Используется БД: SQLite
❌ Планы в Supabase не найдены
```

Это происходит потому, что **нет файла .env** с настройками Supabase.

## ✅ Решение

### **Шаг 1: Создайте файл .env**
Скопируйте пример и заполните реальными данными:

```bash
cp env.supabase.example .env
```

### **Шаг 2: Отредактируйте .env файл**
Откройте `.env` и замените значения:

```env
# === НАСТРОЙКИ БОТА ===
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
ADMIN_ID=123456789

# === НАСТРОЙКИ БАЗЫ ДАННЫХ ===
USE_SUPABASE=true

# === НАСТРОЙКИ SUPABASE ===
SUPABASE_URL=https://abcdefghijklmnop.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# === НАСТРОЙКИ ИИ ===
OPENAI_API_KEY=sk-...
AI_LIMIT_PER_DAY=10

# === ЛОГИРОВАНИЕ ===
LOG_LEVEL=INFO
TZ=Europe/Moscow
```

### **Шаг 3: Где взять данные Supabase**

1. **Откройте [Supabase Dashboard](https://app.supabase.com/)**
2. **Выберите ваш проект**
3. **Перейдите в Settings → API**
4. **Скопируйте:**
   - **Project URL** → `SUPABASE_URL`
   - **Anon public key** → `SUPABASE_KEY`

### **Шаг 4: Проверьте настройки**
```bash
python force_switch_to_supabase_plans.py
```

**Должно показать:**
```
📊 Используется БД: Supabase
✅ Найдено X планов в Supabase
```

## 🎯 После создания .env файла

1. **Проверьте переключение:**
```bash
python force_switch_to_supabase_plans.py
```

2. **Если все работает, пересоберите образ:**
```bash
.\build-and-push.ps1 -Username "probedrik" -Tag "v2.8.10"
```

3. **Обновите контейнер:**
```bash
docker-compose -f docker-compose.supabase-sdk.yml up -d
```

## 🔍 Проверка логов
```bash
docker logs -f bible-bot-supabase | grep -E "(Supabase|планы)"
```

**Должно быть:**
```
INFO: ☁️ Инициализация Supabase менеджера
INFO: 🗄️ Используется база данных: Supabase
INFO: ✅ Планы загружены из Supabase
```

## ⚠️ Важные замечания

- **Файл .env не должен попадать в Git** (он в .gitignore)
- **SUPABASE_KEY** должен быть **anon public key**, не service key
- **USE_SUPABASE=true** обязательно для использования Supabase
- **Планы должны быть импортированы** в Supabase (что вы уже делали)

Основная проблема была в отсутствии .env файла! 🎯 