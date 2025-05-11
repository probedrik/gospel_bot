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
                last_activity TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            # Таблица закладок
            logger.info("Создание/проверка таблицы bookmarks")
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                book_id INTEGER,
                chapter INTEGER,
                display_text TEXT,
                created_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            ''')

            # Проверяем, созданы ли таблицы
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND (name='users' OR name='bookmarks')")
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
                "SELECT COUNT(name) FROM sqlite_master WHERE type='table' AND (name='users' OR name='bookmarks')")
            table_count = cursor.fetchone()[0]
            if table_count == 2:
                logger.info("Обе таблицы (users и bookmarks) успешно созданы")
            else:
                logger.warning(
                    f"Не все таблицы созданы. Найдено таблиц: {table_count}/2")

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

    async def add_bookmark(self, user_id: int, book_id: int, chapter: int, display_text: str) -> bool:
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
            f"Попытка добавления закладки: {user_id} - {display_text} (book_id={book_id}, chapter={chapter})")

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
                "SELECT 1 FROM bookmarks WHERE user_id = ? AND book_id = ? AND chapter = ?",
                (user_id, book_id, chapter)
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
                    query = "INSERT INTO bookmarks (user_id, book_id, chapter, display_text, created_at) VALUES (?, ?, ?, ?, ?)"
                    logger.info(
                        f"SQL запрос: {query} с параметрами ({user_id}, {book_id}, {chapter}, '{display_text}', {now})")
                    cursor.execute(
                        query, (user_id, book_id, chapter, display_text, now))

                    # Обязательно делаем commit для сохранения изменений
                    conn.commit()
                    logger.info(
                        f"SQL запрос выполнен, транзакция подтверждена (commit)")

                    # Проверяем, была ли закладка действительно добавлена
                    cursor.execute(
                        "SELECT * FROM bookmarks WHERE user_id = ? AND book_id = ? AND chapter = ?",
                        (user_id, book_id, chapter)
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
                    SELECT book_id, chapter, display_text FROM bookmarks
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

    async def remove_bookmark(self, user_id: int, book_id: int, chapter: int) -> None:
        """
        Удаляет конкретную закладку пользователя.

        Args:
            user_id: ID пользователя Telegram
            book_id: ID книги Библии
            chapter: Номер главы
        """
        def _execute():
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM bookmarks WHERE user_id = ? AND book_id = ? AND chapter = ?",
                (user_id, book_id, chapter)
            )
            conn.commit()
            conn.close()

        await asyncio.to_thread(_execute)
        logger.debug(
            f"Удалена закладка для пользователя {user_id}: {book_id} {chapter}")

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
                chapter INTEGER,
                display_text TEXT,
                created_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )''')

            conn.commit()
            conn.close()

            result["actions"].append("Созданы новые таблицы users и bookmarks")
            result["success"] = True
            return result

        except Exception as e:
            result["errors"].append(f"Ошибка восстановления БД: {e}")
            return result


# Создаем глобальный экземпляр менеджера БД для использования в других модулях
db_manager = DatabaseManager()
