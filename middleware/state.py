"""
Middleware для работы с состоянием пользователя.
"""
import logging
from typing import Dict, Any, Callable, Awaitable, Tuple, Union
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
from aiogram.fsm.context import FSMContext

# Инициализация логгера
logger = logging.getLogger(__name__)


async def get_chosen_book(state: FSMContext) -> int:
    """
    Получить ID выбранной книги из состояния.

    Args:
        state: Объект FSMContext

    Returns:
        ID книги или None, если книга не выбрана
    """
    data = await state.get_data()
    return data.get('chosen_book')


async def set_chosen_book(state: FSMContext, book_id: int) -> None:
    """
    Установить ID выбранной книги в состоянии.

    Args:
        state: Объект FSMContext
        book_id: ID книги
    """
    await state.update_data(chosen_book=book_id)


async def get_current_chapter(state: FSMContext) -> int:
    """
    Получить номер текущей главы из состояния.

    Args:
        state: Объект FSMContext

    Returns:
        Номер главы или None, если глава не выбрана
    """
    data = await state.get_data()
    return data.get('current_chapter')


async def set_current_chapter(state: FSMContext, chapter: int) -> None:
    """
    Установить номер текущей главы в состоянии.

    Args:
        state: Объект FSMContext
        chapter: Номер главы
    """
    await state.update_data(current_chapter=chapter)


async def get_current_translation(state: FSMContext) -> str:
    """Получает текущий перевод из состояния"""
    data = await state.get_data()

    # Пытаемся получить перевод из состояния
    translation = data.get("current_translation", "rst")

    return translation


async def set_current_translation(state: FSMContext, translation: str) -> None:
    """
    Установить код текущего перевода в состоянии.

    Args:
        state: Объект FSMContext
        translation: Код перевода
    """
    await state.update_data(current_translation=translation)


async def get_page(state: FSMContext) -> int:
    """
    Получить текущую страницу из состояния.

    Args:
        state: Объект FSMContext

    Returns:
        Номер страницы или 0 по умолчанию
    """
    data = await state.get_data()
    return data.get('page', 0)


async def set_page(state: FSMContext, page: int) -> None:
    """
    Установить текущую страницу в состоянии.

    Args:
        state: Объект FSMContext
        page: Номер страницы
    """
    await state.update_data(page=page)


async def get_bookmarks(state: FSMContext) -> Dict:
    """
    Получить список закладок из состояния.

    Args:
        state: Объект FSMContext

    Returns:
        Словарь закладок
    """
    data = await state.get_data()
    bookmarks = data.get('bookmarks', {})

    # Проверяем и обновляем закладки, если они в старом формате
    updated_bookmarks = {}
    for key, value in bookmarks.items():
        if isinstance(value, dict):
            # Проверяем наличие display_text
            if 'display_text' not in value or not isinstance(value['display_text'], str):
                # Добавляем display_text, если его нет или он неверного типа
                book_id = value.get('book_id')
                chapter = value.get('chapter')
                if book_id and chapter:
                    try:
                        # Импортируем здесь для избежания циклических импортов
                        from utils.bible_data import bible_data
                        book_name = bible_data.get_book_name(book_id)
                        value['display_text'] = f"{book_name} {chapter}"
                    except Exception as e:
                        logger.error(
                            f"Ошибка при обновлении формата закладки: {e}")
                        value['display_text'] = f"Книга {book_id}, глава {chapter}"

            updated_bookmarks[key] = value

    # Если были обновления, сохраняем изменения
    if updated_bookmarks and updated_bookmarks != bookmarks:
        await state.update_data(bookmarks=updated_bookmarks)
        return updated_bookmarks

    return bookmarks


async def add_bookmark(state: FSMContext, book_id: int, chapter: int, display_text: str) -> None:
    """
    Добавить закладку в состояние.

    Args:
        state: Объект FSMContext
        book_id: ID книги
        chapter: Номер главы
        display_text: Отображаемый текст закладки
    """
    bookmarks = await get_bookmarks(state)

    # Ключ для закладки
    key = f"{book_id}_{chapter}"

    # Добавляем закладку
    bookmarks[key] = {
        'book_id': book_id,
        'chapter': chapter,
        'display_text': display_text,
        'timestamp': None
    }

    # Обновляем состояние
    await state.update_data(bookmarks=bookmarks)


async def remove_bookmark(state: FSMContext, book_id: int, chapter: int) -> None:
    """
    Удалить закладку из состояния.

    Args:
        state: Объект FSMContext
        book_id: ID книги
        chapter: Номер главы
    """
    bookmarks = await get_bookmarks(state)

    # Ключ для закладки
    key = f"{book_id}_{chapter}"

    # Удаляем закладку, если она существует
    if key in bookmarks:
        del bookmarks[key]

        # Обновляем состояние
        await state.update_data(bookmarks=bookmarks)


async def clear_bookmarks(state: FSMContext) -> None:
    """
    Очистить все закладки в состоянии.

    Args:
        state: Объект FSMContext
    """
    await state.update_data(bookmarks={})


async def get_translation_from_db(bot_or_dispatcher, user_id: int) -> str:
    """
    Получает предпочитаемый перевод пользователя из БД.

    Args:
        bot_or_dispatcher: Объект бота или диспетчера, где хранится ссылка на БД
        user_id: ID пользователя Telegram

    Returns:
        Код перевода (по умолчанию "rst")
    """
    try:
        # Проверяем, содержит ли объект прямой доступ к БД (если это диспетчер)
        if hasattr(bot_or_dispatcher, "__getitem__"):
            try:
                db = bot_or_dispatcher["db"]
                if db:
                    translation = await db.get_user_translation(user_id)
                    return translation
            except (KeyError, TypeError):
                pass

        # Проверяем, есть ли метод get (если это бот в aiobot 2.x)
        if hasattr(bot_or_dispatcher, "get"):
            db = bot_or_dispatcher.get('db')
            if db:
                translation = await db.get_user_translation(user_id)
                return translation
    except Exception as e:
        # В случае ошибки возвращаем значение по умолчанию
        logger.error(f"Ошибка при получении перевода из БД: {e}")

    # Возвращаем значение по умолчанию
    return "rst"


class StateMiddleware(BaseMiddleware):
    """
    Middleware для работы с состоянием пользователя через FSMContext.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """
        Метод для обработки события и добавления состояния пользователя.

        Args:
            handler: Функция-обработчик события
            event: Объект события Telegram
            data: Словарь с данными события

        Returns:
            Результат выполнения обработчика
        """
        # Вызываем обработчик
        return await handler(event, data)
