"""
Обработчики текстовых сообщений бота.
"""
import logging
import re
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext

from keyboards.main import (
    get_main_keyboard,
    create_book_keyboard,
    create_navigation_keyboard,
)
from utils.api_client import bible_api
from utils.bible_data import bible_data
from utils.text_utils import split_text
from middleware.state import (
    get_chosen_book, set_chosen_book,
    get_current_chapter, set_current_chapter,
    get_current_translation, set_current_translation,
    get_page, set_page,
    get_translation_from_db
)
from config.settings import ENABLE_WORD_SEARCH

# Инициализация логгера
logger = logging.getLogger(__name__)

# Создаем роутер для текстовых сообщений
router = Router()

# Словарь для хранения состояния поиска
user_search_state = {}


@router.message(F.text == "📖 Выбрать книгу")
async def select_book(message: Message, state: FSMContext):
    """Обработчик выбора книги"""
    await set_page(state, 0)
    page = await get_page(state)
    await message.answer(
        "Выберите книгу:",
        reply_markup=create_book_keyboard(page)
    )


@router.message(F.text == "📊 Случайный стих")
async def random_verse(message: Message, state: FSMContext, db=None):
    """Обработчик для получения случайного стиха"""
    try:
        # Сначала пытаемся получить перевод из БД
        user_id = message.from_user.id

        translation = None

        # Если db доступен напрямую через параметр
        if db:
            translation = await db.get_user_translation(user_id)
            logger.debug(f"Перевод получен из db параметра: {translation}")

        # Если перевод не получен, попробуем получить из состояния
        if not translation:
            translation = await get_current_translation(state)
            logger.debug(f"Перевод получен из состояния: {translation}")

        # Получаем случайный стих
        text = await bible_api.get_random_verse(translation)
        await message.answer(text)

    except Exception as e:
        logger.error(f"Ошибка при получении случайного стиха: {e}")
        await message.answer("Произошла ошибка при получении случайного стиха. Попробуйте позже.")


@router.message(F.text == "❓ Помощь")
async def help_message(message: Message):
    """Обработчик для получения справки"""
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


@router.message(F.text == "📝 Мои закладки")
async def show_bookmarks_message(message: Message, state: FSMContext):
    """Обработчик для показа закладок через текстовую команду"""
    from handlers.bookmarks import show_bookmarks
    await show_bookmarks(message, state)


@router.message(F.text == "🔄 Сменить перевод")
async def change_translation_message(message: Message):
    """Обработчик для смены перевода через текстовую команду"""
    from keyboards.main import create_translations_keyboard
    await message.answer(
        "Выберите перевод Библии:",
        reply_markup=create_translations_keyboard()
    )


async def is_chapter_bookmarked(user_id: int, book_id: int, chapter: int, db) -> bool:
    """
    Проверяет, добавлена ли глава в закладки

    Args:
        user_id: ID пользователя
        book_id: ID книги
        chapter: Номер главы
        db: Объект базы данных

    Returns:
        True, если глава в закладках, иначе False
    """
    if not db:
        logger.warning("Объект db не доступен при проверке закладки")
        return False

    try:
        # Получаем все закладки пользователя
        bookmarks = await db.get_bookmarks(user_id)

        # Проверяем, есть ли среди них нужная
        for bm_book_id, bm_chapter, _ in bookmarks:
            if bm_book_id == book_id and bm_chapter == chapter:
                logger.info(
                    f"Глава {book_id}:{chapter} найдена в закладках пользователя {user_id}")
                return True

        logger.info(
            f"Глава {book_id}:{chapter} не найдена в закладках пользователя {user_id}")
        return False
    except Exception as e:
        logger.error(f"Ошибка при проверке статуса закладки: {e}")
        return False


@router.message(F.text.regexp(r'^\d+$'))
async def chapter_input(message: Message, state: FSMContext, db=None):
    """Обработчик ввода номера главы"""
    book_id = await get_chosen_book(state)
    if not book_id:
        await message.answer(
            "Сначала выберите книгу с помощью кнопки '📖 Выбрать книгу'",
            reply_markup=get_main_keyboard()
        )
        return

    chapter = int(message.text)

    # Получаем максимальное число глав для данной книги
    max_chapters = bible_data.max_chapters.get(book_id, 1)

    if chapter < 1 or chapter > max_chapters:
        await message.answer(
            f"Пожалуйста, введите номер главы от 1 до {max_chapters}",
            reply_markup=get_main_keyboard()
        )
        return

    # Сохраняем выбранную главу
    await set_current_chapter(state, chapter)

    # Получаем название книги и перевод
    book_name = bible_data.get_book_name(book_id)
    translation = await get_current_translation(state)

    try:
        text = await bible_api.get_formatted_chapter(book_id, chapter, translation)

        if text.startswith("Ошибка:"):
            await message.answer(
                f"Произошла ошибка при загрузке главы {chapter} книги {book_name}.",
                reply_markup=get_main_keyboard()
            )
            return

        # Проверяем, добавлена ли глава в закладки
        is_bookmarked = False
        if db:
            is_bookmarked = await is_chapter_bookmarked(message.from_user.id, book_id, chapter, db)
            logger.info(
                f"Статус закладки для главы {book_id}:{chapter}: {is_bookmarked}")

        # Определяем, есть ли предыдущие/следующие главы
        has_previous = chapter > 1
        has_next = chapter < max_chapters

        # Отправляем текст с разбивкой
        for part in split_text(text):
            await message.answer(part)

        # Отправляем клавиатуру навигации
        await message.answer(
            f"{book_name}, глава {chapter}",
            reply_markup=create_navigation_keyboard(
                has_previous, has_next, is_bookmarked)
        )
    except Exception as e:
        logger.error(f"Ошибка при получении текста главы: {e}")
        await message.answer(
            f"Произошла ошибка при загрузке главы {chapter} книги {book_name}. "
            f"Пожалуйста, попробуйте позже.",
            reply_markup=get_main_keyboard()
        )


@router.message(F.text == "🔍 Найти стих")
async def search_verse(message: Message):
    """Обработчик поиска стихов"""
    await message.answer(
        "Введите ссылку на стих в формате:\n"
        "<b>Книга глава:стих</b>\n\n"
        "Например: <code>Быт 1:1</code> или <code>Ин 3:16</code>"
    )


@router.message(
    lambda msg: re.match(r'^[а-яА-Я0-9]+\s+\d+[:]\d+', msg.text) is not None
)
async def verse_reference(message: Message, state: FSMContext):
    """Обработчик ссылок на стихи в формате 'Книга глава:стих'"""
    try:
        # Парсим ссылку
        match = re.match(r'^([а-яА-Я0-9]+)\s+(\d+)[:](\d+)', message.text)
        if not match:
            return

        book_code, chapter_str, verse_str = match.groups()
        book_id = bible_data.get_book_id(book_code)

        if not book_id:
            await message.answer(f"Книга '{book_code}' не найдена.")
            return

        chapter = int(chapter_str)
        verse = int(verse_str)

        # Проверка допустимости главы
        max_chapter = bible_data.max_chapters.get(book_id, 0)

        logger.info(
            f"Ссылка на стих: {book_code} (ID: {book_id}) {chapter}:{verse}, макс. глав: {max_chapter}")

        if chapter < 1 or chapter > max_chapter:
            book_name = bible_data.get_book_name(book_id)
            await message.answer(
                f"Книга «{book_name}» содержит {max_chapter} глав.\n"
                f"Пожалуйста, введите номер главы от 1 до {max_chapter}."
            )
            return

        # Получаем и отправляем текст стиха/главы
        try:
            translation = await get_current_translation(state)
            text = await bible_api.get_formatted_chapter(
                book_id, chapter, translation
            )

            # Проверка на ошибку при получении текста
            if text.startswith("Ошибка:"):
                await message.answer(f"Глава не найдена. Попробуйте другую главу.")
                return

            # Сохраняем текущую книгу и главу
            await set_chosen_book(state, book_id)
            await set_current_chapter(state, chapter)

            # Отправляем текст с разбивкой
            for part in split_text(text):
                await message.answer(part)

            # Добавляем клавиатуру навигации
            has_previous = chapter > 1
            has_next = chapter < max_chapter
            await message.answer(
                "Выберите действие:",
                reply_markup=create_navigation_keyboard(has_previous, has_next)
            )
        except Exception as e:
            logger.error(f"API error: {e}", exc_info=True)
            await message.answer(f"Не удалось получить текст главы. Пожалуйста, попробуйте позже.")
    except Exception as e:
        logger.error(f"Ошибка в обработке ссылки на стих: {e}", exc_info=True)
        await message.answer("Не удалось найти указанный отрывок. Проверьте правильность ссылки.")


# Обработчики поиска по слову (активны только если включены в настройках)
if ENABLE_WORD_SEARCH:
    @router.message(F.text == "🔍 Поиск по слову")
    async def search_word_command(message: Message, state: FSMContext):
        """Обработчик для поиска слов в тексте Библии"""
        # Сохраняем состояние ожидания поискового запроса
        await state.set_state("waiting_for_search_query")

        # Создаем клавиатуру с кнопкой отмены
        kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="❌ Отмена поиска")]
            ],
            resize_keyboard=True
        )

        await message.answer(
            "Введите слово или фразу для поиска в тексте Библии (минимум 3 символа):",
            reply_markup=kb
        )

    @router.message(F.text == "❌ Отмена поиска")
    async def cancel_search(message: Message, state: FSMContext):
        """Обработчик для отмены поиска"""
        current_state = await state.get_state()
        if current_state == "waiting_for_search_query":
            await state.clear()

        await message.answer("Поиск отменен. Вернулись в главное меню.", reply_markup=get_main_keyboard())

    @router.message(lambda message: message.text and not message.text.startswith('/'))
    async def process_search_query(message: Message, state: FSMContext, db=None):
        """Обработчик для поисковых запросов"""
        current_state = await state.get_state()

        if current_state != "waiting_for_search_query":
            return

        search_query = message.text.strip()

        # Сбрасываем состояние
        await state.clear()

        # Отправляем сообщение о начале поиска
        await message.answer(f"Ищу '{search_query}' в тексте Библии...", reply_markup=get_main_keyboard())

        # Проверяем длину запроса
        if len(search_query) < 3:
            await message.answer("Поисковый запрос должен содержать минимум 3 символа. Попробуйте еще раз.")
            return

        # Выполняем поиск
        translation = None

        # Если db доступен напрямую через параметр
        if db:
            translation = await db.get_user_translation(message.from_user.id)
            logger.debug(f"Перевод получен из db параметра: {translation}")

        # Если перевод не получен, попробуем получить из состояния
        if not translation:
            translation = await get_current_translation(state)
            logger.debug(f"Перевод получен из состояния: {translation}")

        try:
            # Используем API-клиент для поиска
            results = await bible_api.search_bible_text(search_query, translation)

            if not results:
                await message.answer(f"По запросу '{search_query}' ничего не найдено.")
                return

            # Логируем структуру результатов для отладки
            logger.info(
                f"Search results structure: {type(results)} - First item: {results[0] if results else None}")

            result_text = f"Результаты поиска '{search_query}' ({len(results)} найдено):\n\n"

            for i, item in enumerate(results, 1):
                if i > 20:  # Ограничиваем вывод первыми 20 результатами
                    result_text += f"\n... и еще {len(results) - 20} результатов"
                    break

                # Проверяем формат результатов и адаптируем извлечение данных
                if isinstance(item, dict):
                    if 'reference' in item and 'text' in item:
                        result_text += f"{i}. {item['reference']}: {item['text']}\n\n"
                    else:
                        # Если ключи отличаются, ищем альтернативные ключи
                        reference = item.get('info', '') or item.get(
                            'reference', '') or ''
                        text = item.get('verse', '') or item.get(
                            'text', '') or str(item)
                        result_text += f"{i}. {reference}: {text}\n\n"
                else:
                    # Если результаты в другом формате, выводим их как есть
                    result_text += f"{i}. {item}\n\n"

            # Разбиваем результат, если он слишком длинный
            for part in split_text(result_text):
                await message.answer(part)

        except Exception as e:
            logging.error(f"Search error: {e}", exc_info=True)
            await message.answer(f"Ошибка при поиске: {str(e)}")


# Обработчик для всех других текстовых сообщений
@router.message(F.text)
async def other_text(message: Message):
    """Обработчик для других текстовых сообщений"""
    await message.answer(
        "Я не понимаю эту команду. Воспользуйтесь кнопками меню или напишите /help для справки.",
        reply_markup=get_main_keyboard()
    )
