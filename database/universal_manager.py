"""
Универсальный менеджер базы данных.
Автоматически выбирает между SQLite и PostgreSQL на основе переменных окружения.
"""
import logging
import os
from typing import Optional, Union

from .db_manager import DatabaseManager
from .postgres_manager import PostgreSQLManager

logger = logging.getLogger(__name__)


class UniversalDatabaseManager:
    """Универсальный менеджер базы данных"""

    def __init__(self):
        self.manager: Optional[Union[DatabaseManager,
                                     PostgreSQLManager]] = None
        self.is_postgres = False
        self._initialize()

    def _initialize(self):
        """Инициализирует подходящий менеджер базы данных"""
        # Проверяем переменную окружения USE_POSTGRES
        use_postgres = os.getenv('USE_POSTGRES', 'false').lower() in [
            'true', '1', 'yes']

        if use_postgres:
            logger.info("🐘 Инициализация PostgreSQL менеджера")
            self.manager = PostgreSQLManager()
            self.is_postgres = True
        else:
            logger.info("🗃️ Инициализация SQLite менеджера")
            self.manager = DatabaseManager()
            self.is_postgres = False

    async def initialize(self):
        """Асинхронная инициализация менеджера"""
        if self.is_postgres:
            await self.manager.initialize()
        # SQLite инициализируется автоматически в конструкторе

    async def close(self):
        """Закрывает соединения с базой данных"""
        if self.is_postgres and hasattr(self.manager, 'close'):
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

    async def add_bookmark(self, user_id: int, book_id: int, chapter: int, display_text: str):
        """Добавляет закладку"""
        if self.is_postgres:
            return await self.manager.add_bookmark(
                user_id=user_id,
                book_id=book_id,
                chapter=chapter,
                display_text=display_text,
                verse_start=None,
                verse_end=None,
                note=None
            )
        else:
            return await self.manager.add_bookmark(user_id, book_id, chapter, display_text)

    async def remove_bookmark(self, user_id: int, book_id: int, chapter: int):
        """Удаляет закладку"""
        return await self.manager.remove_bookmark(user_id, book_id, chapter)

    async def is_bookmarked(self, user_id: int, book_id: int, chapter: int):
        """Проверяет, есть ли закладка"""
        return await self.manager.is_bookmarked(user_id, book_id, chapter)

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

    # Методы для работы с планами чтения (только для PostgreSQL)
    async def get_reading_plans(self):
        """Получает все планы чтения (только PostgreSQL)"""
        if self.is_postgres:
            return await self.manager.get_reading_plans()
        else:
            # Для SQLite возвращаем пустой список, планы будут из CSV
            return []

    async def get_reading_plan_days(self, plan_id: str):
        """Получает дни плана чтения (только PostgreSQL)"""
        if self.is_postgres:
            return await self.manager.get_reading_plan_days(plan_id)
        else:
            # Для SQLite возвращаем пустой список, планы будут из CSV
            return []

    # Совместимость со старым API SQLite
    def _create_tables(self):
        """Создает таблицы (только для SQLite)"""
        if not self.is_postgres:
            return self.manager._create_tables()

    @property
    def db_file(self):
        """Путь к файлу базы данных (только для SQLite)"""
        if not self.is_postgres:
            return self.manager.db_file
        return None


# Создаем глобальный экземпляр
universal_db_manager = UniversalDatabaseManager()
