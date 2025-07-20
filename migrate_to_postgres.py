#!/usr/bin/env python3
"""
Скрипт миграции данных из SQLite в PostgreSQL.
Переносит все пользовательские данные и планы чтения.
"""
from database.db_manager import DatabaseManager
from database.postgres_manager import PostgreSQLManager
import asyncio
import sqlite3
import csv
import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Добавляем текущую директорию в PYTHONPATH
sys.path.insert(0, '.')


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('migration.log')
    ]
)
logger = logging.getLogger(__name__)


class DataMigrator:
    """Класс для миграции данных из SQLite в PostgreSQL"""

    def __init__(self, sqlite_db_path: str = 'data/bible_bot.db',
                 plans_csv_dir: str = 'data/plans_csv_final'):
        self.sqlite_db_path = sqlite_db_path
        self.plans_csv_dir = plans_csv_dir
        self.postgres_manager = PostgreSQLManager()
        self.sqlite_manager = DatabaseManager(sqlite_db_path)

    async def migrate_all(self):
        """Выполняет полную миграцию всех данных"""
        try:
            logger.info("🚀 Начинаем миграцию данных в PostgreSQL")

            # Инициализируем PostgreSQL
            await self.postgres_manager.initialize()
            logger.info("✅ PostgreSQL инициализирован")

            # Миграция пользователей
            await self.migrate_users()

            # Миграция закладок
            await self.migrate_bookmarks()

            # Миграция лимитов ИИ
            await self.migrate_ai_limits()

            # Миграция планов чтения из CSV
            await self.migrate_reading_plans()

            # Миграция прогресса чтения
            await self.migrate_reading_progress()

            logger.info("🎉 Миграция успешно завершена!")

        except Exception as e:
            logger.error(f"❌ Ошибка миграции: {e}", exc_info=True)
            raise
        finally:
            await self.postgres_manager.close()

    async def migrate_users(self):
        """Мигрирует пользователей"""
        logger.info("📤 Миграция пользователей...")

        if not os.path.exists(self.sqlite_db_path):
            logger.warning(f"SQLite база не найдена: {self.sqlite_db_path}")
            return

        conn = sqlite3.connect(self.sqlite_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM users")
            users = cursor.fetchall()

            migrated_count = 0
            for user in users:
                await self.postgres_manager.add_user(
                    user_id=user['user_id'],
                    username=user['username'] or '',
                    first_name=user['first_name'] or ''
                )

                # Обновляем перевод если он отличается от default
                if user['current_translation'] and user['current_translation'] != 'rst':
                    async with self.postgres_manager.pool.acquire() as pg_conn:
                        await pg_conn.execute(
                            "UPDATE users SET current_translation = $1 WHERE user_id = $2",
                            user['current_translation'], user['user_id']
                        )

                migrated_count += 1

            logger.info(f"✅ Мигрировано пользователей: {migrated_count}")

        except Exception as e:
            logger.error(f"Ошибка миграции пользователей: {e}")
        finally:
            conn.close()

    async def migrate_bookmarks(self):
        """Мигрирует закладки"""
        logger.info("📤 Миграция закладок...")

        if not os.path.exists(self.sqlite_db_path):
            logger.warning(f"SQLite база не найдена: {self.sqlite_db_path}")
            return

        conn = sqlite3.connect(self.sqlite_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM bookmarks ORDER BY created_at")
            bookmarks = cursor.fetchall()

            migrated_count = 0
            for bookmark in bookmarks:
                await self.postgres_manager.add_bookmark(
                    user_id=bookmark['user_id'],
                    book_id=bookmark['book_id'],
                    chapter=bookmark['chapter'],
                    display_text=bookmark['display_text'] or '',
                    verse_start=None,
                    verse_end=None,
                    note=None
                )
                migrated_count += 1

            logger.info(f"✅ Мигрировано закладок: {migrated_count}")

        except Exception as e:
            logger.error(f"Ошибка миграции закладок: {e}")
        finally:
            conn.close()

    async def migrate_ai_limits(self):
        """Мигрирует лимиты ИИ"""
        logger.info("📤 Миграция лимитов ИИ...")

        if not os.path.exists(self.sqlite_db_path):
            logger.warning(f"SQLite база не найдена: {self.sqlite_db_path}")
            return

        conn = sqlite3.connect(self.sqlite_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM ai_limits")
            limits = cursor.fetchall()

            migrated_count = 0
            for limit in limits:
                # Парсим дату из строки
                date_str = limit['date']
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                except:
                    # Если формат даты другой, пропускаем
                    continue

                async with self.postgres_manager.pool.acquire() as pg_conn:
                    await pg_conn.execute('''
                        INSERT INTO ai_limits (user_id, date, count)
                        VALUES ($1, $2, $3)
                        ON CONFLICT (user_id, date) DO UPDATE SET
                            count = EXCLUDED.count
                    ''', limit['user_id'], date_obj, limit['count'])

                migrated_count += 1

            logger.info(f"✅ Мигрировано лимитов ИИ: {migrated_count}")

        except Exception as e:
            logger.error(f"Ошибка миграции лимитов ИИ: {e}")
        finally:
            conn.close()

    async def migrate_reading_plans(self):
        """Мигрирует планы чтения из CSV файлов"""
        logger.info("📤 Миграция планов чтения из CSV...")

        if not os.path.exists(self.plans_csv_dir):
            logger.warning(f"Папка с планами не найдена: {self.plans_csv_dir}")
            return

        migrated_plans = 0
        total_days = 0

        for filename in os.listdir(self.plans_csv_dir):
            if not filename.endswith('.csv'):
                continue

            plan_path = os.path.join(self.plans_csv_dir, filename)
            plan_id = filename.replace('.csv', '')

            logger.info(f"📖 Обрабатываем план: {plan_id}")

            try:
                with open(plan_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)

                    if not rows:
                        continue

                    # Первая строка содержит заголовок плана
                    plan_title = rows[0].get('plan_title', plan_id)

                    # Добавляем план
                    await self.postgres_manager.add_reading_plan(
                        plan_id=plan_id,
                        title=plan_title,
                        description=f"План чтения импортирован из {filename}"
                    )

                    # Добавляем дни плана
                    day_count = 0
                    for row in rows:
                        if 'day' in row and 'reading' in row:
                            try:
                                day_number = int(row['day'])
                                reading_text = row['reading']

                                await self.postgres_manager.add_reading_plan_day(
                                    plan_id=plan_id,
                                    day_number=day_number,
                                    reading_text=reading_text
                                )
                                day_count += 1
                                total_days += 1

                            except ValueError:
                                # Пропускаем строки с некорректным номером дня
                                continue

                    logger.info(f"✅ План {plan_id}: {day_count} дней")
                    migrated_plans += 1

            except Exception as e:
                logger.error(f"Ошибка обработки плана {filename}: {e}")

        logger.info(
            f"✅ Мигрировано планов: {migrated_plans}, всего дней: {total_days}")

    async def migrate_reading_progress(self):
        """Мигрирует прогресс чтения"""
        logger.info("📤 Миграция прогресса чтения...")

        if not os.path.exists(self.sqlite_db_path):
            logger.warning(f"SQLite база не найдена: {self.sqlite_db_path}")
            return

        conn = sqlite3.connect(self.sqlite_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # Миграция прогресса по дням
            cursor.execute("SELECT * FROM reading_progress")
            progress_days = cursor.fetchall()

            migrated_days = 0
            for progress in progress_days:
                if progress['completed']:
                    completed_at = None
                    if progress['completed_at']:
                        try:
                            completed_at = datetime.fromisoformat(
                                progress['completed_at'])
                        except:
                            completed_at = datetime.now()

                    async with self.postgres_manager.pool.acquire() as pg_conn:
                        await pg_conn.execute('''
                            INSERT INTO reading_progress (user_id, plan_id, day_number, completed, completed_at)
                            VALUES ($1, $2, $3, $4, $5)
                            ON CONFLICT (user_id, plan_id, day_number) DO UPDATE SET
                                completed = EXCLUDED.completed,
                                completed_at = EXCLUDED.completed_at
                        ''', progress['user_id'], progress['plan_id'],
                            progress['day'], True, completed_at)

                    migrated_days += 1

            # Миграция прогресса по частям дня
            cursor.execute("SELECT * FROM reading_parts_progress")
            progress_parts = cursor.fetchall()

            migrated_parts = 0
            for progress in progress_parts:
                if progress['completed']:
                    completed_at = None
                    if progress['completed_at']:
                        try:
                            completed_at = datetime.fromisoformat(
                                progress['completed_at'])
                        except:
                            completed_at = datetime.now()

                    async with self.postgres_manager.pool.acquire() as pg_conn:
                        await pg_conn.execute('''
                            INSERT INTO reading_parts_progress (user_id, plan_id, day_number, part_idx, completed, completed_at)
                            VALUES ($1, $2, $3, $4, $5, $6)
                            ON CONFLICT (user_id, plan_id, day_number, part_idx) DO UPDATE SET
                                completed = EXCLUDED.completed,
                                completed_at = EXCLUDED.completed_at
                        ''', progress['user_id'], progress['plan_id'],
                            progress['day'], progress['part_idx'], True, completed_at)

                    migrated_parts += 1

            logger.info(
                f"✅ Мигрировано прогресса дней: {migrated_days}, частей: {migrated_parts}")

        except Exception as e:
            logger.error(f"Ошибка миграции прогресса: {e}")
        finally:
            conn.close()


async def main():
    """Главная функция миграции"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Миграция данных из SQLite в PostgreSQL')
    parser.add_argument('--sqlite-db', default='data/bible_bot.db',
                        help='Путь к SQLite базе данных')
    parser.add_argument('--plans-csv', default='data/plans_csv_final',
                        help='Путь к папке с CSV планами чтения')
    parser.add_argument('--postgres-host', default=None,
                        help='Хост PostgreSQL (или POSTGRES_HOST env)')
    parser.add_argument('--postgres-port', type=int, default=None,
                        help='Порт PostgreSQL (или POSTGRES_PORT env)')
    parser.add_argument('--postgres-db', default=None,
                        help='Имя базы PostgreSQL (или POSTGRES_DB env)')
    parser.add_argument('--postgres-user', default=None,
                        help='Пользователь PostgreSQL (или POSTGRES_USER env)')
    parser.add_argument('--postgres-password', default=None,
                        help='Пароль PostgreSQL (или POSTGRES_PASSWORD env)')

    args = parser.parse_args()

    # Создаем мигратор с параметрами
    migrator = DataMigrator(
        sqlite_db_path=args.sqlite_db,
        plans_csv_dir=args.plans_csv
    )

    # Обновляем параметры PostgreSQL если переданы
    if args.postgres_host:
        migrator.postgres_manager.host = args.postgres_host
    if args.postgres_port:
        migrator.postgres_manager.port = args.postgres_port
    if args.postgres_db:
        migrator.postgres_manager.database = args.postgres_db
    if args.postgres_user:
        migrator.postgres_manager.user = args.postgres_user
    if args.postgres_password:
        migrator.postgres_manager.password = args.postgres_password

    # Выводим параметры подключения
    logger.info(f"🔗 Подключение к PostgreSQL:")
    logger.info(
        f"   Хост: {migrator.postgres_manager.host}:{migrator.postgres_manager.port}")
    logger.info(f"   База: {migrator.postgres_manager.database}")
    logger.info(f"   Пользователь: {migrator.postgres_manager.user}")

    logger.info(f"📂 Источники данных:")
    logger.info(f"   SQLite: {args.sqlite_db}")
    logger.info(f"   CSV планы: {args.plans_csv}")

    # Подтверждение миграции
    confirm = input("\n❓ Продолжить миграцию? (y/N): ")
    if confirm.lower() not in ['y', 'yes', 'да']:
        logger.info("❌ Миграция отменена")
        return

    # Запускаем миграцию
    await migrator.migrate_all()


if __name__ == "__main__":
    asyncio.run(main())
