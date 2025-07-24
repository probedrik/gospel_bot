# 🔧 Исправление схемы Supabase v2.8.8

## ❌ Реальная проблема с сохранением прогресса

### **Корень проблемы был в несоответствии схем БД!**

В SQLite используется поле `part_idx`, а в Supabase было `part_index`:

```sql
-- ❌ БЫЛО В SUPABASE:
CREATE TABLE reading_parts_progress (
    ...
    part_index INTEGER NOT NULL,  -- ❌ Неправильно!
    ...
);

-- ✅ СТАЛО В SUPABASE (соответствует SQLite):
CREATE TABLE reading_parts_progress (
    ...
    part_idx INTEGER NOT NULL,    -- ✅ Правильно!
    ...
);
```

### **Из-за этого в Supabase менеджере:**
```python
# ❌ БЫЛО (неправильное поле):
data = {'part_index': part_idx}  # Сохранялось в part_index
result.select('part_index')      # Читалось из part_index

# ✅ СТАЛО (правильное поле):
data = {'part_idx': part_idx}    # Сохраняется в part_idx
result.select('part_idx')        # Читается из part_idx
```

## 🔧 Исправления в v2.8.8

### **1. Исправлен Supabase менеджер**
- ✅ `mark_reading_part_completed()` - теперь сохраняет в `part_idx`
- ✅ `get_reading_part_progress()` - теперь читает из `part_idx`
- ✅ `is_reading_part_completed()` - теперь проверяет по `part_idx`

### **2. Обновлена SQL схема**
- ✅ `supabase_tables.sql` - поле изменено на `part_idx`
- ✅ Создан миграционный скрипт `supabase_migration_part_idx.sql`

### **3. Добавлено поле completed_at**
- ✅ Для Supabase добавлено `DEFAULT CURRENT_TIMESTAMP`
- ✅ Соответствует схеме SQLite

## 🚀 Миграция для существующей Supabase БД

**Если у вас уже есть таблица с `part_index`, выполните:**

1. **Откройте Supabase SQL Editor**
2. **Скопируйте и выполните** содержимое файла `supabase_migration_part_idx.sql`
3. **Проверьте результат** - должно показать поле `part_idx`

```sql
-- Быстрая проверка схемы:
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'reading_parts_progress' 
ORDER BY ordinal_position;
```

## 🎯 Теперь будет работать:

### **Пошаговый сценарий:**
1. **Открываем план чтения** → Видим дни с правильными значками
2. **Заходим в день** → Видим части: `📄 Быт 1`, `📄 Мф 1` 
3. **Читаем и нажимаем "Прочитано"** → Часть становится `✅ Быт 1`
4. **Возвращаемся к дню** → Показывает `📖 День 1: Прочитано: 1 из 2`
5. **Возвращаемся к списку** → Показывает `📖 День 1 (1/2) - Быт 1; Мф 1`

### **Причина исправления:**
- ✅ **Схемы БД унифицированы** - везде используется `part_idx`
- ✅ **Данные сохраняются корректно** во всех типах БД
- ✅ **Прогресс синхронизируется** между экранами

## 🔍 Затронутые файлы

- `database/supabase_manager.py` - исправлены поля `part_index` → `part_idx`
- `supabase_tables.sql` - обновлена схема таблицы
- `supabase_migration_part_idx.sql` - скрипт миграции для существующих БД
- `docker-compose.supabase-sdk.yml` - обновление до v2.8.8

## 🚀 Деплой

```bash
# 1. Обновите схему Supabase (если нужно)
# Выполните supabase_migration_part_idx.sql в Supabase SQL Editor

# 2. Соберите новый образ
.\build-and-push.ps1 -Username "probedrik" -Tag "v2.8.8"

# 3. Обновите контейнер
docker-compose -f docker-compose.supabase-sdk.yml up -d
```

Теперь сохранение прогресса работает корректно во всех типах БД! 🎯 