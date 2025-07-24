#!/usr/bin/env python3
"""
Детальная диагностика подключения к Supabase
"""

import os
import sys
from dotenv import load_dotenv


def test_env_loading():
    """Проверяем загрузку .env файла"""
    print("🔧 Проверка загрузки .env файла...")

    # Проверяем существование .env
    if not os.path.exists('.env'):
        print("❌ Файл .env не найден!")
        return False

    # Загружаем .env
    load_dotenv()

    # Проверяем ключевые переменные
    env_vars = {
        'USE_SUPABASE': os.getenv('USE_SUPABASE'),
        'SUPABASE_URL': os.getenv('SUPABASE_URL'),
        'SUPABASE_KEY': os.getenv('SUPABASE_KEY')
    }

    print(f"📋 Переменные окружения:")
    for key, value in env_vars.items():
        if value:
            if key == 'SUPABASE_KEY':
                # Маскируем ключ
                masked = value[:20] + "..." if len(value) > 20 else value
                print(f"   ✅ {key}: {masked}")
            else:
                print(f"   ✅ {key}: {value}")
        else:
            print(f"   ❌ {key}: НЕ ЗАДАНО")

    # Проверяем обязательные поля
    if not all([env_vars['USE_SUPABASE'] == 'True', env_vars['SUPABASE_URL'], env_vars['SUPABASE_KEY']]):
        print("❌ Некоторые обязательные переменные не заданы!")
        return False

    print("✅ .env файл загружен корректно")
    return True


def test_supabase_import():
    """Проверяем импорт Supabase"""
    print("\n📦 Проверка импорта Supabase...")

    try:
        from supabase import create_client, Client
        print("✅ Supabase SDK импортирован успешно")
        return True
    except ImportError as e:
        print(f"❌ Ошибка импорта Supabase: {e}")
        print("💡 Установите: pip install supabase")
        return False


def test_supabase_connection():
    """Проверяем подключение к Supabase"""
    print("\n🔗 Проверка подключения к Supabase...")

    try:
        from supabase import create_client, Client

        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')

        print(f"📡 Подключаемся к: {url}")
        supabase: Client = create_client(url, key)

        # Тестовый запрос к таблице reading_plans
        print("🔍 Тестируем запрос к таблице reading_plans...")
        response = supabase.table('reading_plans').select(
            '*').limit(1).execute()

        if response.data:
            print(
                f"✅ Подключение успешно! Найдено планов: {len(response.data)}")
            return True, supabase
        else:
            print("⚠️ Подключение есть, но таблица reading_plans пуста")
            return True, supabase

    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False, None


def test_tables_access(supabase):
    """Проверяем доступ к таблицам"""
    print("\n📊 Проверка доступа к таблицам...")

    tables_to_test = ['reading_plans', 'reading_plan_days']

    for table_name in tables_to_test:
        try:
            print(f"🔍 Проверяем таблицу {table_name}...")
            response = supabase.table(table_name).select(
                '*').limit(5).execute()

            if response.data:
                print(
                    f"   ✅ {table_name}: {len(response.data)} записей найдено")

                # Показываем примеры данных
                if table_name == 'reading_plans':
                    for plan in response.data:
                        plan_id = plan.get('plan_id', 'unknown')
                        title = plan.get('title', 'unknown')
                        total_days = plan.get('total_days', 'unknown')
                        print(
                            f"      📋 {plan_id}: {title} ({total_days} дней)")

                elif table_name == 'reading_plan_days':
                    for day in response.data[:3]:
                        plan_id = day.get('plan_id', 'unknown')
                        day_num = day.get('day', 'unknown')
                        reading_text = day.get('reading_text', 'unknown')[:50]
                        print(
                            f"      📖 {plan_id} день {day_num}: {reading_text}...")
            else:
                print(f"   ⚠️ {table_name}: таблица пуста")

        except Exception as e:
            print(f"   ❌ {table_name}: ошибка доступа - {e}")


def test_service_loading():
    """Проверяем загрузку через наш сервис"""
    print("\n🚀 Проверка через SupabaseReadingPlansService...")

    try:
        # Добавляем путь к проекту
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

        # Включаем детальное логирование
        import logging
        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger('services.supabase_reading_plans')
        logger.setLevel(logging.DEBUG)

        from services.supabase_reading_plans import SupabaseReadingPlansService

        print("📦 Создаем экземпляр сервиса...")
        service = SupabaseReadingPlansService()

        print(f"🔧 Статус db_manager: {service.db_manager}")
        print(f"🔧 Планы уже загружены: {service._plans_loaded}")
        print(f"🔧 Количество планов в памяти: {len(service.plans)}")

        print("📋 Загружаем планы через СИНХРОННЫЙ метод...")

        # Пытаемся загрузить с подробным логированием
        plans = service.get_all_plans_sync()

        print(f"🔧 После загрузки:")
        print(f"   - db_manager: {service.db_manager}")
        print(f"   - планы загружены: {service._plans_loaded}")
        print(f"   - планов в памяти: {len(service.plans)}")
        print(f"   - возвращено планов: {len(plans) if plans else 0}")

        if plans:
            print(f"✅ Через сервис загружено {len(plans)} планов:")
            for plan in plans:
                title = plan.get('title', 'Неизвестный план')
                total_days = plan.get('total_days', 'неизвестно')
                plan_id = plan.get('plan_id', 'неизвестный')
                print(f"   📋 {plan_id}: {title} ({total_days} дней)")

            # Тестируем также получение дней плана
            if plans:
                first_plan_id = plans[0].get('plan_id')
                print(f"\n📅 Тестируем дни плана {first_plan_id}...")
                days = service.get_plan_days_sync(first_plan_id)
                if days:
                    print(
                        f"✅ Найдено {len(days)} дней для плана {first_plan_id}")
                    # Показываем первые 3 дня
                    for day in days[:3]:
                        day_num = day.get('day', 'неизвестно')
                        reading = day.get('reading_text', 'неизвестно')[:50]
                        print(f"      📖 День {day_num}: {reading}...")
                else:
                    print(f"❌ Дни для плана {first_plan_id} не найдены")
            return True
        else:
            print("❌ Сервис не смог загрузить планы")

            # Пытаемся создать db_manager вручную для диагностики
            print("\n🔧 Пытаемся создать db_manager вручную...")
            try:
                from database.universal_manager import universal_db_manager
                print(
                    f"✅ universal_db_manager импортирован: {universal_db_manager}")

                # Тестируем методы db_manager
                if hasattr(universal_db_manager, 'get_reading_plans'):
                    print("✅ Метод get_reading_plans найден")
                else:
                    print("❌ Метод get_reading_plans НЕ найден")

                if hasattr(universal_db_manager, 'get_reading_plan_days'):
                    print("✅ Метод get_reading_plan_days найден")
                else:
                    print("❌ Метод get_reading_plan_days НЕ найден")

            except ImportError as e:
                print(f"❌ Не удалось импортировать universal_db_manager: {e}")

            return False

    except Exception as e:
        print(f"❌ Ошибка тестирования сервиса: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Основная функция диагностики"""
    print("🔧 ДЕТАЛЬНАЯ ДИАГНОСТИКА ПОДКЛЮЧЕНИЯ К SUPABASE")
    print("=" * 60)

    # Шаг 1: Проверка .env
    if not test_env_loading():
        print("\n❌ Диагностика прервана из-за проблем с .env файлом")
        return

    # Шаг 2: Проверка импорта
    if not test_supabase_import():
        print("\n❌ Диагностика прервана из-за проблем с импортом")
        return

    # Шаг 3: Проверка подключения
    connection_ok, supabase = test_supabase_connection()
    if not connection_ok:
        print("\n❌ Диагностика прервана из-за проблем с подключением")
        return

    # Шаг 4: Проверка таблиц
    test_tables_access(supabase)

    # Шаг 5: Проверка через сервис
    test_service_loading()

    print("\n🎯 ДИАГНОСТИКА ЗАВЕРШЕНА")
    print("=" * 60)


if __name__ == "__main__":
    main()
