# 🔧 Исправление подключения к Supabase

## ❌ Ваша текущая проблема:
```
Хост: db.fqmmqmojvafquunkovmv.supabase.co
Порт: 6543
Ошибка: [Errno 11001] getaddrinfo failed
```

## ✅ Правильные настройки:

### **Измените .env файл:**

```env
# ПРАВИЛЬНО (Direct Connection):
POSTGRES_HOST=fqmmqmojvafquunkovmv.supabase.co
POSTGRES_PORT=5432

# НЕПРАВИЛЬНО (убрать db. и порт 6543):
# POSTGRES_HOST=db.fqmmqmojvafquunkovmv.supabase.co
# POSTGRES_PORT=6543
```

### **Полный .env пример:**
```env
BOT_TOKEN=your_telegram_bot_token_here
USE_POSTGRES=true
POSTGRES_HOST=fqmmqmojvafquunkovmv.supabase.co
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_supabase_password
POSTGRES_SSL=require
```

## 🎯 Как найти правильные параметры в Supabase:

1. **Откройте Supabase Dashboard**
2. **Settings → Database**
3. **Найдите "Connection parameters"**
4. **Используйте "Direct connection" (НЕ "Connection pooling")**

### **Должно быть так:**
- **Host:** `your-project-ref.supabase.co` (БЕЗ db.)
- **Port:** `5432` (НЕ 6543)
- **Database:** `postgres`
- **User:** `postgres`

## 🧪 После исправления:

1. **Обновите .env файл** с правильными параметрами
2. **Запустите тест:**
   ```bash
   python test_supabase_connection.py
   ```
3. **Должно показать:** ✅ Подключение к Supabase успешно! 