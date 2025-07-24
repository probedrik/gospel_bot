# 🔐 Настройка SSL сертификата для Supabase

## 📋 Шаги настройки:

### 1. **Обновите .env файл с SSL сертификатом:**

```env
# Правильные параметры из Supabase (Session pooler):
POSTGRES_HOST=aws-0-us-east-1.pooler.supabase.com
POSTGRES_PORT=5432
POSTGRES_USER=postgres.fqmmqmojvafquunkovmv
POSTGRES_PASSWORD=your_password
POSTGRES_DB=postgres

# SSL с сертификатом:
POSTGRES_SSL=require
POSTGRES_SSL_CERT=./prod-ca-2021.crt

USE_POSTGRES=true
```

### 2. **Убедитесь что сертификат на месте:**
```bash
# Проверьте что файл существует
ls -la prod-ca-2021.crt

# Должен быть в корне проекта:
# ├── bot.py
# ├── prod-ca-2021.crt  ← здесь
# ├── .env
# └── ...
```

### 3. **Протестируйте подключение:**
```bash
python test_supabase_connection.py
```

**Ожидаемый результат:**
```
🔍 Проверка параметров подключения к Supabase:
   Хост: aws-0-us-east-1.pooler.supabase.com
   Порт: 5432
   База: postgres
   Пользователь: postgres.fqmmqmojvafquunkovmv
   SSL: require
   SSL сертификат: ./prod-ca-2021.crt
   Пароль: установлен

🔄 Попытка подключения к Supabase...
🔐 Используется SSL сертификат: ./prod-ca-2021.crt
✅ Подключение к Supabase успешно!
```

## 🐳 **Настройка для Docker:**

### **Обновите docker-compose.supabase.yml:**
```yaml
version: '3.8'

services:
  bible-bot:
    image: probedrik/gospel-bot:latest
    container_name: bible-bot-supabase
    restart: unless-stopped
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./prod-ca-2021.crt:/app/prod-ca-2021.crt  # Монтируем сертификат
    env_file:
      - .env
    environment:
      - TZ=Europe/Moscow
      - USE_POSTGRES=true
      - POSTGRES_SSL_CERT=/app/prod-ca-2021.crt  # Путь внутри контейнера
```

## 🔧 **Возможные проблемы:**

### ❌ "SSL сертификат не найден"
```bash
# Проверьте путь к файлу
ls -la ./prod-ca-2021.crt

# Исправьте путь в .env:
POSTGRES_SSL_CERT=./prod-ca-2021.crt
```

### ❌ "SSL connection failed"
```bash
# Попробуйте без сертификата (стандартный SSL):
POSTGRES_SSL=require
# POSTGRES_SSL_CERT=  # закомментируйте
```

### ❌ Проблемы в Docker
```bash
# Убедитесь что сертификат монтируется:
docker-compose -f docker-compose.supabase.yml exec bible-bot ls -la /app/prod-ca-2021.crt
```

## 📊 **Преимущества SSL сертификата:**

- ✅ **Повышенная безопасность** - проверка подлинности сервера
- ✅ **Защита от MITM атак** 
- ✅ **Более надежное соединение**
- ✅ **Соответствие best practices**

## 🚀 **Готовые команды:**

```bash
# 1. Тестирование подключения
python test_supabase_connection.py

# 2. Запуск бота локально
python bot.py

# 3. Запуск в Docker
docker-compose -f docker-compose.supabase.yml up -d

# 4. Просмотр логов
docker-compose -f docker-compose.supabase.yml logs -f bible-bot
``` 