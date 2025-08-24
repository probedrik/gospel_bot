"""
Универсальный менеджер базы данных.
Автоматически выбирает между SQLite и PostgreSQL на основе переменных окружения.
"""
import logging
import os
from typing import Optional, Union, List, Dict

from .db_manager import DatabaseManager
from .postgres_manager import PostgreSQLManager
from .supabase_manager import SupabaseManager

logger = logging.getLogger(__name__)


class UniversalDatabaseManager:
    """Универсальный менеджер базы данных"""

    def __init__(self):
        self.manager: Optional[Union[DatabaseManager,
                                     PostgreSQLManager,
                                     SupabaseManager]] = None
        self.is_postgres = False
        self.is_supabase = False
        self._initialize()

    def _initialize(self):
        """Инициализирует подходящий менеджер базы данных"""
        # Проверяем переменную окружения USE_SUPABASE
        use_supabase = os.getenv('USE_SUPABASE', 'false').lower() in [
            'true', '1', 'yes']

        # Проверяем переменную окружения USE_POSTGRES
        use_postgres = os.getenv('USE_POSTGRES', 'false').lower() in [
            'true', '1', 'yes']

        if use_supabase:
            logger.info("☁️ Инициализация Supabase менеджера")
            self.manager = SupabaseManager()
            self.is_supabase = True
            self.is_postgres = False  # Supabase использует PostgreSQL, но через API
        elif use_postgres:
            logger.info("🐘 Инициализация PostgreSQL менеджера")
            self.manager = PostgreSQLManager()
            self.is_postgres = True
            self.is_supabase = False
        else:
            logger.info("🗃️ Инициализация SQLite менеджера")
            self.manager = DatabaseManager()
            self.is_postgres = False
            self.is_supabase = False

    async def initialize(self):
        """Асинхронная инициализация менеджера"""
        if self.is_postgres or self.is_supabase:
            await self.manager.initialize()
        # SQLite инициализируется автоматически в конструкторе

        # Создаем таблицу ai_settings
        await self.create_ai_settings_table()

    async def close(self):
        """Закрывает соединения с базой данных"""
        if (self.is_postgres or self.is_supabase) and hasattr(self.manager, 'close'):
            await self.manager.close()

    # Методы для работы с пользователями
    async def get_user(self, user_id: int):
        """Получает пользователя из базы данных"""
        return await self.manager.get_user(user_id)

    async def add_user(self, user_id: int, username: str, first_name: str):
        """Добавляет пользователя в базу данных"""
        return await self.manager.add_user(user_id, username, first_name)

    async def update_user_translation(self, user_id: int, translation: str):
        """Обновляет перевод пользователя"""
        return await self.manager.update_user_translation(user_id, translation)

    async def update_user_activity(self, user_id: int):
        """Обновляет время последней активности пользователя"""
        return await self.manager.update_user_activity(user_id)

    async def update_user_response_length(self, user_id: int, response_length: str):
        """Обновляет настройку длины ответа ИИ для пользователя"""
        return await self.manager.update_user_response_length(user_id, response_length)

    async def get_user_response_length(self, user_id: int) -> str:
        """Получает настройку длины ответа ИИ для пользователя"""
        return await self.manager.get_user_response_length(user_id)

    # Методы для работы с закладками
    async def get_bookmarks(self, user_id: int):
        """Получает закладки пользователя"""
        return await self.manager.get_bookmarks(user_id)

    async def add_bookmark(self, user_id: int, book_id: int, chapter_start: int,
                           display_text: str, chapter_end: int = None,
                           verse_start: int = None, verse_end: int = None, note: str = None):
        """Добавляет закладку с поддержкой диапазонов глав и стихов"""
        if self.is_postgres or self.is_supabase:
            return await self.manager.add_bookmark(
                user_id=user_id,
                book_id=book_id,
                chapter_start=chapter_start,
                chapter_end=chapter_end,
                display_text=display_text,
                verse_start=verse_start,
                verse_end=verse_end,
                note=note
            )
        else:
            return await self.manager.add_bookmark(
                user_id, book_id, chapter_start, chapter_end,
                verse_start, verse_end, display_text, note
            )

    async def remove_bookmark(self, user_id: int, book_id: int, chapter_start: int,
                              chapter_end: int = None, verse_start: int = None, verse_end: int = None):
        """Удаляет закладку"""
        return await self.manager.remove_bookmark(user_id, book_id, chapter_start, chapter_end, verse_start, verse_end)

    async def is_bookmarked(self, user_id: int, book_id: int, chapter_start: int,
                            chapter_end: int = None, verse_start: int = None, verse_end: int = None):
        """Проверяет, есть ли закладка"""
        return await self.manager.is_bookmarked(user_id, book_id, chapter_start, chapter_end, verse_start, verse_end)

    # Методы для работы с лимитами ИИ
    async def increment_ai_usage(self, user_id: int):
        """Увеличивает счетчик использования ИИ"""
        return await self.manager.increment_ai_usage(user_id)

    async def get_ai_usage(self, user_id: int, date=None):
        """Получает количество использований ИИ"""
        return await self.manager.get_ai_usage(user_id, date)

    # Методы для работы с прогрессом чтения
    async def mark_reading_day_completed(self, user_id: int, plan_id: str, day: int):
        """Отмечает день как прочитанный"""
        return await self.manager.mark_reading_day_completed(user_id, plan_id, day)

    async def mark_reading_part_completed(self, user_id: int, plan_id: str, day: int, part_idx: int):
        """Отмечает часть дня как прочитанную"""
        return await self.manager.mark_reading_part_completed(user_id, plan_id, day, part_idx)

    async def get_reading_progress(self, user_id: int, plan_id: str):
        """Получает прогресс чтения по плану"""
        return await self.manager.get_reading_progress(user_id, plan_id)

    async def get_reading_part_progress(self, user_id: int, plan_id: str, day: int):
        """Получает прогресс частей дня"""
        return await self.manager.get_reading_part_progress(user_id, plan_id, day)

    async def is_reading_day_completed(self, user_id: int, plan_id: str, day: int):
        """Проверяет, завершен ли день плана чтения"""
        return await self.manager.is_reading_day_completed(user_id, plan_id, day)

    async def is_reading_part_completed(self, user_id: int, plan_id: str, day: int, part_idx: int):
        """Проверяет, отмечена ли часть дня как прочитанная"""
        return await self.manager.is_reading_part_completed(user_id, plan_id, day, part_idx)

    # Методы для совместимости с handlers
    async def get_user_reading_plan(self, user_id: int, plan_id: str):
        """Получает план чтения пользователя"""
        return await self.manager.get_user_reading_plan(user_id, plan_id)

    async def set_user_reading_plan(self, user_id: int, plan_id: str, day: int = 1):
        """Устанавливает план чтения для пользователя"""
        return await self.manager.set_user_reading_plan(user_id, plan_id, day)

    async def get_user_reading_plans(self, user_id: int):
        """Получает все планы чтения пользователя"""
        return await self.manager.get_user_reading_plans(user_id)

    async def update_reading_plan_day(self, user_id: int, plan_id: str, day: int):
        """Обновляет текущий день плана чтения"""
        return await self.manager.update_reading_plan_day(user_id, plan_id, day)

    async def is_bookmark_exists(self, user_id: int, reference: str):
        """Проверяет существование закладки по ссылке"""
        return await self.manager.is_bookmark_exists(user_id, reference)

    # Алиасы для совместимости
    async def get_reading_progress_async(self, user_id: int, plan_id: str):
        """Алиас для get_reading_progress"""
        return await self.get_reading_progress(user_id, plan_id)

    async def is_reading_day_completed_async(self, user_id: int, plan_id: str, day: int):
        """Алиас для is_reading_day_completed"""
        return await self.is_reading_day_completed(user_id, plan_id, day)

    async def mark_reading_day_completed_async(self, user_id: int, plan_id: str, day: int):
        """Алиас для mark_reading_day_completed"""
        return await self.mark_reading_day_completed(user_id, plan_id, day)

    # Методы для работы с планами чтения (только для PostgreSQL)
    async def get_reading_plans(self):
        """Получает все планы чтения (только PostgreSQL/Supabase)"""
        if self.is_postgres or self.is_supabase:
            return await self.manager.get_reading_plans()
        else:
            # Для SQLite возвращаем пустой список, планы будут из CSV
            return []

    async def get_reading_plan_days(self, plan_id: str):
        """Получает дни плана чтения (только PostgreSQL/Supabase)"""
        if self.is_postgres or self.is_supabase:
            return await self.manager.get_reading_plan_days(plan_id)
        else:
            # Для SQLite возвращаем пустой список, планы будут из CSV
            return []

    async def get_reading_plan_by_id(self, plan_id: str):
        """Получает план чтения по ID (только PostgreSQL/Supabase)"""
        if self.is_postgres or self.is_supabase:
            return await self.manager.get_reading_plan_by_id(plan_id)
        else:
            return None

    # Совместимость со старым API SQLite
    def _create_tables(self):
        """Создает таблицы (только для SQLite)"""
        if not self.is_postgres and not self.is_supabase:
            return self.manager._create_tables()

    @property
    def db_file(self):
        """Путь к файлу базы данных (только для SQLite)"""
        if not self.is_postgres and not self.is_supabase:
            return self.manager.db_file
        return None

    # AI Limits методы
    async def get_ai_limit(self, user_id: int, date: str) -> int:
        """Возвращает количество ИИ-запросов пользователя за дату (строка YYYY-MM-DD)"""
        return await self.manager.get_ai_limit(user_id, date)

    async def increment_ai_limit(self, user_id: int, date: str) -> int:
        """Увеличивает счетчик ИИ-запросов пользователя за дату, возвращает новое значение"""
        return await self.manager.increment_ai_limit(user_id, date)

    async def reset_ai_limit(self, user_id: int, date: str) -> None:
        """Сбросить лимит ИИ-запросов пользователя за дату (обнуляет счетчик)"""
        return await self.manager.reset_ai_limit(user_id, date)

    async def get_ai_stats(self, date: str, limit: int = 10) -> list:
        """Топ пользователей по ИИ-запросам за дату (user_id, count)"""
        return await self.manager.get_ai_stats(date, limit)

    async def get_ai_stats_alltime(self, limit: int = 10) -> list:
        """Топ пользователей по ИИ-запросам за всё время (user_id, total_count)"""
        return await self.manager.get_ai_stats_alltime(limit)

    # Методы для сохраненных толкований
    async def save_commentary(self, user_id: int, book_id: int, chapter_start: int,
                              chapter_end: int = None, verse_start: int = None, verse_end: int = None,
                              reference_text: str = "", commentary_text: str = "",
                              commentary_type: str = "ai") -> bool:
        """Сохраняет толкование для пользователя"""
        return await self.manager.save_commentary(
            user_id, book_id, chapter_start, chapter_end, verse_start, verse_end,
            reference_text, commentary_text, commentary_type)

    async def get_saved_commentary(self, user_id: int, book_id: int, chapter_start: int,
                                   chapter_end: int = None, verse_start: int = None, verse_end: int = None,
                                   commentary_type: str = "ai") -> Optional[str]:
        """Получает сохраненное толкование"""
        return await self.manager.get_saved_commentary(
            user_id, book_id, chapter_start, chapter_end, verse_start, verse_end, commentary_type)

    async def delete_saved_commentary(self, user_id: int, book_id: int = None, chapter_start: int = None,
                                      chapter_end: int = None, verse_start: int = None, verse_end: int = None,
                                      commentary_type: str = "ai", commentary_id: int = None) -> bool:
        """Удаляет сохраненное толкование по параметрам или ID"""
        if commentary_id is not None:
            # Удаление по ID (для новой системы закладок)
            if hasattr(self.manager, 'delete_commentary_by_id'):
                return await self.manager.delete_commentary_by_id(user_id, commentary_id)
            else:
                # Fallback: получаем все комментарии и находим нужный
                commentaries = await self.get_user_commentaries(user_id)
                for i, commentary in enumerate(commentaries):
                    if commentary.get('id') == commentary_id:
                        # Используем данные из комментария для удаления
                        return await self.manager.delete_saved_commentary(
                            user_id,
                            commentary.get('book_id'),
                            commentary.get('chapter_start'),
                            commentary.get('chapter_end'),
                            commentary.get('verse_start'),
                            commentary.get('verse_end'),
                            commentary.get('commentary_type', 'ai')
                        )
                return False
        else:
            # Удаление по параметрам (старый способ)
            return await self.manager.delete_saved_commentary(
                user_id, book_id, chapter_start, chapter_end, verse_start, verse_end, commentary_type)

    async def get_user_commentaries(self, user_id: int, limit: int = 50) -> list:
        """Получает последние сохраненные толкования пользователя"""
        return await self.manager.get_user_commentaries(user_id, limit)

    async def get_saved_commentaries(self, user_id: int, limit: int = 50) -> list:
        """Алиас для get_user_commentaries для совместимости"""
        return await self.get_user_commentaries(user_id, limit)

    # Методы для библейских тем
    async def get_bible_topics(self, search_query: str = "", limit: int = 50) -> list:
        """Получает список библейских тем с возможностью поиска"""
        return await self.manager.get_bible_topics(search_query, limit)

    # Универсальные методы для работы с базой данных
    async def fetch_one(self, query: str, params: tuple = None) -> Optional[Dict]:
        """Выполняет запрос и возвращает одну запись"""
        try:
            if self.is_postgres or self.is_supabase:
                # Для PostgreSQL/Supabase используем asyncpg
                if hasattr(self.manager, 'pool') and self.manager.pool:
                    async with self.manager.pool.acquire() as conn:
                        row = await conn.fetchrow(query, *(params or ()))
                        return dict(row) if row else None
                else:
                    logger.error("Пул соединений не инициализирован")
                    return None
            else:
                # Для SQLite используем синхронный подход в отдельном потоке
                import sqlite3
                import asyncio

                def _sync_fetch_one():
                    conn = sqlite3.connect(self.manager.db_file)
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute(query, params or ())
                    row = cursor.fetchone()
                    conn.close()
                    return dict(row) if row else None

                return await asyncio.get_event_loop().run_in_executor(None, _sync_fetch_one)

        except Exception as e:
            logger.error(f"Ошибка выполнения fetch_one: {e}")
            return None

    async def fetch_all(self, query: str, params: tuple = None) -> List[Dict]:
        """Выполняет запрос и возвращает все записи"""
        try:
            if self.is_postgres or self.is_supabase:
                # Для PostgreSQL/Supabase используем asyncpg
                if hasattr(self.manager, 'pool') and self.manager.pool:
                    async with self.manager.pool.acquire() as conn:
                        rows = await conn.fetch(query, *(params or ()))
                        return [dict(row) for row in rows]
                else:
                    logger.error("Пул соединений не инициализирован")
                    return []
            else:
                # Для SQLite используем синхронный подход в отдельном потоке
                import sqlite3
                import asyncio

                def _sync_fetch_all():
                    conn = sqlite3.connect(self.manager.db_file)
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute(query, params or ())
                    rows = cursor.fetchall()
                    conn.close()
                    return [dict(row) for row in rows]

                return await asyncio.get_event_loop().run_in_executor(None, _sync_fetch_all)

        except Exception as e:
            logger.error(f"Ошибка выполнения fetch_all: {e}")
            return []

    async def execute(self, query: str, params: tuple = None) -> bool:
        """Выполняет запрос на изменение данных"""
        try:
            if self.is_postgres or self.is_supabase:
                # Для PostgreSQL/Supabase используем asyncpg
                if hasattr(self.manager, 'pool') and self.manager.pool:
                    async with self.manager.pool.acquire() as conn:
                        await conn.execute(query, *(params or ()))
                        return True
                else:
                    logger.error("Пул соединений не инициализирован")
                    return False
            else:
                # Для SQLite используем синхронный подход в отдельном потоке
                import sqlite3
                import asyncio

                def _sync_execute():
                    conn = sqlite3.connect(self.manager.db_file)
                    cursor = conn.cursor()
                    cursor.execute(query, params or ())
                    conn.commit()
                    conn.close()
                    return True

                return await asyncio.get_event_loop().run_in_executor(None, _sync_execute)

        except Exception as e:
            logger.error(f"Ошибка выполнения execute: {e}")
            return False

    async def create_ai_settings_table(self) -> bool:
        """Создает таблицу ai_settings если она не существует"""
        try:
            # SQL для создания таблицы
            if self.is_postgres or self.is_supabase:
                create_table_sql = """
                    CREATE TABLE IF NOT EXISTS ai_settings (
                        id SERIAL PRIMARY KEY,
                        setting_key VARCHAR(100) NOT NULL UNIQUE,
                        setting_value TEXT NOT NULL,
                        setting_type VARCHAR(20) NOT NULL DEFAULT 'string',
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """
            else:
                # SQLite версия
                create_table_sql = """
                    CREATE TABLE IF NOT EXISTS ai_settings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        setting_key TEXT NOT NULL UNIQUE,
                        setting_value TEXT NOT NULL,
                        setting_type TEXT NOT NULL DEFAULT 'string',
                        description TEXT,
                        created_at TEXT DEFAULT (datetime('now')),
                        updated_at TEXT DEFAULT (datetime('now'))
                    );
                """

            await self.execute(create_table_sql)

            # Создаем индекс
            index_sql = "CREATE INDEX IF NOT EXISTS idx_ai_settings_key ON ai_settings(setting_key);"
            await self.execute(index_sql)

            # Вставляем значения по умолчанию
            defaults = [
                ('ai_daily_limit', '3', 'integer',
                 'Дневной лимит ИИ запросов для обычных пользователей'),
                ('premium_package_price', '100', 'integer',
                 'Цена премиум пакета в рублях'),
                ('premium_package_requests', '30', 'integer',
                 'Количество запросов в премиум пакете'),
                ('admin_premium_mode', 'true', 'boolean',
                 'Использует ли админ премиум ИИ по умолчанию'),
                ('free_premium_users', '[]', 'string',
                 'JSON список пользователей с бесплатным премиум доступом')
            ]

            for key, value, setting_type, description in defaults:
                # Проверяем, существует ли уже настройка
                existing = await self.fetch_one("SELECT setting_key FROM ai_settings WHERE setting_key = ?", (key,))
                if not existing:
                    await self.execute(
                        "INSERT INTO ai_settings (setting_key, setting_value, setting_type, description) VALUES (?, ?, ?, ?)",
                        (key, value, setting_type, description)
                    )

            logger.info("✅ Таблица ai_settings создана и инициализирована")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка создания таблицы ai_settings: {e}")
            return False

    async def get_topic_by_name(self, topic_name: str) -> dict:
        """Получает тему по точному названию"""
        return await self.manager.get_topic_by_name(topic_name)

    async def get_topic_by_id(self, topic_id: int) -> dict:
        """Получает тему по ID"""
        return await self.manager.get_topic_by_id(topic_id)

    async def search_topics_fulltext(self, search_query: str, limit: int = 20) -> list:
        """Полнотекстовый поиск по темам"""
        return await self.manager.search_topics_fulltext(search_query, limit)

    async def get_topics_count(self) -> int:
        """Получает общее количество тем"""
        return await self.manager.get_topics_count()

    async def add_bible_topic(self, topic_name: str, verses: str) -> bool:
        """Добавляет новую библейскую тему"""
        return await self.manager.add_bible_topic(topic_name, verses)

    async def update_bible_topic(self, topic_id: int, topic_name: str = None, verses: str = None) -> bool:
        """Обновляет существующую библейскую тему"""
        return await self.manager.update_bible_topic(topic_id, topic_name, verses)

    async def delete_bible_topic(self, topic_id: int) -> bool:
        """Удаляет библейскую тему"""
        return await self.manager.delete_bible_topic(topic_id)

    # === Диалоговый ассистент: врапперы для Supabase ===
    async def create_conversation(self, user_id: int, title: str = None):
        if hasattr(self.manager, 'create_conversation'):
            return await self.manager.create_conversation(user_id, title)
        return None

    async def update_conversation_title(self, conversation_id: str, user_id: int, title: str) -> bool:
        if hasattr(self.manager, 'update_conversation_title'):
            return await self.manager.update_conversation_title(conversation_id, user_id, title)
        return False

    async def get_conversation(self, conversation_id: str, user_id: int):
        if hasattr(self.manager, 'get_conversation'):
            return await self.manager.get_conversation(conversation_id, user_id)
        return None

    async def list_conversations(self, user_id: int, limit: int = 20):
        if hasattr(self.manager, 'list_conversations'):
            return await self.manager.list_conversations(user_id, limit)
        return []

    async def delete_conversation(self, conversation_id: str, user_id: int) -> bool:
        if hasattr(self.manager, 'delete_conversation'):
            return await self.manager.delete_conversation(conversation_id, user_id)
        return False

    async def add_message(self, conversation_id: str, role: str, content: str, meta=None):
        if hasattr(self.manager, 'add_message'):
            return await self.manager.add_message(conversation_id, role, content, meta)
        return None

    async def list_messages(self, conversation_id: str, limit: int = 20):
        if hasattr(self.manager, 'list_messages'):
            return await self.manager.list_messages(conversation_id, limit)
        return []

    # === МЕТОДЫ ДЛЯ РАБОТЫ С НАСТРОЙКАМИ ИИ ===

    async def get_ai_setting(self, setting_key: str):
        """Получает настройку ИИ по ключу"""
        if hasattr(self.manager, 'get_ai_setting'):
            return await self.manager.get_ai_setting(setting_key)
        else:
            # Fallback для SQLite
            result = await self.fetch_one("SELECT * FROM ai_settings WHERE setting_key = ?", (setting_key,))
            return result

    async def set_ai_setting(self, setting_key: str, setting_value: str, setting_type: str = 'string', description: str = None) -> bool:
        """Устанавливает настройку ИИ"""
        if hasattr(self.manager, 'set_ai_setting'):
            return await self.manager.set_ai_setting(setting_key, setting_value, setting_type, description)
        else:
            # Fallback для SQLite
            try:
                # Пытаемся обновить существующую настройку
                await self.execute(
                    "INSERT OR REPLACE INTO ai_settings (setting_key, setting_value, setting_type, description, updated_at) VALUES (?, ?, ?, ?, datetime('now'))",
                    (setting_key, setting_value, setting_type, description)
                )
                return True
            except Exception as e:
                logger.error(f"Ошибка установки настройки {setting_key}: {e}")
                return False

    async def get_all_ai_settings(self):
        """Получает все настройки ИИ"""
        if hasattr(self.manager, 'get_all_ai_settings'):
            return await self.manager.get_all_ai_settings()
        else:
            # Fallback для SQLite
            return await self.fetch_all("SELECT * FROM ai_settings ORDER BY setting_key")

    # === МЕТОДЫ ДЛЯ РАБОТЫ С ПРЕМИУМ ЗАПРОСАМИ ===

    async def get_user_premium_requests(self, user_id: int) -> int:
        """Получает количество премиум запросов пользователя"""
        if hasattr(self.manager, 'get_user_premium_requests'):
            return await self.manager.get_user_premium_requests(user_id)
        else:
            # Fallback для SQLite
            result = await self.fetch_one("SELECT requests_count FROM premium_requests WHERE user_id = ?", (user_id,))
            return result['requests_count'] if result else 0

    async def add_premium_requests(self, user_id: int, count: int) -> bool:
        """Добавляет премиум запросы пользователю"""
        if hasattr(self.manager, 'add_premium_requests'):
            return await self.manager.add_premium_requests(user_id, count)
        else:
            # Fallback для SQLite
            try:
                # Получаем текущие данные
                existing = await self.fetch_one("SELECT * FROM premium_requests WHERE user_id = ?", (user_id,))

                if existing:
                    # Обновляем существующую запись
                    new_count = existing['requests_count'] + count
                    new_total = existing['total_purchased'] + count

                    await self.execute(
                        "UPDATE premium_requests SET requests_count = ?, total_purchased = ?, updated_at = datetime('now') WHERE user_id = ?",
                        (new_count, new_total, user_id)
                    )
                else:
                    # Создаем новую запись
                    await self.execute(
                        "INSERT INTO premium_requests (user_id, requests_count, total_purchased, total_used) VALUES (?, ?, ?, 0)",
                        (user_id, count, count)
                    )

                return True
            except Exception as e:
                logger.error(
                    f"Ошибка добавления премиум запросов пользователю {user_id}: {e}")
                return False

    async def use_premium_request(self, user_id: int) -> bool:
        """Использует один премиум запрос"""
        if hasattr(self.manager, 'use_premium_request'):
            return await self.manager.use_premium_request(user_id)
        else:
            # Fallback для SQLite
            try:
                # Получаем текущее количество
                result = await self.fetch_one("SELECT * FROM premium_requests WHERE user_id = ?", (user_id,))

                if not result or result['requests_count'] <= 0:
                    return False

                new_count = result['requests_count'] - 1
                new_used = result['total_used'] + 1

                # Обновляем запись
                await self.execute(
                    "UPDATE premium_requests SET requests_count = ?, total_used = ?, updated_at = datetime('now') WHERE user_id = ?",
                    (new_count, new_used, user_id)
                )

                return True
            except Exception as e:
                logger.error(
                    f"Ошибка использования премиум запроса пользователем {user_id}: {e}")
                return False

    async def get_premium_stats(self, user_id: int):
        """Получает статистику премиум запросов пользователя"""
        if hasattr(self.manager, 'get_premium_stats'):
            return await self.manager.get_premium_stats(user_id)
        else:
            # Fallback для SQLite
            try:
                result = await self.fetch_one("SELECT * FROM premium_requests WHERE user_id = ?", (user_id,))

                if result:
                    return {
                        'available': result['requests_count'],
                        'total_purchased': result['total_purchased'],
                        'total_used': result['total_used'],
                        'created_at': result['created_at']
                    }
                else:
                    return {
                        'available': 0,
                        'total_purchased': 0,
                        'total_used': 0,
                        'created_at': None
                    }
            except Exception as e:
                logger.error(
                    f"Ошибка получения статистики премиум запросов для пользователя {user_id}: {e}")
                return {
                    'available': 0,
                    'total_purchased': 0,
                    'total_used': 0,
                    'created_at': None
                }

    # === МЕТОДЫ ДЛЯ РАБОТЫ С ПОКУПКАМИ И ПОЖЕРТВОВАНИЯМИ ===

    async def create_premium_purchase(self, user_id: int, requests_count: int, amount_rub: int, payment_id: str) -> bool:
        """Создает запись о покупке премиум запросов"""
        if hasattr(self.manager, 'create_premium_purchase'):
            return await self.manager.create_premium_purchase(user_id, requests_count, amount_rub, payment_id)
        else:
            # Fallback для SQLite
            try:
                await self.execute(
                    "INSERT INTO premium_purchases (user_id, requests_count, amount_rub, payment_id, payment_status) VALUES (?, ?, ?, ?, 'pending')",
                    (user_id, requests_count, amount_rub, payment_id)
                )
                return True
            except Exception as e:
                logger.error(f"Ошибка создания покупки премиум запросов: {e}")
                return False

    async def complete_premium_purchase(self, payment_id: str) -> bool:
        """Завершает покупку премиум запросов"""
        if hasattr(self.manager, 'complete_premium_purchase'):
            return await self.manager.complete_premium_purchase(payment_id)
        else:
            # Fallback для SQLite - упрощенная версия
            try:
                # Получаем данные покупки
                purchase = await self.fetch_one(
                    "SELECT user_id, requests_count FROM premium_purchases WHERE payment_id = ? AND payment_status = 'pending'",
                    (payment_id,)
                )

                if not purchase:
                    return False

                # Обновляем статус покупки
                await self.execute(
                    "UPDATE premium_purchases SET payment_status = 'completed', completed_at = datetime('now') WHERE payment_id = ?",
                    (payment_id,)
                )

                # Добавляем премиум запросы пользователю
                return await self.add_premium_requests(purchase['user_id'], purchase['requests_count'])

            except Exception as e:
                logger.error(
                    f"Ошибка завершения покупки премиум запросов: {e}")
                return False

    async def create_donation(self, user_id: int, amount_rub: int, payment_id: str, message: str = None) -> bool:
        """Создает запись о пожертвовании"""
        if hasattr(self.manager, 'create_donation'):
            return await self.manager.create_donation(user_id, amount_rub, payment_id, message)
        else:
            # Fallback для SQLite
            try:
                await self.execute(
                    "INSERT INTO donations (user_id, amount_rub, payment_id, message, payment_status) VALUES (?, ?, ?, ?, 'pending')",
                    (user_id, amount_rub, payment_id, message)
                )
                return True
            except Exception as e:
                logger.error(f"Ошибка создания пожертвования: {e}")
                return False

    async def complete_donation(self, payment_id: str) -> bool:
        """Завершает пожертвование"""
        if hasattr(self.manager, 'complete_donation'):
            return await self.manager.complete_donation(payment_id)
        else:
            # Fallback для SQLite
            try:
                await self.execute(
                    "UPDATE donations SET payment_status = 'completed', completed_at = datetime('now') WHERE payment_id = ? AND payment_status = 'pending'",
                    (payment_id,)
                )
                return True
            except Exception as e:
                logger.error(f"Ошибка завершения пожертвования: {e}")
                return False


# Создаем глобальный экземпляр
universal_db_manager = UniversalDatabaseManager()
