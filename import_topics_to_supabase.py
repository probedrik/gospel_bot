#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для импорта библейских тем в Supabase
Использует исправленный CSV файл с темами
"""

import csv
import asyncio
import os
from pathlib import Path
from supabase import create_client, Client


async def import_topics_to_supabase():
    """Импортирует темы в Supabase"""

    # Настройки Supabase
    url = "https://fqmmqmojvafquunkovmv.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZxbW1xbW9qdmFmcXV1bmtvdm12Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTMwOTQzNDYsImV4cCI6MjA2ODY3MDM0Nn0.vOiHdmk9hFKEo5J-m-V3O1qtEB7qUZCE7RnykIXefWs"

    if not url or not key:
        print(
            "❌ Ошибка: SUPABASE_URL и SUPABASE_ANON_KEY должны быть в переменных окружения")
        print("Проверьте файл .env")
        return False

    try:
        # Подключаемся к Supabase
        supabase: Client = create_client(url, key)
        print("✅ Подключение к Supabase успешно")

        # Проверяем файл с исправленными темами
        input_file = "bible_verses_by_topic_fixed.csv"
        if not Path(input_file).exists():
            print(f"❌ Файл {input_file} не найден!")
            print("Сначала запустите fix_bible_names_topics.py")
            return False

        # Очищаем существующие данные (опционально)
        print("🧹 Очищаем существующие темы...")
        try:
            supabase.table('bible_topics').delete().neq('id', 0).execute()
            print("✅ Существующие темы удалены")
        except Exception as e:
            print(f"ℹ️ Предупреждение при очистке: {e}")

        # Читаем и импортируем темы
        topics_imported = 0
        topics_failed = 0

        with open(input_file, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)

            # Пропускаем заголовок
            header = next(reader, None)
            if header:
                print(f"📋 Заголовок: {header}")

            for row_num, row in enumerate(reader, start=2):
                if len(row) >= 2:
                    topic_name = row[0].strip()
                    verses = row[1].strip()

                    if topic_name and verses:
                        try:
                            # Вставляем тему в Supabase
                            data = {
                                'topic_name': topic_name,
                                'verses': verses
                            }

                            result = supabase.table(
                                'bible_topics').insert(data).execute()

                            if result.data:
                                topics_imported += 1
                                print(
                                    f"✅ Строка {row_num}: '{topic_name}' - импортирована")
                            else:
                                topics_failed += 1
                                print(
                                    f"❌ Строка {row_num}: '{topic_name}' - ошибка импорта")

                        except Exception as e:
                            topics_failed += 1
                            print(
                                f"❌ Строка {row_num}: '{topic_name}' - ошибка: {e}")
                    else:
                        print(f"⚠️ Строка {row_num}: пустые данные, пропущена")
                else:
                    print(
                        f"⚠️ Строка {row_num}: неправильный формат, пропущена")

        print(f"\n📊 РЕЗУЛЬТАТ ИМПОРТА:")
        print(f"✅ Успешно импортировано: {topics_imported}")
        print(f"❌ Ошибок: {topics_failed}")
        print(f"📝 Всего обработано: {topics_imported + topics_failed}")

        # Проверяем результат
        if topics_imported > 0:
            try:
                count_result = supabase.table('bible_topics').select(
                    'id', count='exact').execute()
                total_count = count_result.count
                print(f"🗃️ Всего тем в базе: {total_count}")

                # Показываем первые несколько тем для проверки
                sample_result = supabase.table('bible_topics').select(
                    'topic_name').limit(5).execute()
                if sample_result.data:
                    print(f"\n📋 Примеры импортированных тем:")
                    for topic in sample_result.data:
                        print(f"   • {topic['topic_name']}")

            except Exception as e:
                print(f"⚠️ Ошибка при проверке результата: {e}")

        return topics_imported > 0

    except Exception as e:
        print(f"❌ Ошибка подключения к Supabase: {e}")
        return False


def main():
    """Основная функция"""
    print("🚀 Импорт библейских тем в Supabase")
    print("=" * 50)

    success = asyncio.run(import_topics_to_supabase())

    if success:
        print("\n🎉 Импорт завершен успешно!")
        print("Теперь темы доступны в Supabase")
    else:
        print("\n💥 Импорт завершился с ошибками")


if __name__ == "__main__":
    main()
