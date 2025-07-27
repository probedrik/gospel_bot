#!/usr/bin/env python3
"""
Скрипт миграции SQLite базы данных для обновления структуры таблицы bookmarks
"""
import sqlite3
import os
import shutil
from datetime import datetime


def migrate_sqlite_bookmarks():
    """Мигрирует SQLite базу данных для поддержки новой структуры закладок"""
    
    db_file = "data/bible_bot.db"
    backup_file = f"data/bible_bot_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    
    print("🔄 Миграция SQLite базы данных...")
    print("=" * 50)
    
    # Проверяем существование файла БД
    if not os.path.exists(db_file):
        print(f"❌ Файл базы данных не найден: {db_file}")
        return False
    
    # Создаем резервную копию
    print(f"💾 Создание резервной копии: {backup_file}")
    try:
        shutil.copy2(db_file, backup_file)
        print("✅ Резервная копия создана")
    except Exception as e:
        print(f"❌ Ошибка создания резервной копии: {e}")
        return False
    
    try:
        # Подключаемся к базе данных
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Проверяем текущую структуру таблицы
        cursor.execute("PRAGMA table_info(bookmarks)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"📋 Текущие колонки: {column_names}")
        
        # Проверяем, нужна ли миграция
        if 'chapter_start' in column_names:
            print("✅ Таблица уже имеет новую структуру")
            conn.close()
            return True
        
        print("🔧 Выполнение миграции...")
        
        # Получаем все существующие данные
        cursor.execute("SELECT * FROM bookmarks")
        old_data = cursor.fetchall()
        print(f"📊 Найдено {len(old_data)} существующих закладок")
        
        # Создаем новую таблицу с обновленной структурой
        cursor.execute('''
            CREATE TABLE bookmarks_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                book_id INTEGER,
                chapter_start INTEGER NOT NULL,
                chapter_end INTEGER,
                verse_start INTEGER,
                verse_end INTEGER,
                display_text TEXT,
                note TEXT,
                created_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Переносим данные из старой таблицы в новую
        if old_data:
            print("📦 Перенос данных...")
            for row in old_data:
                # Старая структура: id, user_id, book_id, chapter, display_text, comment, created_at
                old_id, user_id, book_id, chapter, display_text, comment, created_at = row
                
                # Новая структура: добавляем chapter_start = chapter, остальные поля NULL
                cursor.execute('''
                    INSERT INTO bookmarks_new 
                    (id, user_id, book_id, chapter_start, chapter_end, verse_start, verse_end, display_text, note, created_at)
                    VALUES (?, ?, ?, ?, NULL, NULL, NULL, ?, ?, ?)
                ''', (old_id, user_id, book_id, chapter, display_text, comment, created_at))
            
            print(f"✅ Перенесено {len(old_data)} закладок")
        
        # Удаляем старую таблицу и переименовываем новую
        cursor.execute("DROP TABLE bookmarks")
        cursor.execute("ALTER TABLE bookmarks_new RENAME TO bookmarks")
        
        # Создаем индексы
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bookmarks_user_id ON bookmarks(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bookmarks_chapters ON bookmarks(user_id, book_id, chapter_start, chapter_end)")
        
        # Сохраняем изменения
        conn.commit()
        conn.close()
        
        print("✅ Миграция успешно завершена!")
        print(f"💾 Резервная копия сохранена: {backup_file}")
        
        # Проверяем результат
        print("\\n🔍 Проверка результата...")
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(bookmarks)")
        new_columns = cursor.fetchall()
        new_column_names = [col[1] for col in new_columns]
        
        print(f"📋 Новые колонки: {new_column_names}")
        
        cursor.execute("SELECT COUNT(*) FROM bookmarks")
        count = cursor.fetchone()[0]
        print(f"📊 Количество закладок после миграции: {count}")
        
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        
        # Восстанавливаем из резервной копии
        if os.path.exists(backup_file):
            print("🔄 Восстановление из резервной копии...")
            try:
                shutil.copy2(backup_file, db_file)
                print("✅ База данных восстановлена из резервной копии")
            except Exception as restore_error:
                print(f"❌ Ошибка восстановления: {restore_error}")
        
        return False


if __name__ == "__main__":
    success = migrate_sqlite_bookmarks()
    if success:
        print("\\n🎉 Миграция завершена успешно!")
        print("Теперь можно запустить: python check_bookmarks_compatibility.py")
    else:
        print("\\n💥 Миграция не удалась!")
        print("Проверьте логи и попробуйте снова.")