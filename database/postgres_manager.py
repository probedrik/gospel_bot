"""
Модуль для управления базой данных PostgreSQL.
Отвечает за хранение информации о пользователях, закладках и планах чтения.
"""
import asyncpg
import logging
import asyncio
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any
import os

# Инициализация логгера
logger = logging.getLogger(__name__)


class PostgreSQLManager:
    """Класс для управления базой данных PostgreSQL"""

    def __init__(self,
                 host: str = None,
                 port: int = None,
                 database: str = None,
                 user: str = None,
                 password: str = None):
        """
        Инициализирует менеджер базы данных PostgreSQL.

        Args:
            host: хост PostgreSQL
            port: порт PostgreSQL  
            database: название базы данных
            user: пользователь
            password: пароль
        """
        # Получаем параметры подключения из переменных окружения или используем переданные
        self.host = host or os.getenv('POSTGRES_HOST', 'localhost')
        self.port = port or int(os.getenv('POSTGRES_PORT', '5432'))
        self.database = database or os.getenv('POSTGRES_DB', 'gospel_bot')
        self.user = user or os.getenv('POSTGRES_USER', 'postgres')
        self.password = password or os.getenv('POSTGRES_PASSWORD', '')

        # Пул соединений
        self.pool = None

        logger.info(
            f"Инициализация PostgreSQL: {self.host}:{self.port}/{self.database}")

    async def initialize(self):
        """Инициализирует пул соединений и создает таблицы"""
        try:
            # Создаем пул соединений
            self.pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                min_size=2,
                max_size=10
            )
            logger.info("Пул соединений PostgreSQL создан")

            # Создаем таблицы
            await self._create_tables()
            logger.info("База данных PostgreSQL инициализирована")

        except Exception as e:
            logger.error(
                f"Ошибка инициализации PostgreSQL: {e}", exc_info=True)
            raise

    async def close(self):
        """Закрывает пул соединений"""
        if self.pool:
            await self.pool.close()
            logger.info("Пул соединений PostgreSQL закрыт")

    async def _create_tables(self):
        """Создает необходимые таблицы в базе данных"""
        async with self.pool.acquire() as conn:
            try:
                # Таблица пользователей
                await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    current_translation TEXT DEFAULT 'rst',
                    last_activity TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                ''')

                # Таблица закладок
                await conn.execute('''
                CREATE TABLE IF NOT EXISTS bookmarks (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                    book_id INTEGER NOT NULL,
                    chapter INTEGER NOT NULL,
                    verse_start INTEGER,
                    verse_end INTEGER,
                    display_text TEXT,
                    note TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                ''')

                # Индекс для быстрого поиска закладок пользователя
                await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_bookmarks_user_id 
                ON bookmarks(user_id)
                ''')

                # Таблица лимитов ИИ
                await conn.execute('''
                CREATE TABLE IF NOT EXISTS ai_limits (
                    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                    date DATE NOT NULL,
                    count INTEGER DEFAULT 0,
                    PRIMARY KEY (user_id, date)
                )
                ''')

                # Таблица планов чтения
                await conn.execute('''
                CREATE TABLE IF NOT EXISTS reading_plans (
                    plan_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    total_days INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                ''')

                # Таблица дней планов чтения
                await conn.execute('''
                CREATE TABLE IF NOT EXISTS reading_plan_days (
                    plan_id TEXT REFERENCES reading_plans(plan_id) ON DELETE CASCADE,
                    day_number INTEGER NOT NULL,
                    reading_text TEXT NOT NULL,
                    PRIMARY KEY (plan_id, day_number)
                )
                ''')

                # Таблица прогресса чтения по дням
                await conn.execute('''
                CREATE TABLE IF NOT EXISTS reading_progress (
                    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                    plan_id TEXT REFERENCES reading_plans(plan_id) ON DELETE CASCADE,
                    day_number INTEGER NOT NULL,
                    completed BOOLEAN DEFAULT FALSE,
                    completed_at TIMESTAMP,
                    PRIMARY KEY (user_id, plan_id, day_number)
                )
                ''')

                # Таблица прогресса чтения по частям дня
                await conn.execute('''
                CREATE TABLE IF NOT EXISTS reading_parts_progress (
                    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                    plan_id TEXT REFERENCES reading_plans(plan_id) ON DELETE CASCADE,
                    day_number INTEGER NOT NULL,
                    part_idx INTEGER NOT NULL,
                    completed BOOLEAN DEFAULT FALSE,
                    completed_at TIMESTAMP,
                    PRIMARY KEY (user_id, plan_id, day_number, part_idx)
                )
                ''')

                # Индексы для улучшения производительности
                await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_reading_progress_user_plan 
                ON reading_progress(user_id, plan_id)
                ''')

                await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_reading_parts_progress_user_plan 
                ON reading_parts_progress(user_id, plan_id)
                ''')

                logger.info("Все таблицы PostgreSQL созданы")

            except Exception as e:
                logger.error(
                    f"Ошибка создания таблиц PostgreSQL: {e}", exc_info=True)
                raise

    # Методы для работы с пользователями
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получает информацию о пользователе"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE user_id = $1", user_id
            )
            return dict(row) if row else None

    async def add_user(self, user_id: int, username: str, first_name: str) -> None:
        """Добавляет или обновляет пользователя"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO users (user_id, username, first_name, last_activity)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (user_id) DO UPDATE SET
                    username = EXCLUDED.username,
                    first_name = EXCLUDED.first_name,
                    last_activity = EXCLUDED.last_activity
            ''', user_id, username, first_name, datetime.now())

    # Методы для работы с закладками
    async def add_bookmark(self, user_id: int, book_id: int, chapter: int,
                           display_text: str, verse_start: int = None,
                           verse_end: int = None, note: str = None) -> bool:
        """Добавляет закладку"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO bookmarks 
                    (user_id, book_id, chapter, verse_start, verse_end, display_text, note)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                ''', user_id, book_id, chapter, verse_start, verse_end, display_text, note)
                return True
        except Exception as e:
            logger.error(f"Ошибка добавления закладки: {e}")
            return False

    async def get_bookmarks(self, user_id: int) -> List[Tuple]:
        """Получает все закладки пользователя"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT book_id, chapter, display_text, verse_start, verse_end, note, created_at
                FROM bookmarks 
                WHERE user_id = $1 
                ORDER BY created_at DESC
            ''', user_id)
            return [tuple(row) for row in rows]

    async def remove_bookmark(self, user_id: int, book_id: int, chapter: int) -> bool:
        """Удаляет закладку"""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute('''
                    DELETE FROM bookmarks 
                    WHERE user_id = $1 AND book_id = $2 AND chapter = $3
                ''', user_id, book_id, chapter)
                return result != 'DELETE 0'
        except Exception as e:
            logger.error(f"Ошибка удаления закладки: {e}")
            return False

    # Методы для работы с планами чтения
    async def add_reading_plan(self, plan_id: str, title: str, description: str = None) -> bool:
        """Добавляет план чтения"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO reading_plans (plan_id, title, description, total_days)
                    VALUES ($1, $2, $3, 0)
                    ON CONFLICT (plan_id) DO UPDATE SET
                        title = EXCLUDED.title,
                        description = EXCLUDED.description
                ''', plan_id, title, description)
                return True
        except Exception as e:
            logger.error(f"Ошибка добавления плана: {e}")
            return False

    async def add_reading_plan_day(self, plan_id: str, day_number: int, reading_text: str) -> bool:
        """Добавляет день к плану чтения"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO reading_plan_days (plan_id, day_number, reading_text)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (plan_id, day_number) DO UPDATE SET
                        reading_text = EXCLUDED.reading_text
                ''', plan_id, day_number, reading_text)

                # Обновляем общее количество дней
                await conn.execute('''
                    UPDATE reading_plans 
                    SET total_days = (
                        SELECT COUNT(*) FROM reading_plan_days WHERE plan_id = $1
                    )
                    WHERE plan_id = $1
                ''', plan_id)
                return True
        except Exception as e:
            logger.error(f"Ошибка добавления дня плана: {e}")
            return False

    async def get_reading_plans(self) -> List[Dict]:
        """Получает все планы чтения"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT plan_id, title, description, total_days, created_at
                FROM reading_plans
                ORDER BY title
            ''')
            return [dict(row) for row in rows]

    async def get_reading_plan_days(self, plan_id: str) -> List[Dict]:
        """Получает все дни плана чтения"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT day_number, reading_text
                FROM reading_plan_days
                WHERE plan_id = $1
                ORDER BY day_number
            ''', plan_id)
            return [dict(row) for row in rows]

    # Методы для работы с прогрессом чтения
    async def mark_reading_day_completed(self, user_id: int, plan_id: str, day: int) -> bool:
        """Отмечает день как прочитанный"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO reading_progress (user_id, plan_id, day_number, completed, completed_at)
                    VALUES ($1, $2, $3, TRUE, $4)
                    ON CONFLICT (user_id, plan_id, day_number) DO UPDATE SET
                        completed = TRUE,
                        completed_at = EXCLUDED.completed_at
                ''', user_id, plan_id, day, datetime.now())
                return True
        except Exception as e:
            logger.error(f"Ошибка отметки дня как прочитанного: {e}")
            return False

    async def mark_reading_part_completed(self, user_id: int, plan_id: str, day: int, part_idx: int) -> bool:
        """Отмечает часть дня как прочитанную"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO reading_parts_progress (user_id, plan_id, day_number, part_idx, completed, completed_at)
                    VALUES ($1, $2, $3, $4, TRUE, $5)
                    ON CONFLICT (user_id, plan_id, day_number, part_idx) DO UPDATE SET
                        completed = TRUE,
                        completed_at = EXCLUDED.completed_at
                ''', user_id, plan_id, day, part_idx, datetime.now())
                return True
        except Exception as e:
            logger.error(f"Ошибка отметки части дня как прочитанной: {e}")
            return False

    # Методы для работы с лимитами ИИ
    async def increment_ai_usage(self, user_id: int) -> bool:
        """Увеличивает счетчик использования ИИ"""
        try:
            today = datetime.now().date()
            async with self.pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO ai_limits (user_id, date, count)
                    VALUES ($1, $2, 1)
                    ON CONFLICT (user_id, date) DO UPDATE SET
                        count = ai_limits.count + 1
                ''', user_id, today)
                return True
        except Exception as e:
            logger.error(f"Ошибка увеличения счетчика ИИ: {e}")
            return False

    async def get_ai_usage(self, user_id: int, date: datetime = None) -> int:
        """Получает количество использований ИИ за день"""
        if date is None:
            date = datetime.now().date()

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('''
                SELECT count FROM ai_limits 
                WHERE user_id = $1 AND date = $2
            ''', user_id, date)
            return row['count'] if row else 0


# Создаем глобальный экземпляр
postgres_manager = PostgreSQLManager()
