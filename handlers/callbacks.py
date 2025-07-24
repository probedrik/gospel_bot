"""
Обработчики колбэков для инлайн-кнопками.
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from config.settings import ENABLE_VERSE_NUMBERS, BIBLE_MARKDOWN_ENABLED, BIBLE_MARKDOWN_MODE

from keyboards.main import (
    get_main_keyboard,
    create_book_keyboard,
    create_navigation_keyboard,
    create_translations_keyboard,
)
from utils.api_client import bible_api
from utils.bible_data import bible_data
from utils.text_utils import split_text
from middleware.state import (
    get_chosen_book, set_chosen_book,
    get_current_chapter, set_current_chapter,
    get_current_translation, set_current_translation,
    get_page, set_page,
    get_bookmarks, add_bookmark, clear_bookmarks, remove_bookmark
)
from handlers.text_messages import delete_related_messages

# Инициализация логгера
logger = logging.getLogger(__name__)

# Создаем роутер для колбэков
router = Router()


@router.callback_query(F.data.startswith("select_book_"))
async def book_selected(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора книги из списка"""
    book_id = int(callback.data.split("_")[2])
    await set_chosen_book(state, book_id)

    book_name = bible_data.get_book_name(book_id)

    # Получаем максимальное число глав
    max_chapters = bible_data.max_chapters.get(book_id, 0)

    # Логируем информацию о выбранной книге
    logger.info(
        f"Выбрана книга: {book_name} (ID: {book_id}), макс. глав: {max_chapters}")

    await callback.answer(f"Выбрана книга: {book_name}")
    await callback.message.answer(
        f"Выбрана книга: <b>{book_name}</b>\n"
        f"Введите номер главы (от 1 до {max_chapters}):",
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("nav_page_"))
async def page_navigation(callback: CallbackQuery, state: FSMContext):
    """Обработчик навигации по страницам с книгами"""
    page = int(callback.data.split("_")[2])
    await set_page(state, page)

    current_page = await get_page(state)
    await callback.message.edit_reply_markup(
        reply_markup=create_book_keyboard(current_page)
    )
    await callback.answer()


@router.callback_query(F.data == "next_chapter")
async def next_chapter(callback: CallbackQuery, state: FSMContext, db=None):
    await delete_related_messages(callback, state)
    try:
        book_id = await get_chosen_book(state)
        if not book_id:
            await callback.answer("Сначала выберите книгу")
            return

        current_chapter = await get_current_chapter(state)
        if not current_chapter:
            await callback.answer("Сначала выберите главу")
            return

        # Проверка максимального числа глав
        max_chapter = bible_data.max_chapters.get(book_id, 0)

        if current_chapter >= max_chapter:
            await callback.answer("Это последняя глава")
            return

        next_chapter_num = current_chapter + 1
        translation = await get_current_translation(state)

        # Получаем текст следующей главы
        try:
            text = await bible_api.get_formatted_chapter(
                book_id, next_chapter_num, translation
            )

            # Проверка на ошибку API
            if text.startswith("Ошибка:"):
                await callback.answer("Глава не найдена")
                return

            # Обновляем текущую главу в состоянии
            await set_current_chapter(state, next_chapter_num)

            # Отображаем текст главы
            from utils.text_utils import split_text, get_verses_parse_mode
            parse_mode = get_verses_parse_mode()

            for part in split_text(text):
                await callback.message.answer(part, parse_mode=parse_mode)

            # Проверяем, добавлена ли глава в закладки
            is_bookmarked = await is_chapter_bookmarked(
                callback.from_user.id, book_id, next_chapter_num, db
            )
            logger.info(
                f"Статус закладки для главы {book_id}:{next_chapter_num}: {is_bookmarked}")

            # Создаем кнопки действий для главы
            from utils.bible_data import create_chapter_action_buttons
            extra_buttons = await create_chapter_action_buttons(
                book_id, next_chapter_num, user_id=callback.from_user.id)

            # Навигация по главам
            has_previous = next_chapter_num > 1
            has_next = next_chapter_num < max_chapter
            await callback.message.answer(
                "Выберите действие:",
                reply_markup=create_navigation_keyboard(
                    has_previous, has_next, is_bookmarked, extra_buttons)
            )
            await callback.answer()
        except Exception as e:
            logger.error(f"API error: {e}", exc_info=True)
            await callback.answer("Не удалось загрузить текст. Попробуйте позже.")
    except Exception as e:
        logger.error(f"Error in next_chapter: {e}", exc_info=True)
        await callback.answer("Произошла ошибка при обработке запроса")


@router.callback_query(F.data == "prev_chapter")
async def prev_chapter(callback: CallbackQuery, state: FSMContext, db=None):
    await delete_related_messages(callback, state)
    try:
        book_id = await get_chosen_book(state)
        if not book_id:
            await callback.answer("Сначала выберите книгу")
            return

        current_chapter = await get_current_chapter(state)
        if not current_chapter or current_chapter <= 1:
            await callback.answer("Это первая глава")
            return

        prev_chapter_num = current_chapter - 1
        translation = await get_current_translation(state)

        # Получаем текст предыдущей главы
        try:
            text = await bible_api.get_formatted_chapter(
                book_id, prev_chapter_num, translation
            )

            # Проверка на ошибку API
            if text.startswith("Ошибка:"):
                await callback.answer("Глава не найдена")
                return

            # Обновляем текущую главу в состоянии
            await set_current_chapter(state, prev_chapter_num)

            # Отображаем текст главы
            from utils.text_utils import split_text, get_verses_parse_mode
            parse_mode = get_verses_parse_mode()

            for part in split_text(text):
                await callback.message.answer(part, parse_mode=parse_mode)

            # Проверяем, добавлена ли глава в закладки
            is_bookmarked = await is_chapter_bookmarked(
                callback.from_user.id, book_id, prev_chapter_num, db
            )
            logger.info(
                f"Статус закладки для главы {book_id}:{prev_chapter_num}: {is_bookmarked}")

            # Создаем кнопки действий для главы
            from utils.bible_data import create_chapter_action_buttons
            extra_buttons = await create_chapter_action_buttons(
                book_id, prev_chapter_num, user_id=callback.from_user.id)

            # Добавляем клавиатуру навигации
            has_previous = prev_chapter_num > 1

            # Проверка максимального числа глав
            max_chapter = bible_data.max_chapters.get(book_id, 0)
            has_next = prev_chapter_num < max_chapter

            # Навигация по главам
            await callback.message.answer(
                "Выберите действие:",
                reply_markup=create_navigation_keyboard(
                    has_previous, has_next, is_bookmarked, extra_buttons)
            )
            await callback.answer()
        except Exception as e:
            logger.error(f"API error: {e}", exc_info=True)
            await callback.answer("Не удалось загрузить текст. Попробуйте позже.")
    except Exception as e:
        logger.error(f"Error in prev_chapter: {e}", exc_info=True)
        await callback.answer("Произошла ошибка при обработке запроса")


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    """Обработчик возврата в главное меню"""
    await callback.message.answer(
        "Главное меню:",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("daily_"))
async def daily_selected(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора чтения из ежедневного плана"""
    try:
        _, book_id, chapter = callback.data.split("_")
        book_id = int(book_id)
        chapter = int(chapter)

        # Сохраняем текущую книгу и главу
        await set_chosen_book(state, book_id)
        await set_current_chapter(state, chapter)

        translation = await get_current_translation(state)
        text = await bible_api.get_formatted_chapter(
            book_id, chapter, translation
        )

        # Отображаем текст главы
        from utils.text_utils import split_text, get_verses_parse_mode
        parse_mode = get_verses_parse_mode()

        for part in split_text(text):
            await callback.message.answer(part, parse_mode=parse_mode)

        # Создаем кнопки действий для главы
        from utils.bible_data import create_chapter_action_buttons
        extra_buttons = await create_chapter_action_buttons(book_id, chapter, user_id=callback.from_user.id)

        # Добавляем клавиатуру навигации
        has_previous = chapter > 1
        max_chapter = bible_data.max_chapters.get(book_id, 0)
        has_next = chapter < max_chapter
        await callback.message.answer(
            "Выберите действие:",
            reply_markup=create_navigation_keyboard(
                has_previous, has_next, False, extra_buttons)
        )
        await callback.answer()
    except Exception as e:
        logger.error(
            f"Ошибка при выборе ежедневного чтения: {e}", exc_info=True)
        await callback.answer("Произошла ошибка при получении текста")


@router.callback_query(F.data == "change_translation")
async def change_translation(callback: CallbackQuery):
    """Обработчик смены перевода Библии"""
    await callback.message.answer(
        "Выберите перевод Библии:",
        reply_markup=create_translations_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("translation_"))
async def change_translation(callback: CallbackQuery, state: FSMContext, db=None):
    """Обработчик колбэка смены перевода"""
    translation = callback.data.split("_")[1]
    translations = {
        "rst": "Синодальный перевод",
        "rbo": "Современный перевод РБО"
    }

    # Сохраняем выбранный перевод в состоянии
    await set_current_translation(state, translation)

    # Сохраняем выбранный перевод в БД
    try:
        # В aiogram 3.x диспетчер передает сохраненные данные как дополнительные аргументы
        if db:
            await db.update_user_translation(callback.from_user.id, translation)
            logger.info(f"Перевод обновлен в БД: {translation}")
    except Exception as e:
        logger.error(f"Ошибка при обновлении перевода в БД: {e}")

    await callback.answer(f"Выбран перевод: {translations.get(translation, translation)}")
    await callback.message.answer(
        f"Установлен перевод: {translations.get(translation, translation)}",
        reply_markup=get_main_keyboard()
    )


@router.callback_query(F.data == "back_to_reading")
async def back_to_reading(callback: CallbackQuery, state: FSMContext):
    """Обработчик возврата к текущему чтению"""
    book_id = await get_chosen_book(state)
    chapter = await get_current_chapter(state)

    if not book_id or not chapter:
        await callback.answer("Нет активного чтения")
        await callback.message.answer(
            "У вас нет активного чтения. Выберите книгу и главу:",
            reply_markup=get_main_keyboard()
        )
        return

    has_previous = chapter > 1
    await callback.message.answer(
        "Возврат к чтению:",
        reply_markup=create_navigation_keyboard(has_previous)
    )
    await callback.answer()


async def get_chapter_extras_keyboard(book_id, chapter, user_id=None):
    """Возвращает клавиатуру с кнопками Толкования Лопухина и ИИ-объяснения для главы."""
    from aiogram.types import InlineKeyboardMarkup
    from utils.bible_data import create_chapter_action_buttons

    buttons = await create_chapter_action_buttons(book_id, chapter, user_id=user_id)
    if buttons:
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    return None


async def is_chapter_bookmarked(user_id: int, book_id: int, chapter: int, db=None) -> bool:
    """
    Проверяет, добавлена ли глава в закладки

    Args:
        user_id: ID пользователя
        book_id: ID книги
        chapter: Номер главы
        db: Объект базы данных (не используется, оставлен для совместимости)

    Returns:
        True, если глава в закладках, иначе False
    """
    from database.universal_manager import universal_db_manager as db_manager

    try:
        # Получаем все закладки пользователя напрямую из db_manager
        bookmarks = await db_manager.get_bookmarks(user_id)

        # Проверяем, есть ли среди них нужная
        # Поддержка разных форматов данных (кортежи для SQLite, словари для Supabase/PostgreSQL)
        for bookmark in bookmarks:
            if isinstance(bookmark, dict):
                # Формат словаря (Supabase/PostgreSQL)
                bm_book_id = bookmark['book_id']
                bm_chapter = bookmark['chapter']
            else:
                # Формат кортежа (SQLite)
                bm_book_id, bm_chapter, _ = bookmark

            if bm_book_id == book_id and bm_chapter == chapter:
                logger.info(
                    f"Глава {book_id}:{chapter} найдена в закладках пользователя {user_id}")
                return True

        logger.info(
            f"Глава {book_id}:{chapter} не найдена в закладках пользователя {user_id}")

        # Дополнительно проверяем в состоянии через FSMContext
        try:
            from aiogram.fsm.context import FSMContext
            from aiogram.fsm.storage.memory import MemoryStorage
            from aiogram import Bot

            # Импортируем функцию получения закладок из состояния
            from middleware.state import get_bookmarks

            # Получаем экземпляр бота для создания контекста FSM
            from handlers import bot

            # Если бот доступен, создаем контекст и проверяем закладки в состоянии
            if bot:
                state = FSMContext(bot=bot, user_id=user_id,
                                   storage=MemoryStorage())
                state_bookmarks = await get_bookmarks(state)

                # Проверяем закладки в состоянии
                for key, data in state_bookmarks.items():
                    if isinstance(data, dict):
                        bm_book_id = data.get('book_id')
                        bm_chapter = data.get('chapter')
                        if bm_book_id == book_id and bm_chapter == chapter:
                            logger.info(
                                f"Глава {book_id}:{chapter} найдена в закладках состояния пользователя {user_id}")
                            return True
        except Exception as state_error:
            logger.error(
                f"Ошибка при проверке закладок в состоянии: {state_error}")

        return False
    except Exception as e:
        logger.error(
            f"Ошибка при проверке статуса закладки: {e}", exc_info=True)
        return False
