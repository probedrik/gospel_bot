"""
Обработчики колбэков для работы с закладками.
"""
import logging
import re
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from config.settings import ENABLE_VERSE_NUMBERS, BIBLE_MARKDOWN_ENABLED, BIBLE_MARKDOWN_MODE

from keyboards.main import get_main_keyboard, create_navigation_keyboard, create_bookmarks_keyboard
from utils.bible_data import bible_data
from utils.api_client import bible_api
from utils.text_utils import split_text
from middleware.state import (
    get_chosen_book, set_chosen_book,
    get_current_chapter, set_current_chapter,
    get_current_translation, set_current_translation,
    get_bookmarks, add_bookmark as add_bookmark_to_state,
    clear_bookmarks as clear_bookmarks_from_state,
    remove_bookmark
)

# Инициализация логгера
logger = logging.getLogger(__name__)

# Создаем роутер для колбэков закладок
router = Router()


@router.callback_query(F.data == "add_bookmark")
async def add_bookmark(callback: CallbackQuery, state: FSMContext, db=None):
    """Обработчик для добавления закладки"""
    user_id = callback.from_user.id
    logger.info(
        f"Вызван обработчик добавления закладки пользователем {user_id}")

    # ВАЖНО: Используем напрямую менеджер БД, минуя middleware
    from database.universal_manager import universal_db_manager as db_manager

    # Получаем выбранную книгу и главу
    book_id = await get_chosen_book(state)
    chapter = await get_current_chapter(state)

    logger.info(f"Данные для закладки: book_id={book_id}, chapter={chapter}")

    if not book_id or not chapter:
        await callback.answer("Сначала выберите книгу и главу")
        logger.warning(
            f"Нет выбранной книги или главы для закладки: book_id={book_id}, chapter={chapter}")
        return

    # Получаем название книги
    book_name = bible_data.get_book_name(book_id)
    display_text = f"{book_name} {chapter}"
    logger.info(f"Подготовлен текст закладки: {display_text}")

    # Флаги для отслеживания успеха
    bookmark_added_to_db = False
    bookmark_added_to_state = False

    # Форсируем создание таблиц перед добавлением
    try:
        db_manager._create_tables()
        logger.info("Таблицы в БД проверены перед прямым добавлением закладки")
    except Exception as e:
        logger.error(f"Ошибка при проверке таблиц: {e}")

    # 1. Сначала добавляем пользователя, если его ещё нет
    try:
        await db_manager.add_user(user_id, callback.from_user.username or "", callback.from_user.first_name or "")
        logger.info(f"Пользователь {user_id} добавлен/обновлен в БД")
    except Exception as e:
        logger.error(f"Ошибка при добавлении пользователя: {e}", exc_info=True)

    # 2. Проверяем, есть ли уже такая закладка в БД
    try:
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
            logger.info(f"Закладка {display_text} уже существует в БД")
            bookmark_added_to_db = True
        else:
            # 3. Напрямую добавляем закладку в БД
            result = await db_manager.add_bookmark(user_id, book_id, chapter, display_text)
            logger.info(
                f"Результат прямого добавления закладки в БД: {result}")
            bookmark_added_to_db = result

            # Проверяем, что закладка действительно добавлена
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
            bookmark_added_to_db = bookmark_in_db
    except Exception as e:
        logger.error(
            f"Ошибка при добавлении закладки в БД: {e}", exc_info=True)
        bookmark_added_to_db = False

    # 4. Дополнительно добавляем в состояние для совместимости
    try:
        await add_bookmark_to_state(state, book_id, chapter, display_text)
        logger.info(f"Закладка добавлена в state: {display_text}")
        bookmark_added_to_state = True
    except Exception as e:
        logger.error(
            f"Ошибка при добавлении закладки в состояние: {e}", exc_info=True)
        bookmark_added_to_state = False

    # 5. Формируем ответное сообщение
    try:
        max_chapters = bible_data.max_chapters.get(book_id, 1)
        has_previous = chapter > 1
        has_next = chapter < max_chapters

        # Создаем кнопки действий для главы (исключаем AI кнопку если нужно)
        from utils.bible_data import create_chapter_action_buttons
        extra_buttons = create_chapter_action_buttons(book_id, chapter)

        # Редактируем существующее сообщение с навигацией, обновляя статус закладки
        await callback.message.edit_reply_markup(
            reply_markup=create_navigation_keyboard(
                has_previous, has_next, True, extra_buttons)
        )

        # Отображаем короткое уведомление
        if bookmark_added_to_db or bookmark_added_to_state:
            await callback.answer("Закладка добавлена")
        else:
            await callback.answer("Ошибка при добавлении закладки")
    except Exception as e:
        logger.error(f"Ошибка при отправке ответа: {e}", exc_info=True)
        await callback.answer("Произошла ошибка")


@router.callback_query(F.data == "clear_bookmarks")
async def clear_bookmarks(callback: CallbackQuery, state: FSMContext, db=None):
    """Обработчик для очистки всех закладок"""
    user_id = callback.from_user.id
    logger.info(f"Вызван обработчик очистки закладок пользователем {user_id}")

    # Используем напрямую менеджер БД
    from database.universal_manager import universal_db_manager as db_manager

    try:
        # Очищаем закладки напрямую в БД
        await db_manager.clear_bookmarks(user_id)
        logger.info(f"Закладки очищены в БД для пользователя {user_id}")

        # Проверяем, что закладки действительно удалены
        bookmarks = await db_manager.get_bookmarks(user_id)
        if not bookmarks:
            logger.info(
                f"Подтверждено удаление всех закладок из БД для пользователя {user_id}")
        else:
            logger.warning(
                f"В БД остались закладки после очистки: {len(bookmarks)}")

        # Очищаем и в состоянии для совместимости
        await clear_bookmarks_from_state(state)
        logger.info(f"Закладки очищены в состоянии для пользователя {user_id}")

        await callback.answer("Все закладки удалены")
        await callback.message.answer("Все закладки были удалены.", reply_markup=get_main_keyboard())
    except Exception as e:
        logger.error(f"Ошибка при очистке закладок: {e}", exc_info=True)
        await callback.answer("Ошибка при удалении закладок")


@router.callback_query(F.data == "bookmark_info")
async def bookmark_info(callback: CallbackQuery, state: FSMContext, db=None):
    """Обработчик для удаления закладки по кнопке '🗑️ Удалить закладку'"""
    user_id = callback.from_user.id
    logger.info(f"Вызван обработчик удаления закладки пользователем {user_id}")

    # Используем напрямую менеджер БД
    from database.universal_manager import universal_db_manager as db_manager

    book_id = await get_chosen_book(state)
    chapter = await get_current_chapter(state)

    if not book_id or not chapter:
        await callback.answer("Ошибка: невозможно определить текущую главу")
        return

    book_name = bible_data.get_book_name(book_id)
    display_text = f"{book_name} {chapter}"

    # Сразу удаляем закладку
    try:
        # Удаляем закладку напрямую из БД
        logger.info(
            f"Удаляем закладку из БД: user_id={user_id}, book_id={book_id}, chapter={chapter}")
        await db_manager.remove_bookmark(user_id, book_id, chapter)
        logger.info(f"Закладка удалена из БД: {display_text}")

        # Проверяем, что закладка действительно удалена
        bookmarks = await db_manager.get_bookmarks(user_id)

        # Поддержка разных форматов данных (кортежи для SQLite, словари для Supabase/PostgreSQL)
        if bookmarks:
            if isinstance(bookmarks[0], dict):
                # Формат словаря (Supabase/PostgreSQL)
                bookmark_exists = any(
                    bm['book_id'] == book_id and bm['chapter'] == chapter for bm in bookmarks)
            else:
                # Формат кортежа (SQLite)
                bookmark_exists = any(
                    bm[0] == book_id and bm[1] == chapter for bm in bookmarks)
        else:
            bookmark_exists = False

        if not bookmark_exists:
            logger.info(f"Подтверждено удаление закладки из БД")
            bookmark_removed = True
        else:
            logger.warning(f"Закладка все еще существует в БД после удаления")
            bookmark_removed = False

        # Удаляем и из состояния для совместимости
        await remove_bookmark(state, book_id, chapter)
        logger.info(f"Закладка удалена из state: {display_text}")

        # Получаем максимальное число глав для данной книги
        max_chapters = bible_data.max_chapters.get(book_id, 1)

        # Определяем, есть ли предыдущие/следующие главы
        has_previous = chapter > 1
        has_next = chapter < max_chapters

        # Создаем кнопки действий для главы
        from utils.bible_data import create_chapter_action_buttons
        extra_buttons = create_chapter_action_buttons(book_id, chapter)

        # Отправляем сообщение об успешном удалении
        await callback.answer("Закладка удалена")

        # Обновляем клавиатуру навигации
        await callback.message.edit_reply_markup(
            reply_markup=create_navigation_keyboard(
                has_previous, has_next, False, extra_buttons)
        )
    except Exception as e:
        logger.error(f"Ошибка при удалении закладки: {e}", exc_info=True)
        await callback.answer("Ошибка при удалении закладки")


@router.callback_query(F.data.startswith("bookmark_"))
async def bookmark_selected(callback: CallbackQuery, state: FSMContext, db=None):
    """Обработчик для выбора закладки"""
    logger.info(f"Вызван обработчик выбора закладки: {callback.data}")

    try:
        # Разбираем данные из callback
        # Формат: bookmark_{book_id}_{chapter}
        callback_parts = callback.data.split("_")
        if len(callback_parts) < 3:
            logger.error(f"Неверный формат callback_data: {callback.data}")
            await callback.answer("Ошибка: неверный формат данных закладки")
            return

        book_id = int(callback_parts[1])
        chapter = int(callback_parts[2])

        logger.info(f"Выбрана закладка: book_id={book_id}, chapter={chapter}")

        # Сохраняем выбор в состоянии
        await set_chosen_book(state, book_id)
        await set_current_chapter(state, chapter)

        # Получаем текст главы
        book_name = bible_data.get_book_name(book_id)

        # Определяем, есть ли предыдущие/следующие главы
        max_chapters = bible_data.max_chapters.get(book_id, 1)
        has_previous = chapter > 1
        has_next = chapter < max_chapters

        # Проверяем, добавлена ли глава в закладки (очевидно, да, раз пользователь запросил её из закладок)
        is_bookmarked = True

        # Получаем текущий выбранный перевод
        translation = await get_current_translation(state)

        # Получаем текст главы
        text = await bible_api.get_formatted_chapter(book_id, chapter, translation)

        # Отправляем текст главы
        from utils.text_utils import get_verses_parse_mode
        parse_mode = get_verses_parse_mode()

        for part in split_text(text):
            await callback.message.answer(part, parse_mode=parse_mode)

        # Создаем кнопки действий для главы
        from utils.bible_data import create_chapter_action_buttons
        extra_buttons = create_chapter_action_buttons(book_id, chapter)

        # Отправляем объединенную клавиатуру навигации с дополнительными кнопками
        await callback.message.answer(
            "⚡ Выберите действие:",
            reply_markup=create_navigation_keyboard(
                has_previous, has_next, is_bookmarked, extra_buttons)
        )
        await callback.answer()
    except ValueError as e:
        logger.error(f"Ошибка при разборе callback_data: {e}", exc_info=True)
        await callback.answer("Ошибка при открытии закладки")
        await callback.message.answer("Произошла ошибка при обработке закладки.")
    except Exception as e:
        logger.error(f"Ошибка при открытии закладки: {e}", exc_info=True)
        await callback.answer("Ошибка при открытии закладки")
        await callback.message.answer(
            f"Не удалось загрузить главу из закладки.",
            reply_markup=get_main_keyboard()
        )


@router.callback_query(F.data.regexp(r'^add_bookmark_(\d+)_(\d+)$'))
async def add_bookmark_from_plan(callback: CallbackQuery, state: FSMContext):
    """Обработчик для добавления закладки из плана чтения (по id книги и главе)"""
    m = re.match(r'^add_bookmark_(\d+)_(\d+)$', callback.data)
    if not m:
        await callback.answer("Ошибка данных закладки")
        return
    book_id, chapter = int(m.group(1)), int(m.group(2))
    from database.universal_manager import universal_db_manager as db_manager
    user_id = callback.from_user.id
    book_name = bible_data.get_book_name(book_id)
    display_text = f"{book_name} {chapter}"
    # Добавляем в БД
    try:
        await db_manager.add_user(user_id, callback.from_user.username or "", callback.from_user.first_name or "")
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

        if not bookmark_exists:
            await db_manager.add_bookmark(user_id, book_id, chapter, display_text)
        await callback.answer("Закладка добавлена")
    except Exception as e:
        await callback.answer("Ошибка при добавлении закладки")
