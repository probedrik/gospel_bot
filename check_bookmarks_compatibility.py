#!/usr/bin/env python3
"""
Скрипт для проверки совместимости данных закладок после миграции
"""
import asyncio
import sys
import os

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.universal_manager import universal_db_manager as db_manager


async def check_bookmarks_structure():
    """Проверяет структуру закладок и совместимость данных"""
    
    print("🔍 Проверка структуры закладок...")
    print("=" * 50)
    
    try:
        # Получаем тестовые закладки (если есть)
        test_user_id = 123456789  # Тестовый ID
        bookmarks = await db_manager.get_bookmarks(test_user_id)
        
        print(f"📊 Найдено закладок для тестового пользователя: {len(bookmarks)}")
        
        if bookmarks:
            print("\\n📋 Структура первой закладки:")
            first_bookmark = bookmarks[0]
            
            if isinstance(first_bookmark, dict):
                # Supabase/PostgreSQL формат
                print("✅ Формат: словарь (Supabase/PostgreSQL)")
                for key, value in first_bookmark.items():
                    print(f"   {key}: {value}")
                    
                # Проверяем наличие новых полей
                required_fields = ['chapter_start', 'chapter_end', 'verse_start', 'verse_end']
                missing_fields = [field for field in required_fields if field not in first_bookmark]
                
                if missing_fields:
                    print(f"\\n⚠️  ВНИМАНИЕ: Отсутствуют поля: {missing_fields}")
                    print("   Необходимо выполнить миграцию базы данных!")
                else:
                    print("\\n✅ Все необходимые поля присутствуют")
                    
            elif isinstance(first_bookmark, (list, tuple)):
                # SQLite формат
                print("✅ Формат: кортеж/список (SQLite)")
                print(f"   Количество полей: {len(first_bookmark)}")
                print(f"   Данные: {first_bookmark}")
                
                if len(first_bookmark) >= 8:
                    print("✅ Структура соответствует новому формату")
                else:
                    print("⚠️  Структура соответствует старому формату")
            
        else:
            print("ℹ️  Закладки не найдены (это нормально для нового пользователя)")
            
        # Тестируем добавление закладки с новой структурой
        print("\\n🧪 Тестирование добавления закладки...")
        
        success = await db_manager.add_bookmark(
            user_id=test_user_id,
            book_id=1,  # Бытие
            chapter_start=1,
            chapter_end=3,  # Диапазон глав 1-3
            verse_start=None,
            verse_end=None,
            display_text="Быт 1-3",
            note="Тестовая закладка"
        )
        
        if success:
            print("✅ Добавление закладки с новой структурой работает")
            
            # Проверяем, что закладка добавилась
            updated_bookmarks = await db_manager.get_bookmarks(test_user_id)
            print(f"📊 Закладок после добавления: {len(updated_bookmarks)}")
            
            # Удаляем тестовую закладку
            await db_manager.remove_bookmark(
                test_user_id, 1, 1, 3, None, None
            )
            print("🗑️  Тестовая закладка удалена")
            
        else:
            print("❌ Ошибка при добавлении закладки с новой структурой")
            
    except Exception as e:
        print(f"❌ Ошибка при проверке: {e}")
        import traceback
        traceback.print_exc()
    
    print("\\n" + "=" * 50)
    print("🏁 Проверка завершена")


async def main():
    """Главная функция"""
    await check_bookmarks_structure()


if __name__ == "__main__":
    asyncio.run(main())