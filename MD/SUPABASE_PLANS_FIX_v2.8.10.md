# 🔧 Исправление загрузки планов из Supabase v2.8.10

## ❌ Проблема
Несмотря на переключение с помощью скрипта `switch_to_supabase_plans.py`, планы чтения все еще загружались из CSV файлов, что приводило к ошибкам:

```
ERROR:services.reading_plans:Папка с планами не найдена: data/plans_csv_final
INFO:services.reading_plans:💡 Попробуйте переключиться на планы из Supabase:
INFO:services.reading_plans:   python switch_to_supabase_plans.py
```

## 🔍 Корень проблемы
Универсальный сервис планов чтения (`services/universal_reading_plans.py`) не проверял конфигурационный файл `data/supabase_plans.conf` и продолжал искать CSV файлы.

## ✅ Исправления в v2.8.10

### **1. Исправлена логика загрузки планов**
```python
# БЫЛО (неправильная последовательность):
def _load_plans(self):
    # Сначала CSV
    if self._load_from_csv():
        return
    # Потом резервная копия
    # Потом заглушки

# СТАЛО (правильная последовательность):  
def _load_plans(self):
    # Сначала проверяем конфигурацию Supabase
    if "USE_SUPABASE_PLANS=true" in config:
        if self._load_from_supabase():
            return
    # Потом CSV, резервная копия, Supabase fallback, заглушки
```

### **2. Добавлен метод `_load_from_supabase()`**
- ✅ Импортирует `SupabaseReadingPlansService`
- ✅ Загружает планы из Supabase
- ✅ Конвертирует в формат `ReadingPlan`

### **3. Добавлены синхронные методы в `SupabaseReadingPlansService`**
- ✅ `get_all_plans()` - получение всех планов
- ✅ `get_plan_days(plan_id)` - получение дней плана
- ✅ Совместимость с универсальным сервисом

### **4. Создан улучшенный скрипт переключения**
`force_switch_to_supabase_plans.py`:
- ✅ Обновляет конфигурацию
- ✅ Отключает CSV планы  
- ✅ Тестирует доступность Supabase планов
- ✅ Проверяет работу универсального сервиса

## 🚀 Как использовать

### **Вариант 1: Локальное переключение**
```bash
python force_switch_to_supabase_plans.py
```

### **Вариант 2: Ручное переключение**
1. **Создайте конфигурационный файл** `data/supabase_plans.conf`:
```ini
USE_SUPABASE_PLANS=true
CSV_PLANS_DISABLED=true
```

2. **Отключите CSV планы:**
```bash
mv data/plans_csv_final data/plans_csv_final_disabled
```

3. **Пересоберите и запустите:**
```bash
.\build-and-push.ps1 -Username "probedrik" -Tag "v2.8.10"
docker-compose -f docker-compose.supabase-sdk.yml up -d
```

## 🔍 Проверка работы

### **В логах бота должно быть:**
```
INFO:services.universal_reading_plans:🔄 Конфигурация указывает использовать Supabase планы
INFO:services.universal_reading_plans:✅ Планы загружены из Supabase
```

### **Вместо ошибок:**
```
ERROR:services.reading_plans:Папка с планами не найдена: data/plans_csv_final
```

## 🎯 Результат

### **✅ Что теперь работает:**
- Планы загружаются из Supabase при наличии конфигурации
- Универсальный сервис правильно переключается между источниками
- CSV планы используются только как fallback
- Прогресс планов сохраняется в Supabase (исправлено в v2.8.8)

### **📊 Последовательность загрузки планов:**
1. **Конфигурация Supabase** (`data/supabase_plans.conf`)
2. **CSV планы** (`data/plans_csv_final`)
3. **Резервная копия** (`data/plans_csv_backup`)
4. **Supabase fallback** (если доступен)
5. **Заглушки** (минимальные планы)

## 🔧 Отладка

Если планы все еще не загружаются из Supabase:

### **1. Проверьте конфигурацию:**
```bash
cat data/supabase_plans.conf
# Должно содержать: USE_SUPABASE_PLANS=true
```

### **2. Проверьте переменные окружения:**
```bash
# В .env файле:
USE_SUPABASE=true
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-key
```

### **3. Проверьте таблицы в Supabase:**
```sql
-- В Supabase SQL Editor:
SELECT COUNT(*) FROM reading_plans;
SELECT COUNT(*) FROM reading_plan_days;
```

### **4. Запустите тест:**
```bash
python force_switch_to_supabase_plans.py
```

## 📝 Затронутые файлы
- `services/universal_reading_plans.py` - исправлена логика загрузки
- `services/supabase_reading_plans.py` - добавлены синхронные методы
- `force_switch_to_supabase_plans.py` - новый скрипт переключения
- `docker-compose.supabase-sdk.yml` - обновление до v2.8.10

Теперь планы корректно загружаются из Supabase! 🎯 