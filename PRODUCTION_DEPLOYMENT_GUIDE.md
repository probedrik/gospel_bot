# 🚀 Руководство по запуску бота в продакшен

## 📋 Содержание
1. [Подготовка VPS](#подготовка-vps)
2. [Настройка Supabase RLS](#настройка-supabase-rls)
3. [Конфигурация бота](#конфигурация-бота)
4. [Настройка статистики](#настройка-статистики)
5. [Мониторинг и логирование](#мониторинг-и-логирование)
6. [Резервное копирование](#резервное-копирование)
7. [Безопасность](#безопасность)

---

# 🖥️ Подготовка VPS

## 🔧 Системные требования
- **ОС**: Ubuntu 20.04+ или CentOS 8+
- **RAM**: Минимум 1GB, рекомендуется 2GB+
- **CPU**: 1 vCPU (достаточно для старта)
- **Диск**: 20GB+ свободного места
- **Сеть**: Стабильное интернет-соединение

## 📦 Установка зависимостей

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker и Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Перезагрузка для применения прав
sudo reboot
```

## 📁 Создание рабочей директории

```bash
# Создание директорий
mkdir -p /opt/gospel-bot/{data,logs,config}
cd /opt/gospel-bot

# Создание пользователя для бота
sudo useradd -r -s /bin/false -d /opt/gospel-bot botuser
sudo chown -R botuser:botuser /opt/gospel-bot
```

---

# 🗄️ Настройка Supabase RLS

## 🔐 Включение Row Level Security

### 1. Настройка RLS политик

```sql
-- Подключение к Supabase SQL Editor

-- Включение RLS для таблицы пользователей
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Политика: пользователи видят только свои данные
CREATE POLICY "Users can view own data" ON users
    FOR SELECT USING (auth.uid() = id::text OR telegram_id = current_setting('app.current_user_telegram_id')::bigint);

-- Политика: пользователи могут обновлять свои данные
CREATE POLICY "Users can update own data" ON users
    FOR UPDATE USING (telegram_id = current_setting('app.current_user_telegram_id')::bigint);

-- Политика: создание новых пользователей
CREATE POLICY "Allow user creation" ON users
    FOR INSERT WITH CHECK (true);

-- Включение RLS для закладок
ALTER TABLE bookmarks ENABLE ROW LEVEL SECURITY;

-- Политика: пользователи видят только свои закладки
CREATE POLICY "Users can view own bookmarks" ON bookmarks
    FOR ALL USING (user_id = (
        SELECT id FROM users WHERE telegram_id = current_setting('app.current_user_telegram_id')::bigint
    ));

-- Включение RLS для прогресса чтения
ALTER TABLE user_reading_progress ENABLE ROW LEVEL SECURITY;

-- Политика: пользователи видят только свой прогресс
CREATE POLICY "Users can view own progress" ON user_reading_progress
    FOR ALL USING (user_id = (
        SELECT id FROM users WHERE telegram_id = current_setting('app.current_user_telegram_id')::bigint
    ));

-- Таблицы только для чтения (без RLS)
-- books, verses, themes, reading_plans, calendar_events
-- Эти таблицы доступны всем для чтения
```

### 2. Создание функции для установки контекста пользователя

```sql
-- Функция для установки текущего пользователя
CREATE OR REPLACE FUNCTION set_current_user_telegram_id(telegram_id bigint)
RETURNS void AS $$
BEGIN
    PERFORM set_config('app.current_user_telegram_id', telegram_id::text, true);
END;
$$ LANGUAGE plpgsql;

-- Предоставление прав на выполнение
GRANT EXECUTE ON FUNCTION set_current_user_telegram_id TO anon, authenticated;
```

### 3. Настройка Service Role

```sql
-- Создание роли для бота с полными правами
-- В Supabase Dashboard -> Settings -> API
-- Используйте service_role key для операций бота

-- Для анонимного доступа (только чтение справочников)
GRANT SELECT ON books, verses, themes, reading_plans, calendar_events TO anon;
```

## 🔧 Обновление кода бота для работы с RLS

```python
# services/database.py
import asyncio
from supabase import create_client, Client
import logging

logger = logging.getLogger(__name__)

class SupabaseManager:
    def __init__(self, url: str, service_key: str):
        self.client: Client = create_client(url, service_key)
        
    async def set_user_context(self, telegram_id: int):
        """Установка контекста пользователя для RLS"""
        try:
            await asyncio.to_thread(
                self.client.rpc,
                'set_current_user_telegram_id',
                {'telegram_id': telegram_id}
            )
        except Exception as e:
            logger.error(f"Ошибка установки контекста пользователя {telegram_id}: {e}")
    
    async def add_user(self, telegram_id: int, username: str, first_name: str):
        """Добавление пользователя с автоматической установкой контекста"""
        try:
            # Устанавливаем контекст
            await self.set_user_context(telegram_id)
            
            # Проверяем существование пользователя
            existing = await asyncio.to_thread(
                self.client.table('users')
                .select('id')
                .eq('telegram_id', telegram_id)
                .execute
            )
            
            if not existing.data:
                # Создаем нового пользователя
                result = await asyncio.to_thread(
                    self.client.table('users')
                    .insert({
                        'telegram_id': telegram_id,
                        'username': username,
                        'first_name': first_name,
                        'created_at': 'now()',
                        'ai_usage_count': 0,
                        'ai_usage_date': 'CURRENT_DATE'
                    })
                    .execute
                )
                logger.info(f"Создан пользователь {telegram_id}")
                return result.data[0]
            else:
                return existing.data[0]
                
        except Exception as e:
            logger.error(f"Ошибка добавления пользователя {telegram_id}: {e}")
            raise
```

---

# ⚙️ Конфигурация бота

## 📄 Создание docker-compose.yml

```yaml
# /opt/gospel-bot/docker-compose.yml
version: '3.8'

services:
  gospel-bot:
    image: probedrik/gospel-bot:latest
    container_name: gospel-bot-production
    restart: unless-stopped
    environment:
      # Telegram Bot
      - BOT_TOKEN=${BOT_TOKEN}
      
      # Supabase
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
      
      # OpenRouter AI
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - OPENROUTER_PREMIUM_API_KEY=${OPENROUTER_PREMIUM_API_KEY}
      
      # Analytics
      - GOOGLE_ANALYTICS_ID=${GOOGLE_ANALYTICS_ID}
      - MIXPANEL_TOKEN=${MIXPANEL_TOKEN}
      
      # Payment
      - YOOKASSA_SHOP_ID=${YOOKASSA_SHOP_ID}
      - YOOKASSA_SECRET_KEY=${YOOKASSA_SECRET_KEY}
      
      # Monitoring
      - SENTRY_DSN=${SENTRY_DSN}
      
      # Admin
      - ADMIN_USER_ID=${ADMIN_USER_ID}
      
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    
    networks:
      - gospel-bot-network
    
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/health', timeout=10)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Nginx для веб-хуков (опционально)
  nginx:
    image: nginx:alpine
    container_name: gospel-bot-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    networks:
      - gospel-bot-network
    depends_on:
      - gospel-bot

networks:
  gospel-bot-network:
    driver: bridge
```

## 🔐 Создание .env файла

```bash
# /opt/gospel-bot/.env

# Telegram
BOT_TOKEN=your_bot_token_here
ADMIN_USER_ID=your_telegram_id

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_service_role_key_here

# OpenRouter
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_PREMIUM_API_KEY=your_premium_key

# Analytics
GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX
MIXPANEL_TOKEN=your_mixpanel_token

# Payment
YOOKASSA_SHOP_ID=your_shop_id
YOOKASSA_SECRET_KEY=your_secret_key

# Monitoring
SENTRY_DSN=https://your-sentry-dsn

# Security
chmod 600 .env
```

---

# 📊 Настройка статистики

## 📈 Google Analytics 4

### 1. Настройка GA4

```bash
# Создание Google Analytics свойства
1. Зайти в https://analytics.google.com
2. Создать новое свойство
3. Включить Enhanced Ecommerce
4. Получить Measurement ID (G-XXXXXXXXXX)
```

### 2. Интеграция в бот

```python
# services/analytics.py
import aiohttp
import asyncio
import logging
from typing import Dict, Any
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

class AnalyticsManager:
    def __init__(self, ga_measurement_id: str, ga_api_secret: str):
        self.ga_measurement_id = ga_measurement_id
        self.ga_api_secret = ga_api_secret
        self.ga_endpoint = f"https://www.google-analytics.com/mp/collect"
        
    async def track_event(self, user_id: int, event_name: str, parameters: Dict[str, Any] = None):
        """Отправка события в Google Analytics"""
        if parameters is None:
            parameters = {}
            
        # Базовые параметры
        base_params = {
            'user_id': str(user_id),
            'session_id': str(uuid.uuid4()),
            'timestamp_micros': int(datetime.now().timestamp() * 1000000)
        }
        
        # Объединяем с переданными параметрами
        parameters.update(base_params)
        
        payload = {
            'client_id': str(user_id),
            'events': [{
                'name': event_name,
                'params': parameters
            }]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.ga_endpoint,
                    params={
                        'measurement_id': self.ga_measurement_id,
                        'api_secret': self.ga_api_secret
                    },
                    json=payload
                ) as response:
                    if response.status == 200:
                        logger.debug(f"GA event sent: {event_name}")
                    else:
                        logger.error(f"GA error: {response.status}")
        except Exception as e:
            logger.error(f"Analytics error: {e}")

# Глобальный экземпляр
analytics = AnalyticsManager(
    ga_measurement_id=os.getenv('GOOGLE_ANALYTICS_ID'),
    ga_api_secret=os.getenv('GA_API_SECRET')
)
```

### 3. Отслеживание событий в обработчиках

```python
# handlers/commands.py
from services.analytics import analytics

@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext, db=None):
    user_id = message.from_user.id
    
    # Отслеживание начала использования бота
    await analytics.track_event(
        user_id=user_id,
        event_name='bot_start',
        parameters={
            'platform': 'telegram',
            'user_type': 'new' if not await db.user_exists(user_id) else 'returning'
        }
    )
    
    # Остальная логика команды...

# handlers/text_messages.py
@router.message(F.text == "📖 Выбрать книгу")
async def select_book(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    # Отслеживание использования функции выбора книги
    await analytics.track_event(
        user_id=user_id,
        event_name='book_selection_started',
        parameters={
            'source': 'main_menu'
        }
    )

# handlers/ai_assistant.py
async def process_ai_request(message: Message, user_id: int, verses: list):
    # Отслеживание использования ИИ
    await analytics.track_event(
        user_id=user_id,
        event_name='ai_explanation_requested',
        parameters={
            'verses_count': len(verses),
            'ai_type': 'regular',  # или 'premium'
            'content_type': 'verse_explanation'
        }
    )
```

## 📊 Mixpanel интеграция (альтернатива)

```python
# services/mixpanel_analytics.py
import aiohttp
import base64
import json
import time

class MixpanelAnalytics:
    def __init__(self, token: str):
        self.token = token
        self.endpoint = "https://api.mixpanel.com/track"
    
    async def track(self, user_id: int, event: str, properties: dict = None):
        if properties is None:
            properties = {}
            
        properties.update({
            'token': self.token,
            'distinct_id': str(user_id),
            'time': int(time.time()),
            '$insert_id': f"{user_id}_{event}_{int(time.time())}"
        })
        
        data = {
            'event': event,
            'properties': properties
        }
        
        encoded_data = base64.b64encode(json.dumps(data).encode()).decode()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.endpoint,
                    data={'data': encoded_data}
                ) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Mixpanel error: {e}")
            return False
```

## 📈 Собственная статистика в Supabase

### 1. Создание таблицы для аналитики

```sql
-- Таблица для хранения событий
CREATE TABLE analytics_events (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    telegram_id BIGINT,
    event_name VARCHAR(100) NOT NULL,
    event_properties JSONB DEFAULT '{}',
    session_id UUID,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_agent TEXT,
    ip_address INET
);

-- Индексы для быстрых запросов
CREATE INDEX idx_analytics_events_user_id ON analytics_events(user_id);
CREATE INDEX idx_analytics_events_event_name ON analytics_events(event_name);
CREATE INDEX idx_analytics_events_timestamp ON analytics_events(timestamp);
CREATE INDEX idx_analytics_events_telegram_id ON analytics_events(telegram_id);

-- Таблица для ежедневной статистики
CREATE TABLE daily_stats (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    total_users INTEGER DEFAULT 0,
    new_users INTEGER DEFAULT 0,
    active_users INTEGER DEFAULT 0,
    total_events INTEGER DEFAULT 0,
    ai_requests INTEGER DEFAULT 0,
    bookmarks_created INTEGER DEFAULT 0,
    UNIQUE(date)
);
```

### 2. Сервис для внутренней аналитики

```python
# services/internal_analytics.py
from supabase import Client
import asyncio
from datetime import datetime, date
import uuid
import logging

logger = logging.getLogger(__name__)

class InternalAnalytics:
    def __init__(self, supabase: Client):
        self.supabase = supabase
        
    async def track_event(
        self, 
        telegram_id: int, 
        event_name: str, 
        properties: dict = None,
        session_id: str = None
    ):
        """Отслеживание события во внутренней аналитике"""
        if properties is None:
            properties = {}
            
        if session_id is None:
            session_id = str(uuid.uuid4())
            
        try:
            # Получаем ID пользователя
            user_result = await asyncio.to_thread(
                self.supabase.table('users')
                .select('id')
                .eq('telegram_id', telegram_id)
                .execute
            )
            
            user_id = user_result.data[0]['id'] if user_result.data else None
            
            # Записываем событие
            await asyncio.to_thread(
                self.supabase.table('analytics_events')
                .insert({
                    'user_id': user_id,
                    'telegram_id': telegram_id,
                    'event_name': event_name,
                    'event_properties': properties,
                    'session_id': session_id,
                    'timestamp': datetime.now().isoformat()
                })
                .execute
            )
            
            logger.debug(f"Internal analytics: {event_name} for user {telegram_id}")
            
        except Exception as e:
            logger.error(f"Internal analytics error: {e}")
    
    async def get_daily_stats(self, days: int = 30) -> list:
        """Получение статистики за последние N дней"""
        try:
            result = await asyncio.to_thread(
                self.supabase.table('daily_stats')
                .select('*')
                .order('date', desc=True)
                .limit(days)
                .execute
            )
            return result.data
        except Exception as e:
            logger.error(f"Error getting daily stats: {e}")
            return []
    
    async def update_daily_stats(self):
        """Обновление ежедневной статистики"""
        today = date.today()
        
        try:
            # Общее количество пользователей
            total_users = await asyncio.to_thread(
                self.supabase.table('users')
                .select('id', count='exact')
                .execute
            )
            
            # Новые пользователи за сегодня
            new_users = await asyncio.to_thread(
                self.supabase.table('users')
                .select('id', count='exact')
                .gte('created_at', today.isoformat())
                .execute
            )
            
            # Активные пользователи за сегодня
            active_users = await asyncio.to_thread(
                self.supabase.table('analytics_events')
                .select('telegram_id', count='exact')
                .gte('timestamp', today.isoformat())
                .execute
            )
            
            # ИИ запросы за сегодня
            ai_requests = await asyncio.to_thread(
                self.supabase.table('analytics_events')
                .select('id', count='exact')
                .eq('event_name', 'ai_explanation_requested')
                .gte('timestamp', today.isoformat())
                .execute
            )
            
            # Создание статистики за день
            await asyncio.to_thread(
                self.supabase.table('daily_stats')
                .upsert({
                    'date': today.isoformat(),
                    'total_users': total_users.count,
                    'new_users': new_users.count,
                    'active_users': active_users.count,
                    'ai_requests': ai_requests.count
                })
                .execute
            )
            
        except Exception as e:
            logger.error(f"Error updating daily stats: {e}")
```

### 3. Middleware для автоматического отслеживания

```python
# middleware/analytics_middleware.py
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from services.internal_analytics import InternalAnalytics
import uuid

class AnalyticsMiddleware(BaseMiddleware):
    def __init__(self, analytics: InternalAnalytics):
        self.analytics = analytics
        super().__init__()

    async def __call__(
        self,
        handler,
        event: TelegramObject,
        data: dict
    ):
        # Генерируем session_id для сессии
        if 'session_id' not in data:
            data['session_id'] = str(uuid.uuid4())
            
        # Отслеживаем события
        if isinstance(event, Message):
            await self._track_message(event, data['session_id'])
        elif isinstance(event, CallbackQuery):
            await self._track_callback(event, data['session_id'])
            
        return await handler(event, data)
    
    async def _track_message(self, message: Message, session_id: str):
        """Отслеживание сообщений"""
        properties = {
            'message_type': 'text' if message.text else 'other',
            'chat_type': message.chat.type,
            'has_reply': bool(message.reply_to_message)
        }
        
        if message.text:
            if message.text.startswith('/'):
                event_name = 'command_used'
                properties['command'] = message.text.split()[0]
            else:
                event_name = 'message_sent'
                properties['text_length'] = len(message.text)
        else:
            event_name = 'media_sent'
            
        await self.analytics.track_event(
            telegram_id=message.from_user.id,
            event_name=event_name,
            properties=properties,
            session_id=session_id
        )
    
    async def _track_callback(self, callback: CallbackQuery, session_id: str):
        """Отслеживание нажатий на кнопки"""
        properties = {
            'callback_data': callback.data,
            'message_id': callback.message.message_id
        }
        
        await self.analytics.track_event(
            telegram_id=callback.from_user.id,
            event_name='button_clicked',
            properties=properties,
            session_id=session_id
        )
```

---

# 📊 Мониторинг и логирование

## 📝 Настройка логирования

```python
# config/logging_config.py
import logging
import logging.handlers
import os
from datetime import datetime

def setup_logging():
    """Настройка системы логирования"""
    
    # Создание директории для логов
    log_dir = '/app/logs'
    os.makedirs(log_dir, exist_ok=True)
    
    # Настройка форматтера
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Основной логгер
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Файловый обработчик с ротацией
    file_handler = logging.handlers.RotatingFileHandler(
        f'{log_dir}/bot.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Отдельный лог для ошибок
    error_handler = logging.handlers.RotatingFileHandler(
        f'{log_dir}/errors.log',
        maxBytes=10*1024*1024,
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    # Консольный вывод
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger
```

## 🔍 Sentry для отслеживания ошибок

```python
# services/sentry_config.py
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
import os

def setup_sentry():
    """Настройка Sentry для отслеживания ошибок"""
    sentry_dsn = os.getenv('SENTRY_DSN')
    
    if sentry_dsn:
        sentry_logging = LoggingIntegration(
            level=logging.INFO,
            event_level=logging.ERROR
        )
        
        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[sentry_logging],
            traces_sample_rate=0.1,
            environment="production"
        )
```

## 📈 Health Check эндпоинт

```python
# health_check.py
from aiohttp import web
import asyncio
import logging
from services.database import db

logger = logging.getLogger(__name__)

async def health_check(request):
    """Проверка здоровья сервиса"""
    try:
        # Проверка подключения к БД
        await db.execute_query("SELECT 1")
        
        return web.json_response({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'services': {
                'database': 'ok',
                'bot': 'running'
            }
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return web.json_response({
            'status': 'unhealthy',
            'error': str(e)
        }, status=500)

# Запуск веб-сервера для health check
async def start_health_server():
    app = web.Application()
    app.router.add_get('/health', health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', 8000)
    await site.start()
    logger.info("Health check server started on port 8000")
```

---

# 💾 Резервное копирование

## 📋 Скрипт для бэкапа Supabase

```bash
#!/bin/bash
# /opt/gospel-bot/scripts/backup.sh

# Настройки
BACKUP_DIR="/opt/gospel-bot/backups"
DATE=$(date +%Y%m%d_%H%M%S)
SUPABASE_PROJECT_ID="your_project_id"
SUPABASE_DB_PASSWORD="your_db_password"

# Создание директории для бэкапов
mkdir -p $BACKUP_DIR

# Бэкап базы данных
echo "Starting database backup..."
pg_dump -h db.${SUPABASE_PROJECT_ID}.supabase.co \
        -U postgres \
        -W \
        -d postgres \
        --no-owner \
        --no-privileges \
        -f ${BACKUP_DIR}/database_backup_${DATE}.sql

# Сжатие бэкапа
gzip ${BACKUP_DIR}/database_backup_${DATE}.sql

# Удаление старых бэкапов (старше 30 дней)
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "Backup completed: database_backup_${DATE}.sql.gz"

# Отправка в облако (опционально)
# aws s3 cp ${BACKUP_DIR}/database_backup_${DATE}.sql.gz s3://your-bucket/backups/
```

## ⏰ Настройка cron для автоматических бэкапов

```bash
# Добавление в crontab
crontab -e

# Бэкап каждый день в 2:00 ночи
0 2 * * * /opt/gospel-bot/scripts/backup.sh >> /opt/gospel-bot/logs/backup.log 2>&1

# Очистка логов каждую неделю
0 0 * * 0 find /opt/gospel-bot/logs -name "*.log" -mtime +7 -delete
```

---

# 🔒 Безопасность

## 🛡️ Настройка файрвола

```bash
# Установка UFW
sudo apt install ufw

# Базовые правила
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Разрешение SSH
sudo ufw allow ssh

# Разрешение HTTP/HTTPS (если используется webhook)
sudo ufw allow 80
sudo ufw allow 443

# Активация файрвола
sudo ufw enable
```

## 🔐 SSL сертификат (если используется webhook)

```bash
# Установка Certbot
sudo apt install certbot

# Получение сертификата
sudo certbot certonly --standalone -d your-domain.com

# Автообновление сертификата
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
```

## 📋 Чек-лист безопасности

- [ ] Использование environment переменных для секретов
- [ ] Настройка файрвола
- [ ] Регулярные обновления системы
- [ ] Мониторинг логов на подозрительную активность
- [ ] Ограничение прав пользователя бота
- [ ] Шифрование чувствительных данных в БД
- [ ] Настройка rate limiting
- [ ] Резервное копирование

---

# 🚀 Финальный запуск

## 📝 Пошаговое руководство

### 1. Проверка всех настроек

```bash
# Проверка переменных окружения
cd /opt/gospel-bot
cat .env | grep -v "^#" | grep -v "^$"

# Проверка Docker
docker --version
docker-compose --version
```

### 2. Запуск в продакшен

```bash
# Скачивание последней версии образа
docker-compose pull

# Запуск в фоновом режиме
docker-compose up -d

# Проверка логов
docker-compose logs -f gospel-bot

# Проверка health check
curl http://localhost:8000/health
```

### 3. Мониторинг после запуска

```bash
# Проверка статуса контейнера
docker-compose ps

# Мониторинг ресурсов
docker stats gospel-bot-production

# Проверка логов в реальном времени
tail -f /opt/gospel-bot/logs/bot.log
```

### 4. Настройка автозапуска

```bash
# Создание systemd сервиса
sudo tee /etc/systemd/system/gospel-bot.service > /dev/null <<EOF
[Unit]
Description=Gospel Bot
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/gospel-bot
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# Активация сервиса
sudo systemctl enable gospel-bot.service
sudo systemctl start gospel-bot.service
```

---

## ✅ Чек-лист готовности к продакшену

### Техническая готовность:
- [ ] VPS настроен и обновлен
- [ ] Docker и Docker Compose установлены
- [ ] Созданы все необходимые директории
- [ ] Настроены права доступа

### Supabase:
- [ ] RLS политики настроены и протестированы
- [ ] Таблицы аналитики созданы
- [ ] Service Role ключ получен
- [ ] Подключение к БД работает

### Конфигурация:
- [ ] .env файл создан и заполнен
- [ ] docker-compose.yml настроен
- [ ] Все API ключи получены и работают
- [ ] Переменные окружения проверены

### Аналитика:
- [ ] Google Analytics настроен
- [ ] Внутренняя аналитика подключена
- [ ] Middleware для отслеживания добавлен
- [ ] Тестовые события отправляются

### Мониторинг:
- [ ] Логирование настроено
- [ ] Sentry подключен
- [ ] Health check работает
- [ ] Алерты настроены

### Безопасность:
- [ ] Файрвол настроен
- [ ] SSL сертификат установлен (если нужен)
- [ ] Права доступа ограничены
- [ ] Секреты защищены

### Резервное копирование:
- [ ] Скрипт бэкапа создан
- [ ] Cron задачи настроены
- [ ] Тестовый бэкап выполнен
- [ ] Восстановление протестировано

---

*После выполнения всех шагов ваш бот будет готов к работе в продакшене с полным мониторингом, аналитикой и системой безопасности!*

