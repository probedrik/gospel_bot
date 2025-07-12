"""
Обработчики команд и запросов, связанных с закладками.
"""
import time
import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from keyboards.main import create_bookmarks_keyboard, get_main_keyboard
from utils.api_client import bible_api
from utils.bible_data import bible_data
from utils.text_utils import split_text
from middleware.state import (
    get_bookmarks, clear_bookmarks, remove_bookmark
)

# Инициализация логгера
logger = logging.getLogger(__name__)

# Создаем роутер для обработки закладок
router = Router()


@router.message(F.text == "📝 Мои закладки")
async def show_bookmarks(message: Message, state: FSMContext, db=None):
    """Обработчик для отображения списка закладок пользователя"""
    user_id = message.from_user.id
    start_time = time.time()
    logger.info(f"Пользователь {user_id} запросил свои закладки")

    # Используем напрямую менеджер БД
    from database.db_manager import db_manager

    db_bookmarks = []
    state_bookmarks = {}
    combined_bookmarks = []

    # 1. Пробуем получить закладки из БД
    try:
        logger.info(f"Запрашиваем закладки из БД для пользователя {user_id}")
        db_bookmarks = await db_manager.get_bookmarks(user_id)

        if db_bookmarks is None:
            logger.error("get_bookmarks вернул None вместо списка")
            db_bookmarks = []

        logger.info(f"Получено {len(db_bookmarks)} закладок из БД")

        # Логируем тип данных для отладки
        logger.info(
            f"Тип закладок из БД: {type(db_bookmarks).__name__}, Элементов: {len(db_bookmarks)}")
        if db_bookmarks:
            # Логируем первые 3 закладки
            for i, bm in enumerate(db_bookmarks[:3]):
                logger.info(f"Закладка {i+1} из БД: {bm}")
    except Exception as e:
        logger.error(
            f"Ошибка при получении закладок из БД: {e}", exc_info=True)
        db_bookmarks = []

    # 2. Получаем закладки из состояния
    try:
        logger.info("Запрашиваем закладки из состояния FSM")
        state_bookmarks = await get_bookmarks(state)

        if state_bookmarks is None:
            logger.error("get_bookmarks (state) вернул None вместо словаря")
            state_bookmarks = {}

        logger.info(f"Получено {len(state_bookmarks)} закладок из состояния")

        # Логируем тип данных для отладки
        logger.info(
            f"Тип закладок из состояния: {type(state_bookmarks).__name__}, Ключей: {len(state_bookmarks)}")
        if state_bookmarks:
            # Логируем первые 3 закладки
            for i, (key, value) in enumerate(list(state_bookmarks.items())[:3]):
                logger.info(
                    f"Закладка {i+1} из состояния: ключ={key}, значение={value}")
    except Exception as e:
        logger.error(
            f"Ошибка при получении закладок из состояния: {e}", exc_info=True)
        state_bookmarks = {}  # Сбрасываем в пустой словарь в случае ошибки

    # 3. Объединяем закладки (приоритет у БД)
    try:
        # Создаем словарь для отслеживания уникальности по (book_id, chapter)
        unique_bookmarks = {}

        # Сначала добавляем закладки из БД
        for bookmark in db_bookmarks:
            try:
                if bookmark and len(bookmark) >= 3:
                    book_id, chapter, display_text = bookmark[0], bookmark[1], bookmark[2]

                    # Проверяем типы данных
                    if not (isinstance(book_id, int) and isinstance(chapter, int) and isinstance(display_text, str)):
                        logger.warning(
                            f"Некорректные типы данных в закладке из БД: {bookmark}")
                        continue

                    key = f"{book_id}_{chapter}"
                    unique_bookmarks[key] = (book_id, chapter, display_text)
                else:
                    logger.warning(
                        f"Некорректный формат закладки из БД: {bookmark}")
            except Exception as e:
                logger.error(f"Ошибка при обработке закладки из БД: {e}")

        # Затем добавляем закладки из состояния (если их нет в БД)
        for key, data in state_bookmarks.items():
            try:
                if key not in unique_bookmarks and isinstance(data, dict):
                    book_id = data.get('book_id')
                    chapter = data.get('chapter')
                    display_text = data.get('display_text')

                    # Проверяем типы данных
                    if (book_id is not None and chapter is not None and display_text is not None and
                            isinstance(book_id, int) and isinstance(chapter, int) and isinstance(display_text, str)):

                        # Дополнительно - сразу добавляем эту закладку в БД, раз она есть только в состоянии
                        try:
                            logger.info(
                                f"Сохраняем закладку из состояния в БД: {book_id}_{chapter}")
                            await db_manager.add_user(user_id, message.from_user.username or "", message.from_user.first_name or "")
                            await db_manager.add_bookmark(user_id, book_id, chapter, display_text)
                            logger.info(
                                f"Закладка {display_text} сохранена в БД из обработчика show_bookmarks")
                        except Exception as add_e:
                            logger.error(
                                f"Ошибка при сохранении закладки в БД: {add_e}")

                        unique_bookmarks[key] = (
                            book_id, chapter, display_text)
                    else:
                        logger.warning(
                            f"Некорректные типы данных в закладке из состояния: {data}")
                elif not isinstance(data, dict):
                    logger.warning(
                        f"Некорректный формат данных закладки в состоянии: {data}")
            except Exception as e:
                logger.error(
                    f"Ошибка при обработке закладки из состояния: {e}")

        # Преобразуем в список
        combined_bookmarks = list(unique_bookmarks.values())
        logger.info(
            f"Объединено {len(combined_bookmarks)} уникальных закладок")
    except Exception as e:
        logger.error(f"Ошибка при объединении закладок: {e}", exc_info=True)
        # В случае ошибки - попробуем использовать данные только из состояния
        combined_bookmarks = []
        try:
            for key, data in state_bookmarks.items():
                if isinstance(data, dict):
                    book_id = data.get('book_id')
                    chapter = data.get('chapter')
                    display_text = data.get('display_text')
                    if book_id and chapter and display_text:
                        combined_bookmarks.append(
                            (book_id, chapter, display_text))
            logger.info(
                f"После ошибки использовано {len(combined_bookmarks)} закладок из состояния")
        except Exception as e2:
            logger.error(f"Критическая ошибка при обработке закладок: {e2}")

    # 4. Отображаем закладки
    try:
        if combined_bookmarks:
            # Логируем форматы закладок перед созданием клавиатуры
            logger.info(f"Форматы закладок перед созданием клавиатуры:")
            # Логируем первые 3 закладки
            for i, bm in enumerate(combined_bookmarks[:3]):
                logger.info(f"Закладка {i+1} для клавиатуры: {bm}")

            await message.answer(
                "Ваши закладки:",
                reply_markup=create_bookmarks_keyboard(combined_bookmarks)
            )
            elapsed = time.time() - start_time
            logger.info(
                f"Отображено {len(combined_bookmarks)} закладок за {elapsed:.2f} сек")
        else:
            logger.info("Закладки не найдены ни в БД, ни в состоянии")
            await message.answer(
                "У вас пока нет сохраненных закладок. "
                "Чтобы добавить закладку, откройте главу книги и нажмите кнопку 'Добавить закладку'.",
                reply_markup=get_main_keyboard()
            )
    except Exception as e:
        logger.error(f"Ошибка при отображении закладок: {e}", exc_info=True)
        await message.answer(
            "Произошла ошибка при отображении закладок. Пожалуйста, попробуйте позже.",
            reply_markup=get_main_keyboard()
        )


@router.message(Command("clear_bookmarks"))
async def clear_all_bookmarks(message: Message, state: FSMContext):
    """Удалить все закладки пользователя"""
    await clear_bookmarks(state)
    await message.answer("Все закладки удалены.")
