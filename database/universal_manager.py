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


# Создаем глобальный экземпляр
universal_db_manager = UniversalDatabaseManager()
