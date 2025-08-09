# 🚀 НАСТРОЙКА SUPABASE ДЛЯ СИСТЕМЫ ИИ

## 🎯 Обзор

Все новые функции системы ИИ полностью совместимы с Supabase и готовы к работе.

## 📋 Шаги настройки

### 1. 🗄️ Создание таблиц в Supabase

**Выполните SQL скрипт в Supabase SQL Editor:**

Откройте файл `database/supabase_ai_settings_migration.sql` и выполните его в вашем Supabase проекте.

**Что создается:**
- ✅ `ai_settings` - динамические настройки ИИ
- ✅ `premium_requests` - премиум запросы пользователей
- ✅ `premium_purchases` - история покупок
- ✅ `donations` - пожертвования
- ✅ Индексы для оптимизации
- ✅ Триггеры для автоматического обновления `updated_at`
- ✅ Row Level Security (RLS) политики

### 2. ⚙️ Переменные окружения

**Убедитесь, что в `.env` файле установлено:**

```env
# Использование Supabase
USE_SUPABASE=true

# Supabase настройки
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key

# ИИ настройки
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_PREMIUM_API_KEY=your_premium_openrouter_key
OPENROUTER_PREMIUM_MODEL=anthropic/claude-3.5-sonnet

# ЮKassa (для будущих платежей)
YOOKASSA_SHOP_ID=your_shop_id
YOOKASSA_SECRET_KEY=your_secret_key
YOOKASSA_WEBHOOK_SECRET=your_webhook_secret
```

### 3. 🔧 Проверка совместимости

**Все методы реализованы в `SupabaseManager`:**

```python
# Настройки ИИ
await db_manager.get_ai_setting('ai_daily_limit')
await db_manager.set_ai_setting('ai_daily_limit', '5', 'integer')
await db_manager.get_all_ai_settings()

# Премиум запросы
await db_manager.get_user_premium_requests(user_id)
await db_manager.add_premium_requests(user_id, 50)
await db_manager.use_premium_request(user_id)
await db_manager.get_premium_stats(user_id)

# Покупки и пожертвования
await db_manager.create_premium_purchase(user_id, 50, 100, payment_id)
await db_manager.complete_premium_purchase(payment_id)
await db_manager.create_donation(user_id, 100, payment_id, message)
await db_manager.complete_donation(payment_id)
```

## 🔄 Автоматическая инициализация

**При запуске бота:**

1. `UniversalDatabaseManager` автоматически определяет использование Supabase
2. Создается `SupabaseManager` с методами для новых таблиц
3. Все сервисы (`AISettingsManager`, `PremiumManager`) работают через единый API

## 🧪 Тестирование

### Проверка подключения:

```python
# В Python консоли или тестовом скрипте
from database.universal_manager import universal_db_manager

# Проверяем тип менеджера
print(f"Используется Supabase: {universal_db_manager.is_supabase}")

# Тестируем настройки ИИ
settings = await universal_db_manager.get_all_ai_settings()
print(f"Настройки ИИ: {settings}")

# Тестируем премиум запросы
premium_count = await universal_db_manager.get_user_premium_requests(123456789)
print(f"Премиум запросы: {premium_count}")
```

### Проверка через админ панель:

1. Запустите бота: `python bot.py`
2. Отправьте `/admin`
3. Нажмите **⚙️ Настройки ИИ**
4. Проверьте, что отображаются текущие настройки
5. Попробуйте изменить дневной лимит

## 📊 Структура данных в Supabase

### Таблица `ai_settings`:
```sql
id | setting_key | setting_value | setting_type | description | created_at | updated_at
1  | ai_daily_limit | 3 | integer | Дневной лимит... | 2024-01-15 | 2024-01-15
2  | premium_package_price | 100 | integer | Цена премиум... | 2024-01-15 | 2024-01-15
```

### Таблица `premium_requests`:
```sql
id | user_id | requests_count | total_purchased | total_used | created_at | updated_at
1  | 123456789 | 25 | 50 | 25 | 2024-01-15 | 2024-01-15
```

### Таблица `premium_purchases`:
```sql
id | user_id | requests_count | amount_rub | payment_id | payment_status | created_at | completed_at
1  | 123456789 | 50 | 100 | pay_123 | completed | 2024-01-15 | 2024-01-15
```

## 🔒 Безопасность

### Row Level Security (RLS):

Все таблицы защищены RLS политиками:
- Доступ только для service role
- Защита от несанкционированного доступа
- Автоматическое управление правами

### Рекомендации:

1. **Используйте service role key** для бота (не anon key)
2. **Настройте дополнительные политики** при необходимости
3. **Регулярно обновляйте ключи** доступа
4. **Мониторьте использование** через Supabase Dashboard

## 🚀 Готово к работе!

### ✅ Что работает с Supabase:

- ✅ **Динамические настройки ИИ** - изменение через админ панель
- ✅ **Премиум запросы** - покупка, использование, статистика
- ✅ **Бесплатный премиум доступ** - управление списком пользователей
- ✅ **Режим ИИ для админа** - переключение между обычным/премиум
- ✅ **Покупки и пожертвования** - готовность к интеграции с ЮKassa
- ✅ **Автоматические триггеры** - обновление временных меток
- ✅ **Оптимизация** - индексы для быстрых запросов

### 🔄 Fallback для SQLite:

Если по какой-то причине Supabase недоступен, система автоматически переключится на SQLite с теми же функциями.

## 🎯 Система полностью готова для Supabase!

Все новые функции ИИ работают нативно с Supabase через Python SDK без дополнительных настроек.