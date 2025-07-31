"""
Модуль для управления базой данных SQLite.
Отвечает за хранение информации о пользователях и их закладках.
"""
import sqlite3
import logging
import os
import asyncio
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any

# Инициализация логгера
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Класс для управления базой данных SQLite"""

    def __init__(self, db_file: str = 'data/bible_bot.db'):
        """
        Инициализирует менеджер базы данных.

        Args:
            db_file: путь к файлу базы данных
        """
        # Создаем директорию для БД, если её нет
        os.makedirs(os.path.dirname(db_file), exist_ok=True)

        self.db_file = db_file

        # Проверяем существование файла и логируем результат
        db_exists = os.path.exists(db_file)
        if db_exists:
            logger.info(f"Подключение к существующей БД: {db_file}")
            # Проверим, можно ли соединиться с БД
            try:
                conn = sqlite3.connect(db_file)
                conn.close()
                logger.info(f"Соединение с БД успешно установлено")
            except Exception as e:
                logger.error(f"Ошибка при соединении с БД: {e}", exc_info=True)
        else:
            logger.info(f"Создаем новую БД: {db_file}")

        self._create_tables()
        logger.info(f"База данных инициализирована: {db_file}")

    def _create_tables(self) -> None:
        """Создает необходимые таблицы в базе данных, если они не существуют"""
        conn = None
        try:
            logger.info(
                f"Попытка создания/проверки таблиц в БД: {self.db_file}")

            # Проверяем директорию БД
            db_dir = os.path.dirname(self.db_file)
            os.makedirs(db_dir, exist_ok=True)

            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            # Таблица пользователей
            logger.info("Создание/проверка таблицы users")
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                current_translation TEXT DEFAULT 'rst',
                response_length TEXT DEFAULT 'full',
                last_activity TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            # Добавляем поле response_length, если его еще нет (миграция)
            try:
                cursor.execute(
                    "ALTER TABLE users ADD COLUMN response_length TEXT DEFAULT 'full'")
                logger.info("Добавлено поле response_length в таблицу users")
            except sqlite3.OperationalError:
                # Поле уже существует
                pass

            # Таблица закладок
            logger.info("Создание/проверка таблицы bookmarks")
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookmarks (
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

            # Таблица лимитов ИИ
            logger.info("Создание/проверка таблицы ai_limits")
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_limits (
                user_id INTEGER,
                date TEXT,
                count INTEGER,
                PRIMARY KEY (user_id, date)
            )
            ''')

            # Таблица сохраненных комментариев
            logger.info("Создание/проверка таблицы saved_commentaries")
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS saved_commentaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                book_id INTEGER NOT NULL,
                chapter_start INTEGER NOT NULL,
                chapter_end INTEGER,
                verse_start INTEGER,
                verse_end INTEGER,
                reference_text TEXT NOT NULL,
                commentary_text TEXT NOT NULL,
                commentary_type TEXT DEFAULT 'ai',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            ''')

            # Таблица прогресса чтения
            logger.info("Создание/проверка таблицы reading_progress")
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS reading_progress (
                user_id INTEGER,
                plan_id TEXT,
                day INTEGER,
                completed INTEGER DEFAULT 0,
                completed_at TIMESTAMP,
                PRIMARY KEY (user_id, plan_id, day)
            )
            ''')

            # Таблица прогресса чтения частей дня
            logger.info("Создание/проверка таблицы reading_parts_progress")
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS reading_parts_progress (
                user_id INTEGER,
                plan_id TEXT,
                day INTEGER,
                part_idx INTEGER,
                completed INTEGER DEFAULT 0,
                completed_at TIMESTAMP,
                PRIMARY KEY (user_id, plan_id, day, part_idx)
            )
            ''')

            # Проверяем, созданы ли таблицы
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND (name='users' OR name='bookmarks' OR name='ai_limits' OR name='reading_progress' OR name='reading_parts_progress')")
            tables = cursor.fetchall()
            logger.info(f"Проверка созданных таблиц: {tables}")

            # Выполняем дополнительную проверку таблицы bookmarks
            try:
                cursor.execute("PRAGMA table_info(bookmarks)")
                columns = cursor.fetchall()
                logger.info(f"Колонки таблицы bookmarks: {columns}")
            except Exception as e:
                logger.error(
                    f"Ошибка при проверке колонок таблицы bookmarks: {e}")

            conn.commit()
            logger.info("Транзакция создания таблиц подтверждена (commit)")

            # Проверим, что таблицы действительно созданы
            cursor.execute(
                "SELECT COUNT(name) FROM sqlite_master WHERE type='table' AND (name='users' OR name='bookmarks' OR name='ai_limits' OR name='reading_progress' OR name='reading_parts_progress')")
            table_count = cursor.fetchone()[0]
            if table_count == 5:
                logger.info(
                    "Все таблицы (users, bookmarks, ai_limits, reading_progress и reading_parts_progress) успешно созданы")
            else:
                logger.warning(
                    f"Не все таблицы созданы. Найдено таблиц: {table_count}/5")

        except Exception as e:
            logger.error(
                f"Ошибка при создании таблиц в БД: {e}", exc_info=True)
            if conn:
                try:
                    conn.rollback()
                    logger.info("Выполнен откат транзакции после ошибки")
                except:
                    pass
        finally:
            if conn:
                conn.close()
                logger.debug("Соединение с БД закрыто после создания таблиц")

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Получает информацию о пользователе из БД.

        Args:
            user_id: ID пользователя Telegram

        Returns:
            Словарь с данными пользователя или None, если пользователь не найден
        """
        # Выполняем SQL-запрос в отдельном потоке через ThreadPoolExecutor
        def _execute():
            conn = sqlite3.connect(self.db_file)
            conn.row_factory = sqlite3.Row  # Для получения результатов в виде словаря
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = cursor.fetchone()
            conn.close()
            return dict(user) if user else None

        return await asyncio.to_thread(_execute)

    async def add_user(self, user_id: int, username: str, first_name: str) -> None:
        """
        Добавляет нового пользователя или обновляет существующего.

        Args:
            user_id: ID пользователя Telegram
            username: Имя пользователя
            first_name: Имя пользователя
        """
        logger.info(
            f"Попытка добавления/обновления пользователя: {user_id} ({username})")

        def _execute():
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            now = datetime.now()

            # Проверяем, существует ли пользователь
            cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
            exists = cursor.fetchone()

            if exists:
                # Обновляем существующего пользователя
                logger.info(
                    f"Обновление существующего пользователя: {user_id}")
                cursor.execute(
                    """
                    UPDATE users SET
                    username = ?,
                    first_name = ?,
                    last_activity = ?
                    WHERE user_id = ?
                    """,
                    (username, first_name, now, user_id)
                )
            else:
                # Добавляем нового пользователя
                logger.info(f"Добавление нового пользователя: {user_id}")
                cursor.execute(
                    """
                    INSERT INTO users (user_id, username, first_name, last_activity)
                    VALUES (?, ?, ?, ?)
                    """,
                    (user_id, username, first_name, now)
                )

            # Проверяем количество записей в таблице после добавления/обновления
            cursor.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            logger.info(
                f"Количество пользователей в БД после операции: {count}")

            conn.commit()
            conn.close()

        try:
            await asyncio.to_thread(_execute)
            logger.info(f"Пользователь успешно добавлен/обновлен: {user_id}")
        except Exception as e:
            logger.error(
                f"Ошибка при добавлении/обновлении пользователя {user_id}: {e}", exc_info=True)

    async def update_user_translation(self, user_id: int, translation: str) -> None:
        """
        Обновляет предпочитаемый перевод Библии пользователя.

        Args:
            user_id: ID пользователя Telegram
            translation: Код перевода (rst, rbo)
        """
        def _execute():
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET current_translation = ? WHERE user_id = ?",
                (translation, user_id)
            )
            conn.commit()
            conn.close()

        await asyncio.to_thread(_execute)
        logger.debug(
            f"Обновлен перевод для пользователя {user_id}: {translation}")

    async def get_user_translation(self, user_id: int) -> str:
        """
        Получает предпочитаемый перевод Библии пользователя.

        Args:
            user_id: ID пользователя Telegram

        Returns:
            Код перевода (по умолчанию 'rst')
        """
        def _execute():
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT current_translation FROM users WHERE user_id = ?",
                (user_id,)
            )
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else 'rst'

        return await asyncio.to_thread(_execute)

    async def update_user_response_length(self, user_id: int, response_length: str) -> None:
        """
        Обновляет настройку длины ответа ИИ пользователя.

        Args:
            user_id: ID пользователя Telegram
            response_length: Тип ответа ('short' или 'full')
        """
        def _execute():
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET response_length = ? WHERE user_id = ?",
                (response_length, user_id)
            )
            conn.commit()
            conn.close()

        await asyncio.to_thread(_execute)
        logger.debug(
            f"Обновлена настройка длины ответа для пользователя {user_id}: {response_length}")

    async def get_user_response_length(self, user_id: int) -> str:
        """
        Получает настройку длины ответа ИИ пользователя.

        Args:
            user_id: ID пользователя Telegram

        Returns:
            Тип ответа ('short' или 'full', по умолчанию 'full')
        """
        def _execute():
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT response_length FROM users WHERE user_id = ?",
                (user_id,)
            )
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else 'full'

        return await asyncio.to_thread(_execute)

    async def add_bookmark(self, user_id: int, book_id: int, chapter_start: int,
                           chapter_end: int = None, verse_start: int = None,
                           verse_end: int = None, display_text: str = None, note: str = None) -> bool:
        """
        Добавляет закладку для пользователя.

        Args:
            user_id: ID пользователя Telegram
            book_id: ID книги Библии
            chapter: Номер главы
            display_text: Отображаемый текст закладки

        Returns:
            True если закладка успешно добавлена, False в противном случае
        """
        logger.info(
            f"Попытка добавления закладки: {user_id} - {display_text} (book_id={book_id}, chapter_start={chapter_start})")

        # Проверяем, существует ли директория для БД
        db_dir = os.path.dirname(self.db_file)
        if not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir, exist_ok=True)
                logger.info(f"Создана директория для БД: {db_dir}")
            except Exception as e:
                logger.error(f"Ошибка при создании директории для БД: {e}")
                return False

        # Проверяем права доступа к файлу БД
        if os.path.exists(self.db_file):
            try:
                # Пробуем открыть файл на запись
                with open(self.db_file, 'a') as f:
                    pass
                logger.info("Проверка прав доступа к БД: OK")
            except PermissionError:
                logger.error(
                    f"Нет прав доступа для записи в файл БД: {self.db_file}")
                return False
            except Exception as e:
                logger.error(f"Ошибка при проверке прав доступа к БД: {e}")
                return False

        success = False
        conn = None

        try:
            # Открываем соединение с БД
            logger.info(f"Открываем соединение с БД: {self.db_file}")
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            now = datetime.now()

            # Проверяем, существует ли пользователь, если нет - создаем
            cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
            if not cursor.fetchone():
                logger.info(f"Пользователь {user_id} не найден, создаем")
                cursor.execute(
                    "INSERT INTO users (user_id, last_activity) VALUES (?, ?)",
                    (user_id, now)
                )
                conn.commit()  # Сохраняем изменения для пользователя
                logger.info(f"Пользователь {user_id} создан")

            # Проверяем, существует ли уже такая закладка
            logger.info(
                f"Проверка существующей закладки: {user_id}, {book_id}, {chapter}")
            cursor.execute(
                "SELECT 1 FROM bookmarks WHERE user_id = ? AND book_id = ? AND chapter_start = ? AND chapter_end IS ? AND verse_start IS ? AND verse_end IS ?",
                (user_id, book_id, chapter_start,
                 chapter_end, verse_start, verse_end)
            )
            if cursor.fetchone():
                logger.info(
                    f"Закладка уже существует: {user_id} - {display_text}")
                # Закладка уже существует, считаем успешным
                success = True
            else:
                # Добавляем закладку
                logger.info(
                    f"Добавление новой закладки: {user_id} - {display_text}")
                try:
                    query = "INSERT INTO bookmarks (user_id, book_id, chapter_start, chapter_end, verse_start, verse_end, display_text, note, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
                    logger.info(
                        f"SQL запрос: {query} с параметрами ({user_id}, {book_id}, {chapter_start}, {chapter_end}, {verse_start}, {verse_end}, '{display_text}', '{note}', {now})")
                    cursor.execute(
                        query, (user_id, book_id, chapter_start, chapter_end, verse_start, verse_end, display_text, note, now))

                    # Обязательно делаем commit для сохранения изменений
                    conn.commit()
                    logger.info(
                        f"SQL запрос выполнен, транзакция подтверждена (commit)")

                    # Проверяем, была ли закладка действительно добавлена
                    cursor.execute(
                        "SELECT * FROM bookmarks WHERE user_id = ? AND book_id = ? AND chapter_start = ? AND chapter_end IS ? AND verse_start IS ? AND verse_end IS ?",
                        (user_id, book_id, chapter_start,
                         chapter_end, verse_start, verse_end)
                    )
                    result = cursor.fetchone()
                    if result:
                        logger.info(f"Успешно добавлена закладка: {result}")
                        success = True
                    else:
                        logger.error(f"Закладка не найдена после добавления!")
                        success = False

                except Exception as e:
                    logger.error(
                        f"Ошибка SQL при добавлении закладки: {e}", exc_info=True)
                    conn.rollback()  # Откатываем изменения при ошибке
                    success = False

                # Проверяем количество закладок после добавления
                cursor.execute(
                    "SELECT COUNT(*) FROM bookmarks WHERE user_id = ?", (user_id,))
                count = cursor.fetchone()[0]
                logger.info(
                    f"Количество закладок пользователя {user_id} после операции: {count}")

        except Exception as e:
            logger.error(f"Общая ошибка при работе с БД: {e}", exc_info=True)
            success = False
        finally:
            # Всегда закрываем соединение с БД
            if conn:
                try:
                    conn.close()
                    logger.info(
                        f"Соединение с БД закрыто. Результат операции: {success}")
                except Exception as e:
                    logger.error(f"Ошибка при закрытии соединения с БД: {e}")

        logger.info(
            f"Закладка {'успешно добавлена' if success else 'НЕ добавлена'}: {user_id} - {display_text}")
        return success

    async def get_bookmarks(self, user_id: int) -> List[Tuple[int, int, str]]:
        """
        Получает все закладки пользователя.

        Args:
            user_id: ID пользователя Telegram

        Returns:
            Список кортежей (book_id, chapter, display_text)
        """
        logger.info(f"Запрос закладок для пользователя {user_id}")

        def _execute():
            try:
                # Проверить файл БД
                if not os.path.exists(self.db_file):
                    logger.error(f"Файл БД не существует: {self.db_file}")
                    return []

                logger.info(
                    f"Открываем соединение с БД для получения закладок: {self.db_file}")
                conn = sqlite3.connect(self.db_file)
                cursor = conn.cursor()

                # Проверить наличие таблицы bookmarks
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='bookmarks'")
                if not cursor.fetchone():
                    logger.error("Таблица bookmarks не существует в БД")
                    conn.close()
                    return []

                # Проверим количество закладок у пользователя сначала
                cursor.execute(
                    "SELECT COUNT(*) FROM bookmarks WHERE user_id = ?", (user_id,))
                count = cursor.fetchone()[0]
                logger.info(
                    f"Количество закладок пользователя {user_id} в БД: {count}")

                # Выполняем основной запрос
                logger.info(
                    f"Выполняем SQL запрос на получение закладок для user_id={user_id}")
                cursor.execute(
                    """
                    SELECT book_id, chapter_start, chapter_end, display_text, verse_start, verse_end, note, created_at FROM bookmarks
                    WHERE user_id = ? ORDER BY created_at DESC
                    """,
                    (user_id,)
                )
                bookmarks = cursor.fetchall()
                logger.info(
                    f"Получено {len(bookmarks)} закладок для пользователя {user_id}")

                # Выводим список полученных закладок
                if bookmarks:
                    for i, bm in enumerate(bookmarks):
                        logger.info(
                            f"Закладка {i+1}: book_id={bm[0]}, chapter={bm[1]}, text={bm[2]}")

                conn.close()
                logger.info(
                    f"Соединение с БД закрыто после получения закладок")
                return bookmarks
            except Exception as e:
                logger.error(
                    f"Ошибка при получении закладок из БД: {e}", exc_info=True)
                return []

        try:
            result = await asyncio.to_thread(_execute)

            # Проверяем формат возвращаемых данных
            validated_bookmarks = []
            for bookmark in result:
                # Проверяем, что кортеж содержит ровно 3 элемента
                if len(bookmark) == 3:
                    book_id, chapter, display_text = bookmark
                    validated_bookmarks.append(
                        (book_id, chapter, display_text))
                else:
                    logger.warning(f"Некорректный формат закладки: {bookmark}")

            logger.info(
                f"Валидировано {len(validated_bookmarks)} закладок для пользователя {user_id}")

            return validated_bookmarks
        except Exception as e:
            logger.error(
                f"Ошибка при получении закладок для пользователя {user_id}: {e}", exc_info=True)
            return []

    async def remove_bookmark(self, user_id: int, book_id: int, chapter_start: int,
                              chapter_end: int = None, verse_start: int = None, verse_end: int = None) -> bool:
        """
        Удаляет конкретную закладку пользователя.

        Args:
            user_id: ID пользователя Telegram
            book_id: ID книги Библии
            chapter_start: Начальная глава
            chapter_end: Конечная глава
            verse_start: Начальный стих
            verse_end: Конечный стих

        Returns:
            bool: True если закладка удалена, False если ошибка
        """
        def _execute():
            try:
                conn = sqlite3.connect(self.db_file)
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM bookmarks WHERE user_id = ? AND book_id = ? AND chapter_start = ? AND chapter_end IS ? AND verse_start IS ? AND verse_end IS ?",
                    (user_id, book_id, chapter_start,
                     chapter_end, verse_start, verse_end)
                )
                conn.commit()
                conn.close()
                return True
            except Exception as e:
                logger.error(f"Ошибка при удалении закладки: {e}")
                return False

        result = await asyncio.to_thread(_execute)
        if result:
            logger.debug(
                f"Удалена закладка для пользователя {user_id}: {book_id} {chapter_start}")
        return result

    async def is_bookmarked(self, user_id: int, book_id: int, chapter_start: int,
                            chapter_end: int = None, verse_start: int = None, verse_end: int = None) -> bool:
        """
        Проверяет, есть ли закладка у пользователя.

        Args:
            user_id: ID пользователя Telegram
            book_id: ID книги Библии
            chapter_start: Начальная глава
            chapter_end: Конечная глава
            verse_start: Начальный стих
            verse_end: Конечный стих

        Returns:
            bool: True если закладка существует, False если нет
        """
        def _execute():
            try:
                conn = sqlite3.connect(self.db_file)
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT 1 FROM bookmarks WHERE user_id = ? AND book_id = ? AND chapter_start = ? AND chapter_end IS ? AND verse_start IS ? AND verse_end IS ?",
                    (user_id, book_id, chapter_start,
                     chapter_end, verse_start, verse_end)
                )
                result = cursor.fetchone()
                conn.close()
                return result is not None
            except Exception as e:
                logger.error(f"Ошибка при проверке закладки: {e}")
                return False

        return await asyncio.to_thread(_execute)

    async def clear_bookmarks(self, user_id: int) -> None:
        """
        Удаляет все закладки пользователя.

        Args:
            user_id: ID пользователя Telegram
        """
        def _execute():
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM bookmarks WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()

        await asyncio.to_thread(_execute)
        logger.debug(f"Очищены все закладки для пользователя {user_id}")

    async def close(self) -> None:
        """Закрывает соединения с базой данных (если необходимо)"""
        # SQLite не требует явного закрытия, но метод оставлен для совместимости
        logger.info("Соединение с базой данных закрыто")

    async def check_db_access(self) -> dict:
        """
        Проверяет доступность БД и права доступа к файлам.

        Returns:
            Словарь с результатами проверки
        """
        results = {
            "db_file": self.db_file,
            "errors": [],
            "success": True
        }

        try:
            # Проверяем директорию
            db_dir = os.path.dirname(self.db_file)

            # Проверка 1: Директория существует?
            dir_exists = os.path.exists(db_dir)
            results["dir_exists"] = dir_exists

            if not dir_exists:
                results["errors"].append(f"Директория {db_dir} не существует")
                results["success"] = False
                try:
                    # Пробуем создать директорию
                    os.makedirs(db_dir, exist_ok=True)
                    results["dir_created"] = True
                except Exception as e:
                    results["dir_created"] = False
                    results["errors"].append(
                        f"Ошибка создания директории: {e}")
                    return results

            # Проверка 2: Права на запись в директорию
            try:
                test_file = os.path.join(db_dir, "_test_write.tmp")
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                results["dir_writable"] = True
            except Exception as e:
                results["dir_writable"] = False
                results["errors"].append(
                    f"Нет прав на запись в директорию: {e}")
                results["success"] = False
                return results

            # Проверка 3: БД файл существует?
            file_exists = os.path.exists(self.db_file)
            results["file_exists"] = file_exists

            if file_exists:
                # Проверка 4: Размер файла
                try:
                    size = os.path.getsize(self.db_file)
                    results["file_size"] = size
                    if size == 0:
                        results["errors"].append(
                            "Файл БД имеет нулевой размер")
                except Exception as e:
                    results["errors"].append(
                        f"Ошибка при проверке размера файла: {e}")

                # Проверка 5: Права на запись в файл
                try:
                    with open(self.db_file, 'a') as f:
                        pass
                    results["file_writable"] = True
                except Exception as e:
                    results["file_writable"] = False
                    results["errors"].append(
                        f"Нет прав на запись в файл БД: {e}")
                    results["success"] = False
                    return results

                # Проверка 6: SQLite может открыть файл
                try:
                    conn = sqlite3.connect(self.db_file)
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'")
                    tables = cursor.fetchall()
                    results["tables"] = [t[0] for t in tables]
                    conn.close()
                    results["sqlite_access"] = True
                except Exception as e:
                    results["sqlite_access"] = False
                    results["errors"].append(
                        f"SQLite не может открыть БД: {e}")
                    results["success"] = False
            else:
                # Если файл не существует, проверяем возможность его создания
                try:
                    conn = sqlite3.connect(self.db_file)
                    conn.close()
                    results["can_create_db"] = True
                    # Удаляем пустой файл, если он был создан
                    if os.path.exists(self.db_file) and os.path.getsize(self.db_file) == 0:
                        os.remove(self.db_file)
                except Exception as e:
                    results["can_create_db"] = False
                    results["errors"].append(
                        f"Не удалось создать файл БД: {e}")
                    results["success"] = False

            return results
        except Exception as e:
            results["errors"].append(f"Общая ошибка при проверке БД: {e}")
            results["success"] = False
            return results

    @classmethod
    async def repair_db(cls, db_path=None):
        """
        Пытается восстановить БД, создавая новый файл с таблицами

        Args:
            db_path: путь к БД, если None используется текущий

        Returns:
            Словарь с результатом восстановления
        """
        result = {
            "success": False,
            "errors": [],
            "actions": []
        }

        try:
            if db_path is None:
                db_path = db_manager.db_file

            # Проверяем и создаем бэкап текущей БД
            if os.path.exists(db_path):
                backup_path = f"{db_path}.bak"
                try:
                    import shutil
                    shutil.copy2(db_path, backup_path)
                    result["actions"].append(f"Создан бэкап: {backup_path}")
                except Exception as e:
                    result["errors"].append(f"Не удалось создать бэкап: {e}")

                # Удаляем текущий файл БД
                try:
                    os.remove(db_path)
                    result["actions"].append(
                        f"Удален поврежденный файл: {db_path}")
                except Exception as e:
                    result["errors"].append(f"Не удалось удалить файл БД: {e}")

            # Создаем новую БД с нуля
            db_dir = os.path.dirname(db_path)
            if not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
                result["actions"].append(f"Создана директория: {db_dir}")

            # Создаем новую БД и таблицы
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Создаем таблицы
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                current_translation TEXT DEFAULT 'rst',
                last_activity TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookmarks (
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
            )''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_limits (
                user_id INTEGER,
                date TEXT,
                count INTEGER,
                PRIMARY KEY (user_id, date)
            )''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS saved_commentaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                book_id INTEGER NOT NULL,
                chapter_start INTEGER NOT NULL,
                chapter_end INTEGER,
                verse_start INTEGER,
                verse_end INTEGER,
                reference_text TEXT NOT NULL,
                commentary_text TEXT NOT NULL,
                commentary_type TEXT DEFAULT 'ai',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS reading_progress (
                user_id INTEGER,
                plan_id TEXT,
                day INTEGER,
                completed INTEGER DEFAULT 0,
                completed_at TIMESTAMP,
                PRIMARY KEY (user_id, plan_id, day)
            )''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS reading_parts_progress (
                user_id INTEGER,
                plan_id TEXT,
                day INTEGER,
                part_idx INTEGER,
                completed INTEGER DEFAULT 0,
                completed_at TIMESTAMP,
                PRIMARY KEY (user_id, plan_id, day, part_idx)
            )''')

            conn.commit()
            conn.close()

            result["actions"].append(
                "Созданы новые таблицы users, bookmarks, ai_limits, reading_progress и reading_parts_progress")
            result["success"] = True
            return result

        except Exception as e:
            result["errors"].append(f"Ошибка восстановления БД: {e}")
            return result

    async def get_ai_limit(self, user_id: int, date: str) -> int:
        """Возвращает количество ИИ-запросов пользователя за дату (строка YYYY-MM-DD)"""
        def _execute():
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT count FROM ai_limits WHERE user_id=? AND date=?", (user_id, date))
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else 0
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _execute)

    async def increment_ai_limit(self, user_id: int, date: str) -> int:
        """Увеличивает счетчик ИИ-запросов пользователя за дату, возвращает новое значение"""
        def _execute():
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT count FROM ai_limits WHERE user_id=? AND date=?", (user_id, date))
            row = cursor.fetchone()
            if row:
                new_count = row[0] + 1
                cursor.execute(
                    "UPDATE ai_limits SET count=? WHERE user_id=? AND date=?", (new_count, user_id, date))
            else:
                new_count = 1
                cursor.execute(
                    "INSERT INTO ai_limits (user_id, date, count) VALUES (?, ?, ?)", (user_id, date, 1))
            conn.commit()
            conn.close()
            return new_count
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _execute)

    async def reset_ai_limit(self, user_id: int, date: str) -> None:
        """Сбросить лимит ИИ-запросов пользователя за дату (обнуляет счетчик)"""
        def _execute():
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM ai_limits WHERE user_id=? AND date=?", (user_id, date))
            conn.commit()
            conn.close()
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _execute)

    async def get_ai_stats(self, date: str, limit: int = 10) -> list:
        """Топ пользователей по ИИ-запросам за дату (user_id, count)"""
        def _execute():
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id, count FROM ai_limits WHERE date=? ORDER BY count DESC LIMIT ?", (date, limit))
            rows = cursor.fetchall()
            conn.close()
            return rows
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _execute)

    async def get_ai_stats_alltime(self, limit: int = 10) -> list:
        """Топ пользователей по ИИ-запросам за всё время (user_id, total_count)"""
        def _execute():
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id, SUM(count) as total FROM ai_limits GROUP BY user_id ORDER BY total DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            conn.close()
            return rows
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _execute)

    def mark_reading_day_completed(self, user_id: int, plan_id: str, day: int):
        """Отметить день плана как прочитанный пользователем."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO reading_progress (user_id, plan_id, day, completed, completed_at)
            VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
        ''', (user_id, plan_id, day))
        conn.commit()
        conn.close()

    def is_reading_day_completed(self, user_id: int, plan_id: str, day: int) -> bool:
        """Проверить, отмечен ли день как прочитанный."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT completed FROM reading_progress WHERE user_id=? AND plan_id=? AND day=?
        ''', (user_id, plan_id, day))
        row = cursor.fetchone()
        conn.close()
        return bool(row and row[0])

    def get_reading_progress(self, user_id: int, plan_id: str) -> list:
        """Получить список всех отмеченных дней для пользователя и плана."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT day FROM reading_progress WHERE user_id=? AND plan_id=? AND completed=1
        ''', (user_id, plan_id))
        days = [row[0] for row in cursor.fetchall()]
        conn.close()
        return days

    def _mark_reading_part_completed_sync(self, user_id: int, plan_id: str, day: int, part_idx: int):
        """Отметить часть дня плана как прочитанную пользователем."""
        logger.info(
            f"[DB_SQLITE] Сохраняем прогресс: user_id={user_id}, plan_id={plan_id}, day={day}, part_idx={part_idx}")
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO reading_parts_progress (user_id, plan_id, day, part_idx, completed, completed_at)
            VALUES (?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
        ''', (user_id, plan_id, day, part_idx))
        affected_rows = cursor.rowcount
        conn.commit()
        conn.close()
        logger.info(f"[DB_SQLITE] Затронуто строк: {affected_rows}")

    async def mark_reading_part_completed(self, user_id: int, plan_id: str, day: int, part_idx: int) -> bool:
        """Асинхронный метод для отметки части дня как прочитанной (для совместимости с универсальным менеджером)"""
        try:
            import asyncio
            await asyncio.to_thread(self._mark_reading_part_completed_sync, user_id, plan_id, day, part_idx)
            logger.info(
                f"[DB_SQLITE] Успешно сохранен прогресс: user_id={user_id}, plan_id={plan_id}, day={day}, part_idx={part_idx}")
            return True
        except Exception as e:
            logger.error(
                f"[DB_SQLITE] Ошибка при отметке части дня как прочитанной: {e}")
            return False

    def _is_reading_part_completed_sync_old(self, user_id: int, plan_id: str, day: int, part_idx: int) -> bool:
        """Старая синхронная версия - оставлена для совместимости"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT completed FROM reading_parts_progress WHERE user_id=? AND plan_id=? AND day=? AND part_idx=?
        ''', (user_id, plan_id, day, part_idx))
        row = cursor.fetchone()
        conn.close()
        return bool(row and row[0])

    def get_reading_parts_progress(self, user_id: int, plan_id: str, day: int) -> list:
        """Получить список всех отмеченных частей для пользователя, плана и дня."""
        logger.info(
            f"[DB_SQLITE] Читаем прогресс: user_id={user_id}, plan_id={plan_id}, day={day}")
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT part_idx FROM reading_parts_progress WHERE user_id=? AND plan_id=? AND day=? AND completed=1
        ''', (user_id, plan_id, day))
        parts = [row[0] for row in cursor.fetchall()]
        conn.close()
        logger.info(f"[DB_SQLITE] Найдено завершенных частей: {parts}")
        return parts

    async def get_reading_part_progress(self, user_id: int, plan_id: str, day: int) -> list:
        """Асинхронная версия получения списка отмеченных частей для пользователя, плана и дня."""
        import asyncio
        result = await asyncio.to_thread(self.get_reading_parts_progress, user_id, plan_id, day)
        logger.info(f"[DB_SQLITE] Асинхронно получен прогресс: {result}")
        return result

    def _is_reading_part_completed_sync(self, user_id: int, plan_id: str, day: int, part_idx: int) -> bool:
        """Синхронная версия проверки завершения части дня"""
        logger.info(
            f"[DB_SQLITE] Проверяем статус части: user_id={user_id}, plan_id={plan_id}, day={day}, part_idx={part_idx}")
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT completed FROM reading_parts_progress WHERE user_id=? AND plan_id=? AND day=? AND part_idx=?
        ''', (user_id, plan_id, day, part_idx))
        row = cursor.fetchone()
        conn.close()
        result = bool(row and row[0])
        logger.info(f"[DB_SQLITE] Статус части: {result}")
        return result

    async def is_reading_part_completed(self, user_id: int, plan_id: str, day: int, part_idx: int) -> bool:
        """Асинхронный метод для проверки завершения части дня (для совместимости с универсальным менеджером)"""
        import asyncio
        result = await asyncio.to_thread(self._is_reading_part_completed_sync, user_id, plan_id, day, part_idx)
        logger.info(f"[DB_SQLITE] Асинхронно проверен статус части: {result}")
        return result

    # Методы для сохраненных толкований
    async def save_commentary(self, user_id: int, book_id: int, chapter_start: int,
                              chapter_end: int = None, verse_start: int = None, verse_end: int = None,
                              reference_text: str = "", commentary_text: str = "",
                              commentary_type: str = "ai") -> bool:
        """Сохраняет толкование для пользователя"""
        def _execute():
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            try:
                # Проверяем, есть ли уже комментарий для этой ссылки
                cursor.execute('''
                    SELECT id FROM saved_commentaries 
                    WHERE user_id = ? AND book_id = ? AND chapter_start = ? 
                    AND chapter_end IS ? AND verse_start IS ? AND verse_end IS ? 
                    AND commentary_type = ?
                ''', (user_id, book_id, chapter_start, chapter_end, verse_start, verse_end, commentary_type))

                existing = cursor.fetchone()

                if existing:
                    # Обновляем существующий
                    cursor.execute('''
                        UPDATE saved_commentaries 
                        SET reference_text = ?, commentary_text = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (reference_text, commentary_text, existing[0]))
                else:
                    # Создаем новый
                    cursor.execute('''
                        INSERT INTO saved_commentaries 
                        (user_id, book_id, chapter_start, chapter_end, verse_start, verse_end,
                         reference_text, commentary_text, commentary_type)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (user_id, book_id, chapter_start, chapter_end, verse_start, verse_end,
                          reference_text, commentary_text, commentary_type))

                conn.commit()
                return True

            except Exception as e:
                logger.error(f"Ошибка сохранения комментария: {e}")
                conn.rollback()
                return False
            finally:
                conn.close()

        return await asyncio.to_thread(_execute)

    async def get_saved_commentary(self, user_id: int, book_id: int, chapter_start: int,
                                   chapter_end: int = None, verse_start: int = None, verse_end: int = None,
                                   commentary_type: str = "ai") -> Optional[str]:
        """Получает сохраненное толкование"""
        def _execute():
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            try:
                cursor.execute('''
                    SELECT commentary_text FROM saved_commentaries 
                    WHERE user_id = ? AND book_id = ? AND chapter_start = ? 
                    AND chapter_end IS ? AND verse_start IS ? AND verse_end IS ? 
                    AND commentary_type = ?
                ''', (user_id, book_id, chapter_start, chapter_end, verse_start, verse_end, commentary_type))

                result = cursor.fetchone()
                return result[0] if result else None

            except Exception as e:
                logger.error(f"Ошибка получения комментария: {e}")
                return None
            finally:
                conn.close()

        return await asyncio.to_thread(_execute)

    async def delete_saved_commentary(self, user_id: int, book_id: int, chapter_start: int,
                                      chapter_end: int = None, verse_start: int = None, verse_end: int = None,
                                      commentary_type: str = "ai") -> bool:
        """Удаляет сохраненное толкование"""
        def _execute():
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            try:
                cursor.execute('''
                    DELETE FROM saved_commentaries 
                    WHERE user_id = ? AND book_id = ? AND chapter_start = ? 
                    AND chapter_end IS ? AND verse_start IS ? AND verse_end IS ? 
                    AND commentary_type = ?
                ''', (user_id, book_id, chapter_start, chapter_end, verse_start, verse_end, commentary_type))

                conn.commit()
                return cursor.rowcount > 0

            except Exception as e:
                logger.error(f"Ошибка удаления комментария: {e}")
                conn.rollback()
                return False
            finally:
                conn.close()

        return await asyncio.to_thread(_execute)

    async def get_user_commentaries(self, user_id: int, limit: int = 50) -> list:
        """Получает последние сохраненные толкования пользователя"""
        def _execute():
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            try:
                cursor.execute('''
                    SELECT id, book_id, chapter_start, chapter_end, verse_start, verse_end,
                           reference_text, commentary_text, commentary_type, created_at
                    FROM saved_commentaries 
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (user_id, limit))

                results = cursor.fetchall()

                # Преобразуем в список словарей
                commentaries = []
                for row in results:
                    commentaries.append({
                        'id': row[0],
                        'book_id': row[1],
                        'chapter_start': row[2],
                        'chapter_end': row[3],
                        'verse_start': row[4],
                        'verse_end': row[5],
                        'reference_text': row[6],
                        'commentary_text': row[7],
                        'commentary_type': row[8],
                        'created_at': row[9]
                    })

                return commentaries

            except Exception as e:
                logger.error(
                    f"Ошибка получения комментариев пользователя: {e}")
                return []
            finally:
                conn.close()

        return await asyncio.to_thread(_execute)

    # Заглушки для методов библейских тем (для совместимости API)
    async def get_bible_topics(self, search_query: str = "", limit: int = 50) -> list:
        """Получает список библейских тем (заглушка для SQLite)"""
        logger.warning("Метод get_bible_topics не реализован для SQLite")
        return []

    async def get_topic_by_name(self, topic_name: str) -> dict:
        """Получает тему по названию (заглушка для SQLite)"""
        logger.warning("Метод get_topic_by_name не реализован для SQLite")
        return {}

    async def get_topic_by_id(self, topic_id: int) -> dict:
        """Получает тему по ID (заглушка для SQLite)"""
        logger.warning("Метод get_topic_by_id не реализован для SQLite")
        return {}

    async def search_topics_fulltext(self, search_query: str, limit: int = 20) -> list:
        """Полнотекстовый поиск по темам (заглушка для SQLite)"""
        logger.warning("Метод search_topics_fulltext не реализован для SQLite")
        return []

    async def get_topics_count(self) -> int:
        """Получает количество тем (заглушка для SQLite)"""
        logger.warning("Метод get_topics_count не реализован для SQLite")
        return 0

    async def add_bible_topic(self, topic_name: str, verses: str) -> bool:
        """Добавляет тему (заглушка для SQLite)"""
        logger.warning("Метод add_bible_topic не реализован для SQLite")
        return False

    async def update_bible_topic(self, topic_id: int, topic_name: str = None, verses: str = None) -> bool:
        """Обновляет тему (заглушка для SQLite)"""
        logger.warning("Метод update_bible_topic не реализован для SQLite")
        return False

    async def delete_bible_topic(self, topic_id: int) -> bool:
        """Удаляет тему (заглушка для SQLite)"""
        logger.warning("Метод delete_bible_topic не реализован для SQLite")
        return False


# Глобальный экземпляр менеджера БД


db_manager = DatabaseManager()
