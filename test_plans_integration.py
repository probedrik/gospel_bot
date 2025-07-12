#!/usr/bin/env python3
"""
Тест интеграции планов чтения с новыми функциями.
"""

from utils.reference_parser import parse_reference, parse_multiple_references
from services.reading_plans import reading_plans_service
import asyncio
import sys
import os

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_reading_plans():
    """Тестирует загрузку планов чтения."""
    print("🔍 Тестирование планов чтения...")

    # Получаем все планы
    plans = reading_plans_service.get_all_plans()
    print(f"📋 Найдено планов: {len(plans)}")

    for plan in plans:
        print(f"  - {plan.plan_id}: {plan.title} ({plan.total_days} дней)")

        # Тестируем первый день каждого плана
        day_1 = reading_plans_service.get_plan_day(plan.plan_id, 1)
        if day_1:
            print(f"    День 1: {day_1}")

            # Парсим ссылки
            references = reading_plans_service.parse_reading_references(day_1)
            print(f"    Ссылок в дне 1: {len(references)}")
            for i, ref in enumerate(references[:3]):  # Показываем первые 3
                print(f"      {i+1}. {ref}")
        print()


def test_reference_parser():
    """Тестирует парсер ссылок."""
    print("🔍 Тестирование парсера ссылок...")

    test_refs = [
        "Мф 1",
        "Мф 1:1",
        "Мф 1:1-5",
        "Лк 5:27-39",
        "Быт 1:1-2:25",
        "Пс 1",
        "Первая Царств 1:1-2:25"
    ]

    for ref in test_refs:
        parsed = parse_reference(ref)
        print(f"  {ref} -> {parsed}")

    print("\n🔍 Тестирование множественных ссылок...")
    multi_ref = "Мф 1; Мф 2; Лк 1:1-25"
    parsed_multi = parse_multiple_references(multi_ref)
    print(f"  {multi_ref} -> {len(parsed_multi)} ссылок")
    for i, ref in enumerate(parsed_multi):
        print(f"    {i+1}. {ref}")


async def test_database_methods():
    """Тестирует новые методы базы данных."""
    print("🔍 Тестирование методов базы данных...")

    from database.db_manager import db_manager

    # Тестовые данные
    test_user_id = 12345
    test_book_id = 1  # Предполагаем, что это Матфей
    test_chapter = 1
    test_verse_start = 1
    test_verse_end = 5

    try:
        # Проверяем существование закладки
        exists_before = await db_manager.is_bookmark_exists_detailed(
            test_user_id, test_book_id, test_chapter, test_verse_start, test_verse_end
        )
        print(f"  Закладка существует до добавления: {exists_before}")

        # Добавляем закладку
        added = await db_manager.add_bookmark_detailed(
            test_user_id, test_book_id, test_chapter,
            test_verse_start, test_verse_end, "Тестовая закладка"
        )
        print(f"  Закладка добавлена: {added}")

        # Проверяем существование после добавления
        exists_after = await db_manager.is_bookmark_exists_detailed(
            test_user_id, test_book_id, test_chapter, test_verse_start, test_verse_end
        )
        print(f"  Закладка существует после добавления: {exists_after}")

        # Удаляем закладку
        removed = await db_manager.remove_bookmark_detailed(
            test_user_id, test_book_id, test_chapter, test_verse_start, test_verse_end
        )
        print(f"  Закладка удалена: {removed}")

        # Проверяем существование после удаления
        exists_final = await db_manager.is_bookmark_exists_detailed(
            test_user_id, test_book_id, test_chapter, test_verse_start, test_verse_end
        )
        print(f"  Закладка существует после удаления: {exists_final}")

    except Exception as e:
        print(f"  ❌ Ошибка при тестировании БД: {e}")


def main():
    """Основная функция тестирования."""
    print("🚀 Тестирование интеграции планов чтения\n")

    # Тест планов чтения
    test_reading_plans()

    # Тест парсера ссылок
    test_reference_parser()

    # Тест методов базы данных
    print("\n🔍 Запуск асинхронных тестов...")
    asyncio.run(test_database_methods())

    print("\n✅ Тестирование завершено!")


if __name__ == "__main__":
    main()
