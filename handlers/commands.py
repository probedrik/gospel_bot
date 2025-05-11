"""
Обработчики команд бота.
"""
import logging
from datetime import datetime
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from keyboards.main import get_main_keyboard, create_book_keyboard
from utils.api_client import bible_api
from utils.bible_data import bible_data
from middleware.state import set_page, get_current_translation, get_chosen_book, get_current_chapter, get_bookmarks

# Инициализация логгера
logger = logging.getLogger(__name__)

# Создаем роутер для команд
router = Router()


@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext, db=None):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or "пользователь"

    # Сохраняем пользователя в БД
    try:
        # В aiogram 3.x диспетчер передает сохраненные данные как дополнительные аргументы
        if db:
            await db.add_user(user_id, username, first_name)
    except Exception as e:
        logger.error(f"Ошибка при сохранении пользователя в БД: {e}")

    welcome_text = (
        f"🙏 Добро пожаловать, {first_name}!\n\n"
        "Этот бот поможет вам:\n"
        "📖 Читать книги Библии\n"
        "✨ Получать случайные стихи\n"
        "📌 Сохранять закладки для быстрого доступа\n"
        "🔍 Искать по ссылкам (например, 'Быт 1:1')\n\n"
        "Используйте кнопки меню ниже для навигации."
    )

    await message.answer(welcome_text, reply_markup=get_main_keyboard())


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    help_text = (
        "📚 <b>Помощь по использованию бота</b>\n\n"
        "Основные команды:\n"
        "• /start - Запустить бота\n"
        "• /help - Показать эту помощь\n"
        "• /books - Показать список книг\n"
        "• /random - Получить случайный стих\n"
        "• /bookmarks - Показать ваши закладки\n\n"
        "Поиск отрывка:\n"
        "Напишите ссылку в формате [Книга глава:стих], например:\n"
        "Быт 1:1 - Первый стих Бытия\n"
        "Ин 3:16 - 16-й стих 3-й главы Иоанна\n\n"
        "Для чтения выберите книгу и главу в меню бота."
    )

    await message.answer(help_text)


@router.message(Command("books"))
async def cmd_books(message: Message, state: FSMContext):
    """Обработчик команды /books"""
    await set_page(state, 0)
    await message.answer(
        "Выберите книгу:",
        reply_markup=create_book_keyboard(0)
    )


@router.message(Command("random"))
async def cmd_random(message: Message, state: FSMContext):
    """Обработчик команды /random"""
    translation = await get_current_translation(state)
    text = await bible_api.get_random_verse(translation)
    await message.answer(text)


@router.message(Command("about"))
async def cmd_about(message: Message):
    """Обработчик команды /about"""
    about_text = (
        "📱 <b>О боте</b>\n\n"
        "Этот бот разработан для чтения Библии с удобным интерфейсом.\n\n"
        "Используемые API:\n"
        "• JustBible API - https://justbible.ru/\n\n"
        "Доступные переводы:\n"
        "• Синодальный перевод (RST)\n"
        "• Современный перевод РБО (RBO)\n\n"
        "Бот находится в разработке и постоянно улучшается. "
        "Если у вас есть предложения или вы нашли ошибку, напишите нам."
    )

    await message.answer(about_text)


@router.message(Command("test_db"))
async def test_db_command(message: Message, state: FSMContext, db=None):
    """Тестовый обработчик для проверки доступности объекта БД"""
    logger.info("Вызвана команда /test_db")

    result = [
        "Проверка доступности БД:",
        f"- Объект db передан в обработчик: {'Да' if db else 'Нет'}"
    ]

    if db:
        try:
            # Проверяем атрибуты и метод get_user
            result.append(f"- Путь к файлу БД: {db.db_file}")

            # Пробуем добавить тестового пользователя
            await db.add_user(
                message.from_user.id,
                message.from_user.username or "",
                message.from_user.first_name or "test_user"
            )
            result.append("- Добавление тестового пользователя: Успешно")

            # Пробуем получить пользователя
            user = await db.get_user(message.from_user.id)
            if user:
                result.append(
                    f"- Получение пользователя из БД: Успешно (ID: {user.get('user_id')})")
            else:
                result.append(
                    "- Получение пользователя из БД: Ошибка (пользователь не найден)")

            # Пробуем добавить тестовую закладку
            await db.add_bookmark(
                message.from_user.id,
                1,  # Genesis/Бытие
                1,  # Chapter 1
                "Test Bookmark"
            )
            result.append("- Добавление тестовой закладки: Успешно")

            # Пробуем получить закладки
            bookmarks = await db.get_bookmarks(message.from_user.id)
            result.append(
                f"- Получение закладок из БД: {len(bookmarks)} закладок")
        except Exception as e:
            result.append(f"- Ошибка при тестировании БД: {e}")

    # Отправляем результат
    await message.answer("\n".join(result))


@router.message(Command("test_db_write"))
async def test_db_write(message: Message):
    """Тестовый обработчик для прямой записи в БД"""
    user_id = message.from_user.id
    try:
        from database.db_manager import db_manager

        # Путь к файлу БД
        db_file = db_manager.db_file
        logger.info(f"Прямая запись в БД: {db_file}")

        # Принудительно создаем таблицы
        db_manager._create_tables()

        # Добавляем пользователя
        await db_manager.add_user(user_id, message.from_user.username or "", message.from_user.first_name or "")
        logger.info(f"Пользователь {user_id} добавлен в БД")

        # Добавляем тестовую закладку
        book_id = 1  # Бытие
        chapter = 1
        display_text = "Тестовая закладка: Бытие 1"

        result = await db_manager.add_bookmark(user_id, book_id, chapter, display_text)
        logger.info(f"Результат добавления тестовой закладки: {result}")

        # Проверяем, что закладка добавлена
        bookmarks = await db_manager.get_bookmarks(user_id)
        logger.info(f"Закладки после добавления: {bookmarks}")

        if bookmarks and len(bookmarks) > 0:
            await message.answer(f"✅ Тестовая закладка успешно добавлена в БД: {display_text}")
        else:
            await message.answer("❌ Не удалось добавить тестовую закладку в БД")

    except Exception as e:
        logger.error(f"Ошибка при тестовой записи в БД: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка при тестовой записи в БД: {str(e)[:100]}")


@router.message(Command("direct_bookmark"))
async def direct_bookmark(message: Message, state: FSMContext):
    """Напрямую добавляет текущую главу в закладки через db_manager"""
    user_id = message.from_user.id
    try:
        # Импортируем менеджер БД напрямую
        from database.db_manager import db_manager

        # Получаем выбранную книгу и главу из состояния
        # Теперь state передается правильно как аргумент функции
        book_id = await get_chosen_book(state)
        chapter = await get_current_chapter(state)

        logger.info(
            f"Попытка прямого добавления закладки: user_id={user_id}, book_id={book_id}, chapter={chapter}")

        if not book_id or not chapter:
            await message.answer("❌ Сначала выберите книгу и главу")
            return

        from utils.bible_data import bible_data
        book_name = bible_data.get_book_name(book_id)
        display_text = f"{book_name} {chapter}"

        # Форсируем создание таблиц
        db_manager._create_tables()
        logger.info("Таблицы в БД проверены перед прямым добавлением закладки")

        # Добавляем пользователя (на всякий случай)
        await db_manager.add_user(user_id, message.from_user.username or "", message.from_user.first_name or "")
        logger.info(
            f"Пользователь {user_id} добавлен/обновлен в БД перед прямым добавлением закладки")

        # Напрямую добавляем в БД, минуя обработчики
        result = await db_manager.add_bookmark(user_id, book_id, chapter, display_text)
        logger.info(f"Результат прямого добавления закладки: {result}")

        # Проверяем, добавилась ли закладка
        bookmarks = await db_manager.get_bookmarks(user_id)
        bookmark_in_db = any(bm[0] == book_id and bm[1]
                             == chapter for bm in bookmarks)
        logger.info(
            f"Проверка наличия закладки в БД после добавления: {'найдена' if bookmark_in_db else 'не найдена'}")

        if result:
            await message.answer(f"✅ Закладка напрямую добавлена в БД: {display_text}")
        else:
            await message.answer(f"❌ Не удалось добавить закладку в БД: {display_text}")

    except Exception as e:
        logger.error(
            f"Ошибка при прямом добавлении закладки: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка: {str(e)[:100]}")


@router.message(Command("check_db"))
async def check_db(message: Message):
    """Проверяет доступность БД и выводит отчет"""
    try:
        from database.db_manager import db_manager

        # Выполняем проверку
        result = await db_manager.check_db_access()

        # Формируем отчет
        report = [f"📊 Отчет о состоянии БД: {result['db_file']}"]

        if result['success']:
            report.append("✅ БД доступна и работает корректно")
        else:
            report.append("❌ Обнаружены проблемы с БД:")

        # Добавляем детали
        if 'dir_exists' in result:
            report.append(
                f"- Директория: {'существует' if result['dir_exists'] else 'НЕ существует'}")
        if 'dir_writable' in result:
            report.append(
                f"- Запись в директорию: {'доступна' if result['dir_writable'] else 'НЕ доступна'}")
        if 'file_exists' in result:
            report.append(
                f"- Файл БД: {'существует' if result['file_exists'] else 'НЕ существует'}")
        if 'file_size' in result:
            report.append(f"- Размер файла: {result['file_size']} байт")
        if 'file_writable' in result:
            report.append(
                f"- Запись в файл: {'доступна' if result['file_writable'] else 'НЕ доступна'}")
        if 'sqlite_access' in result:
            report.append(
                f"- Доступ SQLite: {'успешный' if result['sqlite_access'] else 'ОШИБКА'}")
        if 'tables' in result:
            report.append(f"- Таблицы в БД: {', '.join(result['tables'])}")

        # Ошибки
        if result['errors']:
            report.append("\n⚠️ Обнаружены ошибки:")
            for err in result['errors']:
                report.append(f"  - {err}")

        await message.answer("\n".join(report))

    except Exception as e:
        logger.error(f"Ошибка при проверке БД: {e}", exc_info=True)
        await message.answer(f"❌ Произошла ошибка при проверке БД: {str(e)[:100]}")


@router.message(Command("repair_db"))
async def repair_db_command(message: Message):
    """Пытается восстановить БД"""
    try:
        from database.db_manager import db_manager

        # Сначала проверяем БД
        check_result = await db_manager.check_db_access()

        # Если все в порядке, не восстанавливаем
        if check_result['success'] and not check_result['errors']:
            await message.answer("✅ БД работает нормально, восстановление не требуется")
            return

        # Восстанавливаем БД
        repair_result = await db_manager.repair_db()

        # Формируем отчет
        report = ["🔧 Отчет о восстановлении БД:"]

        if repair_result['success']:
            report.append("✅ БД успешно восстановлена")
        else:
            report.append("❌ Восстановление БД не удалось")

        # Действия
        if repair_result['actions']:
            report.append("\nВыполненные действия:")
            for action in repair_result['actions']:
                report.append(f"  - {action}")

        # Ошибки
        if repair_result['errors']:
            report.append("\n⚠️ Ошибки при восстановлении:")
            for err in repair_result['errors']:
                report.append(f"  - {err}")

        # Повторная проверка
        check_result = await db_manager.check_db_access()
        if check_result['success']:
            report.append("\n✅ Повторная проверка: БД работает нормально")
        else:
            report.append("\n❌ Повторная проверка: БД все еще имеет проблемы")

        await message.answer("\n".join(report))

    except Exception as e:
        logger.error(f"Ошибка при восстановлении БД: {e}", exc_info=True)
        await message.answer(f"❌ Произошла ошибка при восстановлении БД: {str(e)[:100]}")


@router.message(Command("save_bookmarks_to_db"))
async def save_bookmarks_to_db(message: Message, state: FSMContext):
    """Сохраняет все закладки из состояния в БД"""
    user_id = message.from_user.id
    try:
        # Импортируем напрямую
        from database.db_manager import db_manager

        # Получаем закладки из состояния
        state_bookmarks = await get_bookmarks(state)
        logger.info(
            f"Получено {len(state_bookmarks)} закладок из состояния для сохранения в БД")

        if not state_bookmarks:
            await message.answer("В состоянии нет закладок для сохранения")
            return

        # Добавляем пользователя (на всякий случай)
        await db_manager.add_user(user_id, message.from_user.username or "", message.from_user.first_name or "")

        # Тест соединения с БД
        try:
            # Проверка доступа
            check_result = await db_manager.check_db_access()
            if not check_result['success']:
                errors = ", ".join(check_result['errors'])
                await message.answer(f"⚠️ Проблемы с доступом к БД: {errors}")

                # Пробуем восстановить БД
                logger.info(
                    "Попытка восстановления БД перед сохранением закладок")
                repair_result = await db_manager.repair_db()
                if repair_result['success']:
                    await message.answer("✅ БД успешно восстановлена перед сохранением")
                else:
                    await message.answer(f"❌ Не удалось восстановить БД: {', '.join(repair_result['errors'])}")
                    return
        except Exception as e:
            logger.error(f"Ошибка при проверке доступа к БД: {e}")
            await message.answer(f"❌ Ошибка при проверке БД: {str(e)[:100]}")

        # Счетчики для отчета
        saved_count = 0
        failed_count = 0
        already_exists_count = 0

        # Сохраняем каждую закладку
        for key, data in state_bookmarks.items():
            if isinstance(data, dict):
                try:
                    book_id = data.get('book_id')
                    chapter = data.get('chapter')
                    display_text = data.get('display_text')

                    if not (book_id and chapter and display_text):
                        logger.warning(f"Некорректные данные закладки: {data}")
                        failed_count += 1
                        continue

                    # Проверяем, есть ли такая закладка уже в БД
                    bookmarks = await db_manager.get_bookmarks(user_id)
                    bookmark_exists = any(
                        bm[0] == book_id and bm[1] == chapter for bm in bookmarks)

                    if bookmark_exists:
                        logger.info(
                            f"Закладка {display_text} уже существует в БД")
                        already_exists_count += 1
                        continue

                    # Сохраняем в БД
                    result = await db_manager.add_bookmark(user_id, book_id, chapter, display_text)

                    if result:
                        logger.info(
                            f"Закладка {display_text} успешно сохранена в БД")
                        saved_count += 1
                    else:
                        logger.warning(
                            f"Не удалось сохранить закладку {display_text} в БД")
                        failed_count += 1

                except Exception as e:
                    logger.error(f"Ошибка при сохранении закладки {key}: {e}")
                    failed_count += 1
            else:
                logger.warning(f"Некорректный формат закладки: {key} = {data}")
                failed_count += 1

        # Проверка сохраненных закладок
        final_bookmarks = await db_manager.get_bookmarks(user_id)
        logger.info(f"После сохранения в БД: {len(final_bookmarks)} закладок")

        # Отчет
        report = [
            f"📊 Отчет о сохранении закладок в БД:",
            f"- Всего закладок в состоянии: {len(state_bookmarks)}",
            f"- Успешно сохранено: {saved_count}",
            f"- Уже существовало в БД: {already_exists_count}",
            f"- Не удалось сохранить: {failed_count}",
            f"- Итого в БД: {len(final_bookmarks)} закладок"
        ]

        await message.answer("\n".join(report))

    except Exception as e:
        logger.error(
            f"Ошибка при сохранении закладок в БД: {e}", exc_info=True)
        await message.answer(f"❌ Критическая ошибка: {str(e)[:100]}")


@router.message(Command("reset_db"))
async def reset_db_command(message: Message, state: FSMContext):
    """Полностью пересоздает базу данных и переносит закладки из состояния"""
    user_id = message.from_user.id
    try:
        # Импортируем все необходимое
        from database.db_manager import db_manager
        import os
        import sqlite3
        from datetime import datetime

        # Получаем закладки из состояния перед сбросом
        state_bookmarks = await get_bookmarks(state)
        bookmark_count = len(state_bookmarks)
        logger.info(
            f"Получено {bookmark_count} закладок из состояния перед сбросом БД")

        # Информация о текущей БД
        db_file = db_manager.db_file
        db_dir = os.path.dirname(db_file)

        await message.answer(f"🔄 Начинаю полное пересоздание базы данных: {db_file}")

        # 1. Делаем бэкап, если БД существует
        backup_path = None
        if os.path.exists(db_file):
            backup_path = f"{db_file}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
            try:
                import shutil
                shutil.copy2(db_file, backup_path)
                logger.info(f"Создан бэкап БД: {backup_path}")
                await message.answer(f"✅ Создан бэкап: {backup_path}")
            except Exception as e:
                logger.error(f"Ошибка при создании бэкапа: {e}")
                await message.answer(f"⚠️ Не удалось создать бэкап: {str(e)[:100]}")

        # 2. Удаляем существующий файл БД
        if os.path.exists(db_file):
            try:
                os.remove(db_file)
                logger.info(f"Удален файл БД: {db_file}")
                await message.answer("✅ Существующий файл БД удален")
            except Exception as e:
                logger.error(f"Ошибка при удалении файла БД: {e}")
                await message.answer(f"⚠️ Не удалось удалить файл БД: {str(e)[:100]}")
                return

        # 3. Создаем директорию для БД, если её нет
        if not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir, exist_ok=True)
                logger.info(f"Создана директория для БД: {db_dir}")
            except Exception as e:
                logger.error(f"Ошибка при создании директории: {e}")
                await message.answer(f"❌ Не удалось создать директорию для БД: {str(e)[:100]}")
                return

        # 4. Создаем новую БД и таблицы
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()

            # Таблица пользователей
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
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()

            conn.commit()
            conn.close()

            logger.info(f"Созданы таблицы в новой БД: {tables}")
            await message.answer(f"✅ Создана новая БД с таблицами: {', '.join([t[0] for t in tables])}")
        except Exception as e:
            logger.error(f"Ошибка при создании новой БД: {e}")
            await message.answer(f"❌ Не удалось создать новую БД: {str(e)[:100]}")
            return

        # 5. Добавляем пользователя
        try:
            await db_manager.add_user(user_id, message.from_user.username or "", message.from_user.first_name or "")
            logger.info(f"Пользователь {user_id} добавлен в новую БД")
        except Exception as e:
            logger.error(f"Ошибка при добавлении пользователя: {e}")
            await message.answer(f"⚠️ Не удалось добавить пользователя: {str(e)[:100]}")

        # 6. Переносим закладки из состояния
        if bookmark_count > 0:
            await message.answer(f"🔄 Переношу {bookmark_count} закладок из состояния в новую БД...")

            saved_count = 0
            failed_count = 0

            for key, data in state_bookmarks.items():
                if isinstance(data, dict):
                    try:
                        book_id = data.get('book_id')
                        chapter = data.get('chapter')
                        display_text = data.get('display_text')

                        if book_id and chapter and display_text:
                            result = await db_manager.add_bookmark(user_id, book_id, chapter, display_text)
                            if result:
                                saved_count += 1
                            else:
                                failed_count += 1
                        else:
                            failed_count += 1
                    except Exception as e:
                        logger.error(
                            f"Ошибка при переносе закладки {key}: {e}")
                        failed_count += 1
                else:
                    failed_count += 1

            # Проверяем результат
            final_bookmarks = await db_manager.get_bookmarks(user_id)
            await message.answer(
                f"✅ Перенос закладок завершен:\n"
                f"- Успешно: {saved_count}\n"
                f"- С ошибками: {failed_count}\n"
                f"- Всего в БД: {len(final_bookmarks)}"
            )

        # 7. Финальная проверка
        check_result = await db_manager.check_db_access()
        if check_result['success']:
            await message.answer("✅ База данных успешно пересоздана и готова к использованию")
        else:
            errors = ", ".join(check_result['errors'])
            await message.answer(f"⚠️ База данных пересоздана, но есть проблемы: {errors}")

    except Exception as e:
        logger.error(
            f"Критическая ошибка при пересоздании БД: {e}", exc_info=True)
        await message.answer(f"❌ Критическая ошибка: {str(e)[:100]}")
