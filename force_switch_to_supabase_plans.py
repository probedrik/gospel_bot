#!/usr/bin/env python3
"""
Скрипт для принудительного переключения на планы чтения из Supabase.
Обновляет конфигурацию и проверяет доступность планов.
"""

import os
import sys
import asyncio
from pathlib import Path


def update_supabase_config():
    """Обновляет конфигурационный файл для использования Supabase планов"""
    config_file = "data/supabase_plans.conf"

    # Создаем директорию если нужно
    os.makedirs("data", exist_ok=True)

    config_content = """# Конфигурация планов чтения из Supabase

# Этот файл указывает боту использовать планы чтения из Supabase
# вместо CSV файлов

USE_SUPABASE_PLANS=true
CSV_PLANS_DISABLED=true

# Если нужно вернуться к CSV планам:
# 1. Переименуйте папку data/plans_csv_final_disabled обратно в data/plans_csv_final
# 2. Удалите этот файл или установите USE_SUPABASE_PLANS=false

"""

    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(config_content)

    print(f"✅ Создан конфигурационный файл: {config_file}")


def disable_csv_plans():
    """Отключает CSV планы если они есть"""
    csv_dir = "data/plans_csv_final"
    disabled_dir = "data/plans_csv_final_disabled"

    if os.path.exists(csv_dir) and not os.path.exists(disabled_dir):
        os.rename(csv_dir, disabled_dir)
        print(f"✅ CSV планы отключены: {csv_dir} → {disabled_dir}")
    else:
        print(f"ℹ️ CSV планы уже отключены или не существуют")


async def test_supabase_plans():
    """Тестирует доступность планов из Supabase"""
    try:
        print("🔄 Тестируем доступность планов из Supabase...")

        # Загружаем переменные окружения
        from dotenv import load_dotenv
        load_dotenv()

        # Проверяем тип БД
        from database.universal_manager import universal_db_manager

        if universal_db_manager.is_supabase:
            print("📊 Используется БД: Supabase")
        elif universal_db_manager.is_postgres:
            print("📊 Используется БД: PostgreSQL")
        else:
            print("📊 Используется БД: SQLite")

        # Инициализируем БД менеджер
        await universal_db_manager.initialize()

        # Создаем сервис с правильным db_manager
        from services.supabase_reading_plans import SupabaseReadingPlansService
        service = SupabaseReadingPlansService(universal_db_manager)

        # Используем АСИНХРОННЫЙ метод
        plans = await service.get_all_plans()

        if plans:
            print(f"✅ Найдено {len(plans)} планов в Supabase:")
            for plan in plans:
                print(
                    f"   📋 {plan.plan_id}: {plan.title} ({plan.total_days} дней)")
            return True
        else:
            print("❌ Планы в Supabase не найдены")
            return False

    except Exception as e:
        print(f"❌ Ошибка при тестировании Supabase планов: {e}")
        import traceback
        print(f"Трассировка: {traceback.format_exc()}")
        return False


async def test_universal_service():
    """Тестирует универсальный сервис планов"""
    try:
        print("🔄 Тестируем универсальный сервис планов...")

        # Загружаем переменные окружения
        from dotenv import load_dotenv
        load_dotenv()

        # Инициализируем универсальный сервис
        from services.universal_reading_plans import universal_reading_plans_service

        # Попробуем инициализировать заново если нужно
        if not hasattr(universal_reading_plans_service, 'plans') or not universal_reading_plans_service.plans:
            print("🔄 Повторная инициализация универсального сервиса...")
            universal_reading_plans_service._load_plans()

        plans = universal_reading_plans_service.get_all_plans()

        if plans:
            print(f"✅ Универсальный сервис загрузил {len(plans)} планов:")
            for plan in plans[:3]:
                # Проверяем, это dict или ReadingPlan объект
                if hasattr(plan, 'title'):
                    # Это ReadingPlan объект
                    title = plan.title
                    days = plan.total_days
                    plan_id = plan.plan_id
                    print(f"   📋 {plan_id}: {title} ({days} дней)")
                elif isinstance(plan, dict):
                    # Это словарь
                    title = plan.get('title', 'Неизвестный план')
                    days = plan.get('total_days', 'неизвестно')
                    plan_id = plan.get('plan_id', 'неизвестный')
                    print(f"   📋 {plan_id}: {title} ({days} дней)")
                else:
                    # Неизвестный тип
                    print(f"   📋 {str(plan)}")

            if len(plans) > 3:
                print(f"   ... и еще {len(plans) - 3} планов")
            return True
        else:
            print("❌ Универсальный сервис не смог загрузить планы")
            return False

    except Exception as e:
        print(f"❌ Ошибка тестирования универсального сервиса: {e}")
        import traceback
        print(f"Трассировка: {traceback.format_exc()}")
        return False


async def main():
    """Основная функция"""
    print("🔧 Принудительное переключение на планы Supabase")
    print("=" * 60)

    # Шаг 1: Создание конфигурации
    update_supabase_config()

    # Шаг 2: Отключение CSV планов
    disable_csv_plans()

    # Шаг 3: Тестирование
    print("\n📊 Тестирование доступности планов...")

    # Тестируем Supabase планы
    supabase_ok = await test_supabase_plans()

    # Тестируем универсальный сервис
    universal_ok = await test_universal_service()

    # Результат
    print(f"\n🎯 Результат:")
    if supabase_ok:
        print("✅ Планы в Supabase доступны")
        print("✅ Переключение на Supabase планы завершено успешно!")
        print("\n📋 Следующие шаги:")
        print("1. Соберите новый образ: .\\build-and-push.ps1 -Username \"probedrik\" -Tag \"v2.8.12\"")
        print(
            "2. Обновите контейнер: docker-compose -f docker-compose.supabase-sdk.yml up -d")
        print("3. Проверьте логи: docker logs -f bible-bot-supabase")
    else:
        print("❌ Планы в Supabase недоступны")
        print("Убедитесь, что:")
        print("1. USE_SUPABASE=true в .env файле")
        print("2. Правильные параметры Supabase в .env")
        print("3. Таблицы reading_plans и reading_plan_days созданы")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
