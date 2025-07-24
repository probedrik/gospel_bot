"""
Модуль для управления базой данных PostgreSQL.
Отвечает за хранение информации о пользователях, закладках и планах чтения.
"""
import asyncpg
import logging
import asyncio
import ssl
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
        self.ssl = os.getenv('POSTGRES_SSL', None)
        self.ssl_cert = os.getenv('POSTGRES_SSL_CERT', None)
        self.min_connections = int(os.getenv('POSTGRES_MIN_CONNECTIONS', '1'))
        self.max_connections = int(os.getenv('POSTGRES_MAX_CONNECTIONS', '10'))

        # Пул соединений
        self.pool = None

        logger.info(
            f"Инициализация PostgreSQL: {self.host}:{self.port}/{self.database} (SSL: {self.ssl})")

    async def initialize(self):
        """Инициализирует пул соединений и создает таблицы"""
        try:
            # Подготавливаем параметры подключения
            connection_params = {
                'host': self.host,
                'port': self.port,
                'database': self.database,
                'user': self.user,
                'password': self.password,
                'min_size': self.min_connections,
                'max_size': self.max_connections
            }

            # Добавляем SSL если указан
            if self.ssl:
                if self.ssl_cert and os.path.exists(self.ssl_cert):
                    # Создаем SSL контекст с сертификатом
                    ssl_context = ssl.create_default_context(
                        cafile=self.ssl_cert)
                    ssl_context.check_hostname = False  # Для Supabase
                    connection_params['ssl'] = ssl_context
                    logger.info(
                        f"SSL соединение с сертификатом: {self.ssl_cert}")
                else:
                    # Используем стандартный SSL
                    connection_params['ssl'] = self.ssl
                    logger.info(f"SSL соединение: {self.ssl}")

            # Создаем пул соединений
            self.pool = await asyncpg.create_pool(**connection_params)
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

                # Таблица планов чтения пользователей
                await conn.execute('''
                CREATE TABLE IF NOT EXISTS user_reading_plans (
                    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                    plan_id TEXT REFERENCES reading_plans(plan_id) ON DELETE CASCADE,
                    current_day INTEGER DEFAULT 1,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, plan_id)
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

                # Таблица сохраненных толкований
                await conn.execute('''
                CREATE TABLE IF NOT EXISTS saved_commentaries (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                    book_id INTEGER NOT NULL,
                    chapter_start INTEGER NOT NULL,
                    chapter_end INTEGER,
                    verse_start INTEGER,
                    verse_end INTEGER,
                    reference_text TEXT NOT NULL,
                    commentary_text TEXT NOT NULL,
                    commentary_type TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                ''')

                # Индекс для быстрого поиска сохраненных толкований пользователя
                await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_saved_commentaries_user_id 
                ON saved_commentaries(user_id)
                ''')

                # Индекс для быстрого поиска сохраненных толкований по ссылке
                await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_saved_commentaries_reference 
                ON saved_commentaries(user_id, book_id, chapter_start, chapter_end, verse_start, verse_end, commentary_type)
                ''')

                # Таблица библейских тем
                await conn.execute('''
                CREATE TABLE IF NOT EXISTS bible_topics (
                    id SERIAL PRIMARY KEY,
                    topic_name TEXT NOT NULL UNIQUE,
                    verses TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                ''')

                # Индекс для быстрого поиска библейских тем
                await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_bible_topics_name ON bible_topics(topic_name)
                ''')

                # Индекс для полнотекстового поиска библейских тем
                await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_bible_topics_fts ON bible_topics USING gin(to_tsvector('russian', topic_name))
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
        """Получает количество использований ИИ за указанную дату"""
        if date is None:
            date = datetime.now().date()

        try:
            query = """
                SELECT daily_usage FROM ai_limits 
                WHERE user_id = $1 AND date = $2
            """
            result = await self.pool.fetchval(query, user_id, date)
            return result if result is not None else 0
        except Exception as e:
            logger.error(f"Ошибка получения использования ИИ: {e}")
            return 0

    async def get_reading_progress(self, user_id: int, plan_id: str) -> List[int]:
        """Получает список завершенных дней для плана чтения"""
        try:
            query = """
                SELECT day_number FROM reading_progress 
                WHERE user_id = $1 AND plan_id = $2 AND completed = TRUE
                ORDER BY day_number
            """
            rows = await self.pool.fetch(query, user_id, plan_id)
            return [row['day_number'] for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения прогресса чтения: {e}")
            return []

    async def is_reading_day_completed(self, user_id: int, plan_id: str, day: int) -> bool:
        """Проверяет, завершен ли день плана чтения"""
        try:
            query = """
                SELECT completed FROM reading_progress 
                WHERE user_id = $1 AND plan_id = $2 AND day_number = $3
            """
            result = await self.pool.fetchval(query, user_id, plan_id, day)
            return result is True
        except Exception as e:
            logger.error(f"Ошибка проверки завершения дня: {e}")
            return False

    async def is_reading_part_completed(self, user_id: int, plan_id: str, day: int, part_idx: int) -> bool:
        """Проверяет, отмечена ли часть дня как прочитанная"""
        try:
            query = """
                SELECT completed FROM reading_parts_progress 
                WHERE user_id = $1 AND plan_id = $2 AND day_number = $3 AND part_index = $4
            """
            result = await self.pool.fetchval(query, user_id, plan_id, day, part_idx)
            return result is True
        except Exception as e:
            logger.error(f"Ошибка проверки завершения части дня: {e}")
            return False

    async def get_reading_part_progress(self, user_id: int, plan_id: str, day: int) -> List[int]:
        """Получает список завершенных частей дня"""
        try:
            query = """
                SELECT part_index FROM reading_parts_progress 
                WHERE user_id = $1 AND plan_id = $2 AND day_number = $3 AND completed = TRUE
                ORDER BY part_index
            """
            rows = await self.pool.fetch(query, user_id, plan_id, day)
            return [row['part_index'] for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения прогресса частей: {e}")
            return []

    # Методы для совместимости с handlers
    async def get_user_reading_plan(self, user_id: int, plan_id: str) -> Optional[Dict]:
        """Получает план чтения пользователя"""
        try:
            query = """
                SELECT rp.*, up.current_day, up.started_at
                FROM reading_plans rp
                LEFT JOIN user_reading_plans up ON rp.id = up.plan_id AND up.user_id = $1
                WHERE rp.id = $2
            """
            row = await self.pool.fetchrow(query, user_id, plan_id)
            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"Ошибка получения плана пользователя: {e}")
            return None

    async def set_user_reading_plan(self, user_id: int, plan_id: str, day: int = 1) -> bool:
        """Устанавливает план чтения для пользователя"""
        try:
            query = """
                INSERT INTO user_reading_plans (user_id, plan_id, current_day, started_at)
                VALUES ($1, $2, $3, NOW())
                ON CONFLICT (user_id, plan_id) DO UPDATE SET 
                    current_day = $3, 
                    updated_at = NOW()
            """
            await self.pool.execute(query, user_id, plan_id, day)
            return True
        except Exception as e:
            logger.error(f"Ошибка установки плана пользователя: {e}")
            return False

    async def get_user_reading_plans(self, user_id: int) -> List[Dict]:
        """Получает все планы чтения пользователя"""
        try:
            query = """
                SELECT rp.*, up.current_day, up.started_at
                FROM user_reading_plans up
                JOIN reading_plans rp ON up.plan_id = rp.id
                WHERE up.user_id = $1
                ORDER BY up.started_at DESC
            """
            rows = await self.pool.fetch(query, user_id)
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения планов пользователя: {e}")
            return []

    async def update_reading_plan_day(self, user_id: int, plan_id: str, day: int) -> bool:
        """Обновляет текущий день плана чтения"""
        try:
            query = """
                UPDATE user_reading_plans 
                SET current_day = $3, updated_at = NOW()
                WHERE user_id = $1 AND plan_id = $2
            """
            await self.pool.execute(query, user_id, plan_id, day)
            return True
        except Exception as e:
            logger.error(f"Ошибка обновления дня плана: {e}")
            return False

    async def is_bookmark_exists(self, user_id: int, reference: str) -> bool:
        """Проверяет существование закладки по ссылке"""
        try:
            # Парсим reference вида "book_id:chapter"
            if ':' in reference:
                book_id, chapter = reference.split(':')
                book_id, chapter = int(book_id), int(chapter)
            else:
                return False

            query = """
                SELECT 1 FROM bookmarks 
                WHERE user_id = $1 AND book_id = $2 AND chapter = $3
                LIMIT 1
            """
            result = await self.pool.fetchval(query, user_id, book_id, chapter)
            return result is not None
        except Exception as e:
            logger.error(f"Ошибка проверки закладки: {e}")
            return False

    # Алиасы для совместимости
    async def get_reading_progress_async(self, user_id: int, plan_id: str) -> List[int]:
        """Алиас для get_reading_progress"""
        return await self.get_reading_progress(user_id, plan_id)

    async def is_reading_day_completed_async(self, user_id: int, plan_id: str, day: int) -> bool:
        """Алиас для is_reading_day_completed"""
        return await self.is_reading_day_completed(user_id, plan_id, day)

    async def mark_reading_day_completed_async(self, user_id: int, plan_id: str, day: int) -> bool:
        """Алиас для mark_reading_day_completed"""
        return await self.mark_reading_day_completed(user_id, plan_id, day)

    # AI Limits методы
    async def get_ai_limit(self, user_id: int, date: str) -> int:
        """Возвращает количество ИИ-запросов пользователя за дату (строка YYYY-MM-DD)"""
        try:
            query = """
                SELECT count FROM ai_limits 
                WHERE user_id = $1 AND date = $2
            """
            result = await self.pool.fetchval(query, user_id, date)
            return result if result is not None else 0
        except Exception as e:
            logger.error(f"Ошибка получения AI лимита: {e}")
            return 0

    async def increment_ai_limit(self, user_id: int, date: str) -> int:
        """Увеличивает счетчик ИИ-запросов пользователя за дату, возвращает новое значение"""
        try:
            # Используем UPSERT для атомарной операции
            query = """
                INSERT INTO ai_limits (user_id, date, count) 
                VALUES ($1, $2, 1)
                ON CONFLICT (user_id, date) 
                DO UPDATE SET count = ai_limits.count + 1
                RETURNING count
            """
            result = await self.pool.fetchval(query, user_id, date)
            return result if result is not None else 1
        except Exception as e:
            logger.error(f"Ошибка увеличения AI лимита: {e}")
            return 0

    async def reset_ai_limit(self, user_id: int, date: str) -> None:
        """Сбросить лимит ИИ-запросов пользователя за дату (удаляет запись)"""
        try:
            query = """
                DELETE FROM ai_limits 
                WHERE user_id = $1 AND date = $2
            """
            await self.pool.execute(query, user_id, date)
        except Exception as e:
            logger.error(f"Ошибка сброса AI лимита: {e}")

    async def get_ai_stats(self, date: str, limit: int = 10) -> list:
        """Топ пользователей по ИИ-запросам за дату (user_id, count)"""
        try:
            query = """
                SELECT user_id, count FROM ai_limits 
                WHERE date = $1 
                ORDER BY count DESC 
                LIMIT $2
            """
            rows = await self.pool.fetch(query, date, limit)
            return [(row['user_id'], row['count']) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения AI статистики: {e}")
            return []

    async def get_ai_stats_alltime(self, limit: int = 10) -> list:
        """Топ пользователей по ИИ-запросам за всё время (user_id, total_count)"""

        try:
            query = """
                SELECT user_id, SUM(count) as total
                FROM ai_limits
                GROUP BY user_id
                ORDER BY total DESC
                LIMIT $1
            """
            rows = await self.pool.fetch(query, limit)
            return [(row['user_id'], row['total']) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения общей AI статистики: {e}")
            return []

    # Методы для сохраненных толкований
    async def save_commentary(self, user_id: int, book_id: int, chapter_start: int,
                              chapter_end: int = None, verse_start: int = None, verse_end: int = None,
                              reference_text: str = "", commentary_text: str = "",
                              commentary_type: str = "ai") -> bool:
        """Сохраняет толкование для пользователя"""
        try:
            # Проверяем, есть ли уже толкование для этой ссылки
            check_query = """
                SELECT id FROM saved_commentaries 
                WHERE user_id = $1 AND book_id = $2 AND chapter_start = $3 
                AND chapter_end IS NOT DISTINCT FROM $4
                AND verse_start IS NOT DISTINCT FROM $5 
                AND verse_end IS NOT DISTINCT FROM $6
                AND commentary_type = $7
            """
            existing = await self.pool.fetchrow(
                check_query, user_id, book_id, chapter_start, chapter_end,
                verse_start, verse_end, commentary_type
            )

            if existing:
                # Обновляем существующее
                update_query = """
                    UPDATE saved_commentaries 
                    SET reference_text = $1, commentary_text = $2, updated_at = NOW()
                    WHERE id = $3
                """
                await self.pool.execute(update_query, reference_text, commentary_text, existing['id'])
            else:
                # Создаем новое
                insert_query = """
                    INSERT INTO saved_commentaries 
                    (user_id, book_id, chapter_start, chapter_end, verse_start, verse_end,
                     reference_text, commentary_text, commentary_type)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """
                await self.pool.execute(
                    insert_query, user_id, book_id, chapter_start, chapter_end,
                    verse_start, verse_end, reference_text, commentary_text, commentary_type
                )

            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения толкования: {e}")
            return False

    async def get_saved_commentary(self, user_id: int, book_id: int, chapter_start: int,
                                   chapter_end: int = None, verse_start: int = None, verse_end: int = None,
                                   commentary_type: str = "ai") -> Optional[str]:
        """Получает сохраненное толкование"""
        try:
            query = """
                SELECT commentary_text FROM saved_commentaries 
                WHERE user_id = $1 AND book_id = $2 AND chapter_start = $3 
                AND chapter_end IS NOT DISTINCT FROM $4
                AND verse_start IS NOT DISTINCT FROM $5 
                AND verse_end IS NOT DISTINCT FROM $6
                AND commentary_type = $7
            """
            result = await self.pool.fetchval(
                query, user_id, book_id, chapter_start, chapter_end,
                verse_start, verse_end, commentary_type
            )
            return result
        except Exception as e:
            logger.error(f"Ошибка получения сохраненного толкования: {e}")
            return None

    async def delete_saved_commentary(self, user_id: int, book_id: int, chapter_start: int,
                                      chapter_end: int = None, verse_start: int = None, verse_end: int = None,
                                      commentary_type: str = "ai") -> bool:
        """Удаляет сохраненное толкование"""
        try:
            query = """
                DELETE FROM saved_commentaries 
                WHERE user_id = $1 AND book_id = $2 AND chapter_start = $3 
                AND chapter_end IS NOT DISTINCT FROM $4
                AND verse_start IS NOT DISTINCT FROM $5 
                AND verse_end IS NOT DISTINCT FROM $6
                AND commentary_type = $7
            """
            await self.pool.execute(
                query, user_id, book_id, chapter_start, chapter_end,
                verse_start, verse_end, commentary_type
            )
            return True
        except Exception as e:
            logger.error(f"Ошибка удаления толкования: {e}")
            return False

    async def get_user_commentaries(self, user_id: int, limit: int = 50) -> list:
        """Получает последние сохраненные толкования пользователя"""
        try:
            query = """
                SELECT reference_text, commentary_text, commentary_type, created_at
                FROM saved_commentaries 
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT $2
            """
            rows = await self.pool.fetch(query, user_id, limit)
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения толкований пользователя: {e}")
            return []

    # Методы для библейских тем
    async def get_bible_topics(self, search_query: str = "", limit: int = 50) -> list:
        """Получает список библейских тем с возможностью поиска"""
        try:
            if search_query:
                query = """
                    SELECT id, topic_name, verses 
                    FROM bible_topics 
                    WHERE topic_name ILIKE $1
                    ORDER BY topic_name
                    LIMIT $2
                """
                rows = await self.pool.fetch(query, f'%{search_query}%', limit)
            else:
                query = """
                    SELECT id, topic_name, verses 
                    FROM bible_topics 
                    ORDER BY topic_name
                    LIMIT $1
                """
                rows = await self.pool.fetch(query, limit)

            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения тем: {e}")
            return []

    async def get_topic_by_name(self, topic_name: str) -> dict:
        """Получает тему по точному названию"""
        try:
            query = """
                SELECT id, topic_name, verses 
                FROM bible_topics 
                WHERE topic_name = $1
            """
            row = await self.pool.fetchrow(query, topic_name)
            return dict(row) if row else {}
        except Exception as e:
            logger.error(f"Ошибка получения темы '{topic_name}': {e}")
            return {}

    async def get_topic_by_id(self, topic_id: int) -> dict:
        """Получает тему по ID"""
        try:
            query = """
                SELECT id, topic_name, verses 
                FROM bible_topics 
                WHERE id = $1
            """
            row = await self.pool.fetchrow(query, topic_id)
            return dict(row) if row else {}
        except Exception as e:
            logger.error(f"Ошибка получения темы по ID {topic_id}: {e}")
            return {}

    async def search_topics_fulltext(self, search_query: str, limit: int = 20) -> list:
        """Полнотекстовый поиск по темам (PostgreSQL FTS)"""
        try:
            query = """
                SELECT id, topic_name, verses,
                       ts_rank(to_tsvector('russian', topic_name), plainto_tsquery('russian', $1)) as rank
                FROM bible_topics 
                WHERE to_tsvector('russian', topic_name) @@ plainto_tsquery('russian', $1)
                ORDER BY rank DESC, topic_name
                LIMIT $2
            """
            rows = await self.pool.fetch(query, search_query, limit)
            return [dict(row) for row in rows]
        except Exception as e:
            logger.warning(f"Ошибка FTS поиска, переходим к обычному: {e}")
            # Fallback к обычному поиску
            return await self.get_bible_topics(search_query, limit)

    async def get_topics_count(self) -> int:
        """Получает общее количество тем"""
        try:
            query = "SELECT COUNT(*) FROM bible_topics"
            result = await self.pool.fetchval(query)
            return result if result is not None else 0
        except Exception as e:
            logger.error(f"Ошибка получения количества тем: {e}")
            return 0

    async def add_bible_topic(self, topic_name: str, verses: str) -> bool:
        """Добавляет новую библейскую тему"""
        try:
            query = """
                INSERT INTO bible_topics (topic_name, verses)
                VALUES ($1, $2)
                RETURNING id
            """
            result = await self.pool.fetchval(query, topic_name, verses)
            return result is not None
        except Exception as e:
            logger.error(f"Ошибка добавления темы '{topic_name}': {e}")
            return False

    async def update_bible_topic(self, topic_id: int, topic_name: str = None, verses: str = None) -> bool:
        """Обновляет существующую библейскую тему"""
        try:
            updates = []
            params = []
            param_count = 1

            if topic_name is not None:
                updates.append(f"topic_name = ${param_count}")
                params.append(topic_name)
                param_count += 1

            if verses is not None:
                updates.append(f"verses = ${param_count}")
                params.append(verses)
                param_count += 1

            if not updates:
                return False

            updates.append(f"updated_at = ${param_count}")
            params.append(datetime.now())
            param_count += 1

            params.append(topic_id)  # для WHERE

            query = f"""
                UPDATE bible_topics 
                SET {', '.join(updates)}
                WHERE id = ${param_count}
                RETURNING id
            """

            result = await self.pool.fetchval(query, *params)
            return result is not None

        except Exception as e:
            logger.error(f"Ошибка обновления темы ID {topic_id}: {e}")
            return False

    async def delete_bible_topic(self, topic_id: int) -> bool:
        """Удаляет библейскую тему"""
        try:
            query = "DELETE FROM bible_topics WHERE id = $1 RETURNING id"
            result = await self.pool.fetchval(query, topic_id)
            return result is not None
        except Exception as e:
            logger.error(f"Ошибка удаления темы ID {topic_id}: {e}")
            return False


# Создаем глобальный экземпляр
postgres_manager = PostgreSQLManager()
