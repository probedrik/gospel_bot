# Исправления планов чтения и навигации v2.8.4

## Описание проблем

### 1. Ошибка при открытии главы из плана чтения
**Проблема**: При нажатии на главу из плана чтения возникала ошибка:
```
AttributeError: 'UniversalDatabaseManager' object has no attribute 'is_reading_part_completed'
```

**Причина**: В UniversalDatabaseManager отсутствовал метод `is_reading_part_completed`, который необходим для отображения статуса прочитанных частей плана.

### 2. Планы чтения загружаются из CSV вместо Supabase
**Проблема**: Несмотря на миграцию в Supabase, планы чтения все еще загружались из CSV файлов.

**Причина**: Служба `ReadingPlansService` по умолчанию использует CSV файлы. Нужен альтернативный сервис для Supabase.

### 3. Инициализация базы данных
**Проблема**: Ошибки инициализации БД в логах:
```
ERROR:__main__:❌ Критическая ошибка при инициализации БД: expected str, bytes or os.PathLike object, not NoneType
```

## Исправления

### 1. Добавление метода `is_reading_part_completed`

**Файлы**: 
- `database/universal_manager.py`
- `database/supabase_manager.py` 
- `database/postgres_manager.py`
- `database/db_manager.py`

Добавлен метод `is_reading_part_completed` во все менеджеры баз данных:

```python
# В UniversalDatabaseManager
async def is_reading_part_completed(self, user_id: int, plan_id: str, day: int, part_idx: int):
    """Проверяет, отмечена ли часть дня как прочитанная"""
    return await self.manager.is_reading_part_completed(user_id, plan_id, day, part_idx)

# В SupabaseManager  
async def is_reading_part_completed(self, user_id: int, plan_id: str, day: int, part_idx: int) -> bool:
    """Проверяет, отмечена ли часть дня как прочитанная"""
    try:
        result = self.client.table('reading_parts_progress').select('user_id').eq(
            'user_id', user_id).eq('plan_id', plan_id).eq('day', day).eq('part_index', part_idx).execute()
        return len(result.data) > 0
    except Exception as e:
        logger.error(f"Ошибка проверки завершения части дня для пользователя {user_id}: {e}")
        return False

# В PostgreSQLManager
async def is_reading_part_completed(self, user_id: int, plan_id: str, day: int, part_idx: int) -> bool:
    """Проверяет, отмечена ли часть дня как прочитанная"""
    try:
        query = """
            SELECT completed FROM reading_parts_progress 
            WHERE user_id = $1 AND plan_id = $2 AND day_number = $3 AND part_index = $4
        """
        result = await self.pool.fetchval(query, user_id, plan_id, day, part_idx)
        return result is True
    except Exception as e:
        logger.error(f"Ошибка проверки завершения части дня: {e}")
        return False

# В SQLite DatabaseManager (асинхронная обертка)
async def is_reading_part_completed(self, user_id: int, plan_id: str, day: int, part_idx: int) -> bool:
    """Асинхронный метод для проверки завершения части дня"""
    return self._is_reading_part_completed_sync(user_id, plan_id, day, part_idx)
```

### 2. Новый сервис планов чтения из Supabase

**Файл**: `services/supabase_reading_plans.py`

Создан новый сервис `SupabaseReadingPlansService` для загрузки планов из Supabase:

```python
class SupabaseReadingPlansService:
    """Служба для работы с планами чтения из Supabase"""

    async def _load_plans(self) -> None:
        """Загружает все планы из Supabase"""
        plans_data = await self.db_manager.get_reading_plans()
        for plan_data in plans_data:
            plan_id = plan_data.get('plan_id')
            title = plan_data.get('title')
            days_data = await self.db_manager.get_reading_plan_days(plan_id)
            # ... обработка и создание ReadingPlan объектов
```

### 3. Скрипт переключения на Supabase планы

**Файл**: `switch_to_supabase_plans.py`

Создан скрипт для безопасного переключения с CSV на Supabase планы:

- Создает резервную копию CSV файлов
- Переименовывает папку `data/plans_csv_final` в `data/plans_csv_final_disabled`
- Создает конфигурационный файл для индикации использования Supabase
- Предоставляет инструкции по восстановлению

```bash
# Запуск скрипта
python switch_to_supabase_plans.py
```

## Развертывание

### Обновление Docker образа
Образ `probedrik/gospel-bot:v2.8.4` опубликован на Docker Hub.

### Обновление docker-compose.supabase-sdk.yml
```yaml
services:
  bible-bot:
    image: probedrik/gospel-bot:v2.8.4  # Обновлено с v2.8.3
```

### Команды для применения исправлений

```bash
# Остановить текущий контейнер
docker-compose -f docker-compose.supabase-sdk.yml down

# Загрузить новый образ
docker pull probedrik/gospel-bot:v2.8.4

# (Опционально) Переключиться на Supabase планы
python switch_to_supabase_plans.py

# Запустить обновленный контейнер
docker-compose -f docker-compose.supabase-sdk.yml up -d

# Проверить логи
docker-compose -f docker-compose.supabase-sdk.yml logs -f
```

## Переключение на планы из Supabase

### Автоматическое переключение
```bash
python switch_to_supabase_plans.py
```

### Ручное переключение
1. Создать резервную копию:
   ```bash
   cp -r data/plans_csv_final data/plans_csv_backup
   ```

2. Отключить CSV планы:
   ```bash
   mv data/plans_csv_final data/plans_csv_final_disabled
   ```

3. Перезапустить бота

### Восстановление CSV планов
Если нужно вернуться к CSV планам:
```bash
mv data/plans_csv_final_disabled data/plans_csv_final
rm data/supabase_plans.conf
docker-compose -f docker-compose.supabase-sdk.yml restart
```

## Результат

✅ **Планы чтения работают корректно** - исправлена ошибка с отсутствующим методом `is_reading_part_completed`

✅ **Поддержка планов из Supabase** - создан альтернативный сервис для загрузки планов из базы данных

✅ **Безопасное переключение** - скрипт для миграции с CSV на Supabase с возможностью отката

✅ **Полная совместимость** - поддержка как CSV, так и Supabase планов чтения

## Тестирование

После обновления рекомендуется протестировать:

1. **Планы чтения**: открыть любой план и убедиться, что нет ошибок при открытии глав
2. **Навигация в планах**: переходы между днями, отметка прочитанных частей
3. **Загрузка планов**: проверить источник планов (CSV или Supabase) в логах
4. **Переключение источника**: протестировать скрипт `switch_to_supabase_plans.py`

## Логи для диагностики

### Планы из CSV
```
INFO:services.reading_plans:Загружен план 'Евангелие на каждый день – план чтения' с 45 днями из файла Евангелие-на-каждый-день.csv
```

### Планы из Supabase
```
INFO:services.supabase_reading_plans:Получено 3 планов из Supabase
INFO:services.supabase_reading_plans:Загружен план из Supabase: Евангелие на каждый день (45 дней)
```

## Версия

**v2.8.4** - 30 декабря 2024
- Исправлена ошибка отсутствующего метода `is_reading_part_completed`
- Добавлен сервис планов чтения из Supabase
- Создан скрипт безопасного переключения с CSV на Supabase
- Улучшена совместимость и стабильность планов чтения 