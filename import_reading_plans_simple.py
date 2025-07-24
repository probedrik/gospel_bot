#!/usr/bin/env python3
"""
Упрощенный скрипт для импорта планов чтения Библии из CSV файлов в Supabase.
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Планы с сокращенными названиями
PLANS = [
    {
        "file": "data/plans_csv_final/Евангелие-на-каждый-день.csv",
        "id": "gospel-daily",
        "title": "📖 Евангелие на каждый день",
        "description": "Ежедневное чтение Евангелия"
    },
    {
        "file": "data/plans_csv_final/Классический-план-чтения-Библии-за-1-год.csv",
        "id": "classic-1-year",
        "title": "📚 Классический план за год",
        "description": "Чтение всей Библии за один год"
    },
    {
        "file": "data/plans_csv_final/План-чтения-Библии-ВЗ-и-НЗ.csv",
        "id": "ot-nt-plan",
        "title": "⚖️ План ВЗ и НЗ",
        "description": "Параллельное чтение Ветхого и Нового Завета"
    }
]


async def import_plans():
    """Импортирует планы чтения в Supabase"""

    print("🔄 Импорт планов чтения в Supabase...")

    try:
        # Создаем менеджер
        from database.supabase_manager import SupabaseManager
        manager = SupabaseManager()
        await manager.initialize()
        print("✅ Подключение к Supabase установлено")

        for plan in PLANS:
            print(f"\n📚 Импорт: {plan['title']}")

            # Читаем файл
            if not os.path.exists(plan['file']):
                print(f"❌ Файл {plan['file']} не найден")
                continue

            days_data = []
            with open(plan['file'], 'r', encoding='utf-8') as f:
                lines = f.readlines()

                # Обрабатываем строки начиная с 3-й (пропускаем заголовки)
                for i, line in enumerate(lines[2:], start=1):
                    line = line.strip()
                    if not line:
                        continue

                    # Простое разделение по первой запятой
                    parts = line.split(',', 1)
                    if len(parts) == 2:
                        try:
                            day = int(parts[0])
                            reading = parts[1].strip()
                            if reading:
                                days_data.append({
                                    'plan_id': plan['id'],
                                    'day': day,
                                    'reading_text': reading
                                })
                        except ValueError:
                            continue

            if not days_data:
                print(f"⚠️ Нет данных в файле {plan['file']}")
                continue

            print(f"📅 Найдено дней: {len(days_data)}")

            # 1. Создаем план
            plan_data = {
                'plan_id': plan['id'],
                'title': plan['title'],
                'description': plan['description'],
                'total_days': len(days_data)
            }

            try:
                result = manager.client.table(
                    'reading_plans').upsert(plan_data).execute()
                print(f"✅ План создан/обновлен")
            except Exception as e:
                print(f"❌ Ошибка создания плана: {e}")
                continue

            # 2. Удаляем старые дни
            try:
                manager.client.table('reading_plan_days').delete().eq(
                    'plan_id', plan['id']).execute()
                print(f"🧹 Старые дни удалены")
            except Exception as e:
                print(f"⚠️ Ошибка удаления: {e}")

            # 3. Добавляем дни батчами
            batch_size = 100
            for i in range(0, len(days_data), batch_size):
                batch = days_data[i:i + batch_size]
                try:
                    result = manager.client.table(
                        'reading_plan_days').insert(batch).execute()
                    print(f"✅ Добавлено дней: {len(batch)}")
                except Exception as e:
                    print(f"❌ Ошибка добавления дней: {e}")

            print(f"🎉 План '{plan['title']}' импортирован!")

        # Показываем итоги
        print(f"\n📊 Итоги:")
        plans_result = manager.client.table('reading_plans').select(
            'plan_id, title, total_days').execute()
        for plan in plans_result.data:
            print(f"  📚 {plan['title']}: {plan['total_days']} дней")

        await manager.close()
        return True

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def main():
    print("=== ИМПОРТ ПЛАНОВ ЧТЕНИЯ В SUPABASE ===\n")

    print("📋 Будут импортированы планы:")
    for i, plan in enumerate(PLANS, 1):
        print(f"{i}. {plan['title']} (ID: {plan['id']})")

    print("\n💡 Чтобы изменить названия планов, отредактируйте список PLANS в этом файле")

    response = input("\n❓ Продолжить импорт? (y/n): ").lower()
    if response not in ['y', 'yes', 'да', 'д']:
        print("❌ Импорт отменен")
        return

    success = asyncio.run(import_plans())

    if success:
        print("\n🎉 Импорт завершен успешно!")
    else:
        print("\n❌ Импорт завершен с ошибками!")


if __name__ == "__main__":
    main()
