"""
Обработчики команд бота.
"""
import logging
from datetime import datetime
from aiogram import Router
from aiogram.filters import Command, Filter
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext

from keyboards.main import get_main_keyboard, create_book_keyboard
from utils.api_client import bible_api
from utils.bible_data import bible_data
from middleware.state import set_page, get_current_translation, get_chosen_book, get_current_chapter, get_bookmarks
from database.universal_manager import universal_db_manager as db_manager
from aiogram import Router, F
from config.ai_settings import AI_OWNER_ID, AI_DAILY_LIMIT

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
        f"🙏 **Добро пожаловать, {first_name}!**\n\n"
        "📱 **Библейский бот** — ваш помощник в изучении Священного Писания!\n\n"

        "**🔥 Возможности бота:**\n"
        "📖 Чтение всех 66 книг Библии • 🔍 Поиск стихов (`Ин 3:16`) • 🤖 ИИ разбор (3/день) • 📝 Закладки с заметками • 📚 Планы чтения • 🎯 Библейские темы • 📅 Православный календарь • ⚙️ Гибкие настройки • 🔍 Поиск по словам\n\n"

        "🚀 **Начните с меню ниже или просто напишите библейскую ссылку!**"
    )

    await message.answer(welcome_text, reply_markup=await get_main_keyboard(), parse_mode="Markdown")


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    help_text = (
        "📚 **Помощь по использованию бота**\n\n"

        "🎯 **Основные возможности:**\n"
        "• 📖 Чтение всех 66 книг Библии\n"
        "• 🔍 Поиск стихов прямо из чата\n"
        "• 🤖 ИИ помощник с лимитом 3 запроса/день\n"
        "• 📝 Закладки с заметками\n"
        "• 📚 Планы чтения с прогрессом\n"
        "• 🎯 Библейские темы\n"
        "• ⚙️ Гибкие настройки\n\n"

        "📋 **Команды:**\n"
        "• `/start` — Главное меню\n"
        "• `/help` — Эта справка\n"
        "• `/books` — Список книг Библии\n"
        "• `/random` — Случайный стих\n"
        "• `/bookmarks` — Ваши закладки\n\n"

        "🔍 **Поиск стихов (прямо в чат):**\n"
        "• `Ин 3:16` — один стих\n"
        "• `Мф 5:3-12` — диапазон стихов\n"
        "• `Ин 3:16-4:18` — между главами\n"
        "• `Быт 1` — вся глава\n"
        "• `Быт 1-3` — диапазон глав\n\n"

        "🤖 **ИИ функции:**\n"
        "• Разбор стихов и глав\n"
        "• Подбор стихов по ситуациям\n"
        "• Объяснение библейских тем\n"
        "• Автоматическое обновление лимитов\n\n"

        "📝 **Закладки:**\n"
        "• Сохранение любых отрывков\n"
        "• Добавление личных заметок\n"
        "• Сохраненные разборы ИИ\n"
        "• Удобная пагинация\n\n"

        "📚 **Планы чтения:**\n"
        "• Различные планы на выбор\n"
        "• Отслеживание прогресса\n"
        "• Ежедневные отрывки\n"
        "• Интеграция с закладками\n\n"

        "⚙️ **Настройки:**\n"
        "• Смена перевода Библии\n"
        "• Просмотр лимитов ИИ\n"
        "• Подробная помощь\n"
        "• Админ панель (для админов)\n\n"

        "💡 **Совет:** Начните с кнопок меню или просто напишите библейскую ссылку!"
    )
    await message.answer(help_text, parse_mode="Markdown")


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
        from database.universal_manager import universal_db_manager as db_manager

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
        from database.universal_manager import universal_db_manager as db_manager

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

        # Поддержка разных форматов данных
        if bookmarks:
            if isinstance(bookmarks[0], dict):
                bookmark_in_db = any(
                    bm['book_id'] == book_id and bm['chapter'] == chapter for bm in bookmarks)
            else:
                bookmark_in_db = any(
                    bm[0] == book_id and bm[1] == chapter for bm in bookmarks)
        else:
            bookmark_in_db = False

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
        from database.universal_manager import universal_db_manager as db_manager

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
        from database.universal_manager import universal_db_manager as db_manager

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
        from database.universal_manager import universal_db_manager as db_manager

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

                    # Поддержка разных форматов данных
                    if bookmarks:
                        if isinstance(bookmarks[0], dict):
                            bookmark_exists = any(
                                bm['book_id'] == book_id and bm['chapter'] == chapter for bm in bookmarks)
                        else:
                            bookmark_exists = any(
                                bm[0] == book_id and bm[1] == chapter for bm in bookmarks)
                    else:
                        bookmark_exists = False

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
        from database.universal_manager import universal_db_manager as db_manager
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


@router.message(F.text.regexp(r"^/ai_limit( \d+)?$"))
async def ai_limit_command(message: Message):
    """Показать лимит ИИ-запросов для пользователя (только для владельца)"""
    if message.from_user.id != AI_OWNER_ID:
        await message.answer("Доступ запрещён.")
        return
    parts = message.text.strip().split()
    if len(parts) == 2:
        user_id = int(parts[1])
    else:
        user_id = message.from_user.id
    today = datetime.date.today().isoformat()
    count = await db_manager.get_ai_limit(user_id, today)
    await message.answer(f"Пользователь {user_id} сделал {count}/{AI_DAILY_LIMIT} ИИ-запросов сегодня.")


@router.message(F.text.regexp(r"^/ai_limit_reset( \d+)?$"))
async def ai_limit_reset_command(message: Message):
    """Сбросить лимит ИИ-запросов для пользователя (только для владельца)"""
    if message.from_user.id != AI_OWNER_ID:
        await message.answer("Доступ запрещён.")
        return
    parts = message.text.strip().split()
    if len(parts) == 2:
        user_id = int(parts[1])
    else:
        user_id = message.from_user.id
    today = datetime.date.today().isoformat()
    await db_manager.reset_ai_limit(user_id, today)
    await message.answer(f"Лимит ИИ-запросов для пользователя {user_id} сброшен на сегодня.")


@router.message(F.text == "/admin")
async def admin_panel(message: Message):
    if message.from_user.id != AI_OWNER_ID:
        await message.answer("Доступ запрещён.")
        return
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="⚙️ Настройки ИИ", callback_data="admin_ai_limits")],
            [InlineKeyboardButton(
                text="📊 Статистика ИИ-запросов", callback_data="admin_ai_stats")],
            [InlineKeyboardButton(
                text="👥 Топ пользователей по ИИ", callback_data="admin_ai_top")],
            [InlineKeyboardButton(text="🔓 Список безлимитных",
                                  callback_data="admin_ai_unlimited")],
            [InlineKeyboardButton(
                text="🔄 Сбросить лимит пользователя", callback_data="admin_ai_reset")],
            [InlineKeyboardButton(
                text="🔄 Обновить", callback_data="admin_panel_refresh")],
        ]
    )
    await message.answer("<b>Админ-панель</b>\nВыберите действие:", reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data == "admin_panel_refresh")
async def admin_panel_refresh(callback: CallbackQuery):
    if callback.from_user.id != AI_OWNER_ID:
        await callback.answer("Доступ запрещён.", show_alert=True)
        return
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="⚙️ Настройки ИИ", callback_data="admin_ai_limits")],
            [InlineKeyboardButton(
                text="📊 Статистика ИИ-запросов", callback_data="admin_ai_stats")],
            [InlineKeyboardButton(
                text="👥 Топ пользователей по ИИ", callback_data="admin_ai_top")],
            [InlineKeyboardButton(text="🔓 Список безлимитных",
                                  callback_data="admin_ai_unlimited")],
            [InlineKeyboardButton(
                text="🔄 Сбросить лимит пользователя", callback_data="admin_ai_reset")],
            [InlineKeyboardButton(
                text="🔄 Обновить", callback_data="admin_panel_refresh")],
        ]
    )
    await callback.message.edit_text("<b>Админ-панель</b>\nВыберите действие:", reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin_ai_stats")
async def admin_ai_stats(callback: CallbackQuery):
    from database.universal_manager import universal_db_manager as db_manager
    import datetime
    today = datetime.date.today().isoformat()
    # Получить топ-10 пользователей по количеству ИИ-запросов за сегодня
    stats = await db_manager.get_ai_stats(today, limit=10)
    text = "<b>Топ-10 пользователей по ИИ-запросам сегодня:</b>\n"
    for user_id, count in stats:
        text += f"<code>{user_id}</code>: {count}\n"
    await callback.message.edit_text(text, reply_markup=callback.message.reply_markup, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin_ai_top")
async def admin_ai_top(callback: CallbackQuery):
    from database.universal_manager import universal_db_manager as db_manager
    # Получить топ-10 пользователей за всё время
    stats = await db_manager.get_ai_stats_alltime(limit=10)
    text = "<b>Топ-10 пользователей по ИИ-запросам (всё время):</b>\n"
    for user_id, count in stats:
        text += f"<code>{user_id}</code>: {count}\n"
    await callback.message.edit_text(text, reply_markup=callback.message.reply_markup, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin_ai_unlimited")
async def admin_ai_unlimited(callback: CallbackQuery):
    from config.ai_settings import AI_UNLIMITED_USERS
    text = "<b>Пользователи с безлимитным доступом:</b>\n"
    for uid in AI_UNLIMITED_USERS:
        text += f"<code>{uid}</code>\n"
    text += "\nДля изменения списка — отредактируйте config/ai_settings.py."
    await callback.message.edit_text(text, reply_markup=callback.message.reply_markup, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin_ai_reset")
async def admin_ai_reset(callback: CallbackQuery):
    await callback.message.edit_text(
        "Введите user_id для сброса лимита (отправьте числом в чат):",
        reply_markup=callback.message.reply_markup
    )
    # Сохраняем состояние ожидания user_id (можно реализовать через FSM или временно через глобальный dict)
    global _admin_wait_reset
    _admin_wait_reset = callback.from_user.id
    await callback.answer()


class AdminWaitResetFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        return '_admin_wait_reset' in globals() and message.from_user.id == _admin_wait_reset


@router.message(AdminWaitResetFilter())
async def admin_ai_reset_userid(message: Message):
    global _admin_wait_reset
    try:
        user_id = int(message.text.strip())
    except Exception:
        await message.answer("Некорректный user_id. Введите число.")
        return
    import datetime
    today = datetime.date.today().isoformat()
    from database.universal_manager import universal_db_manager as db_manager
    await db_manager.reset_ai_limit(user_id, today)
    await message.answer(f"Лимит ИИ-запросов для пользователя {user_id} сброшен на сегодня.")
    del _admin_wait_reset


# Обработчик настроек ИИ из /admin панели
@router.callback_query(F.data == "admin_ai_limits")
async def admin_ai_limits_from_commands(callback: CallbackQuery):
    """Переход к настройкам ИИ из /admin панели"""
    if callback.from_user.id != AI_OWNER_ID:
        await callback.answer("Доступ запрещён.", show_alert=True)
        return

    # Импортируем функцию из handlers/settings.py
    from handlers.settings import admin_ai_limits
    from aiogram.fsm.context import FSMContext

    # Создаем пустое состояние для совместимости
    state = FSMContext(storage=None, key=None)

    # Вызываем функцию настроек ИИ
    await admin_ai_limits(callback, state)
