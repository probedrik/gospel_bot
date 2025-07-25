"""
Обработчики текстовых сообщений бота.
"""
from config.settings import MARKDOWN_ENABLED, MARKDOWN_MODE, MARKDOWN_BOLD_TITLE, MARKDOWN_QUOTE, MARKDOWN_ESCAPE, ENABLE_VERSE_NUMBERS, BIBLE_MARKDOWN_ENABLED, BIBLE_MARKDOWN_MODE
import logging
import re
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.enums.parse_mode import ParseMode
from config.ai_settings import ENABLE_GPT_EXPLAIN, AI_OWNER_ID, AI_UNLIMITED_USERS, AI_DAILY_LIMIT
from config.settings import ENABLE_DELETE_RELATED_MESSAGES_DEFAULT

from keyboards.main import (
    get_main_keyboard,
    create_book_keyboard,
    create_navigation_keyboard,
)
from utils.api_client import bible_api, ask_gpt_explain
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
from handlers.verse_reference import get_verse_by_reference
from utils.topics import get_topics_list, get_verses_for_topic
from utils.lopukhin_commentary import lopukhin_commentary
from database.universal_manager import universal_db_manager as db_manager

import datetime

# Инициализация логгера
logger = logging.getLogger(__name__)

# Создаем роутер для текстовых сообщений
router = Router()

# Словарь для хранения состояния поиска
user_search_state = {}

# Счетчик ИИ-запросов: user_id -> {'count': int, 'date': date}
_ai_daily_counter = {}


def ai_check_and_increment(user_id: int) -> bool:
    """
    Проверяет и увеличивает счетчик ИИ-запросов для пользователя.
    Возвращает True, если лимит не превышен, иначе False.
    """
    today = datetime.date.today()
    if user_id in AI_UNLIMITED_USERS:
        return True
    rec = _ai_daily_counter.get(user_id)
    if rec and rec['date'] == today:
        if rec['count'] >= AI_DAILY_LIMIT:
            return False
        rec['count'] += 1
    else:
        _ai_daily_counter[user_id] = {'count': 1, 'date': today}
    return True


async def ai_check_and_increment_db(user_id: int) -> bool:
    """
    Проверяет и увеличивает счетчик ИИ-запросов для пользователя в БД.
    Возвращает True, если лимит не превышен, иначе False.
    """
    from config.ai_settings import AI_UNLIMITED_USERS, AI_DAILY_LIMIT
    if user_id in AI_UNLIMITED_USERS:
        return True
    today = datetime.date.today().isoformat()
    count = await db_manager.get_ai_limit(user_id, today)
    if count >= AI_DAILY_LIMIT:
        return False
    await db_manager.increment_ai_limit(user_id, today)
    return True


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
        user_id = message.from_user.id
        translation = None
        if db:
            translation = await db.get_user_translation(user_id)
            logger.debug(f"Перевод получен из db параметра: {translation}")
        if not translation:
            translation = await get_current_translation(state)
            logger.debug(f"Перевод получен из состояния: {translation}")
        text = await bible_api.get_random_verse(translation)
        await message.answer(text)
        # Попробуем извлечь book и chapter для кнопки "Открыть всю главу"
        import re
        match = re.search(r"([А-Яа-яёЁ\s]+)\s(\d+):\d+", text)
        if match:
            book_raw = match.group(1).strip().lower()
            chapter = match.group(2)
            book_abbr = bible_data.normalize_book_name(book_raw)
            if bible_data.get_book_id(book_abbr):
                kb = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(
                            text="Открыть всю главу", callback_data=f"open_chapter_{book_abbr}_{chapter}")]
                    ]
                )
                await message.answer("Хотите открыть всю главу?", reply_markup=kb)
    except Exception as e:
        logger.error(f"Ошибка при получении случайного стиха: {e}")
        await message.answer("Произошла ошибка при получении случайного стиха. Попробуйте позже.")


@router.message(F.text == "❓ Помощь")
async def help_message(message: Message):
    """Обработчик для получения справки"""
    help_text = (
        "<b>📚 Помощь по использованию бота</b>\n\n"
        "Возможности:\n"
        "• 📖 Быстрый выбор книги и главы\n"
        "• 🔍 Поиск стихов по ссылке (например, <code>Ин 3:16</code>)\n"
        "• 📝 Закладки на любимые главы и быстрый доступ к ним\n"
        "• 🎯 Тематические подборки стихов (кнопка '🎯 Темы' в главном меню)\n"
        "• 💬 Поиск по словам (если включено)\n"
        "• 📊 Случайный стих\n"
        "• 🧑‍🏫 Толкования проф. Лопухина по каждому стиху и главе (постранично, с кнопками)\n"
        "• 🤖 Объяснение смысла главы или стиха с помощью ИИ (кнопка всегда доступна, лимит 5 в сутки)\n"
        "• Кэширование популярных ИИ-ответов для экономии лимита\n"
        "• Включение/отключение автоудаления сообщений: /clean_on и /clean_off\n"
        "\n"
        "<b>Как сменить перевод Библии?</b>\n"
        "Отправьте команду <b>🔄 Сменить перевод</b> в чат или выберите соответствующий пункт в этом меню.\n"
        "\n"
        "<b>Как пользоваться:</b>\n"
        "- Выберите книгу и главу через меню или введите ссылку (например, <code>Ин 3</code>, <code>Быт 1:1</code>)\n"
        "- Для каждой главы доступны кнопки: 'Толкование проф. Лопухина' и '🤖 Разбор от ИИ'\n"
        "- Навигируйте по главам с помощью стрелок\n"
        "- Добавляйте и удаляйте закладки\n"
        "- Открывайте толкования и объяснения ИИ в один клик\n"
        "\n"
        "<b>Примеры команд:</b>\n"
        "• /start — Запустить бота\n"
        "• /help — Показать эту справку\n"
        "• /books — Показать список книг\n"
        "• /random — Получить случайный стих\n"
        "• /bookmarks — Показать ваши закладки\n"
        "• /clean_on — Включить автоудаление сообщений\n"
        "• /clean_off — Отключить автоудаление сообщений\n"
    )
    await message.answer(help_text, parse_mode="HTML")


@router.message(F.text == "📝 Мои закладки")
async def show_bookmarks_message(message: Message, state: FSMContext):
    """Обработчик для показа закладок через текстовую команду"""
    from handlers.bookmarks import show_bookmarks
    await show_bookmarks(message, state)


@router.message(F.text == "🔄 Сменить перевод")
async def change_translation_message(message: Message):
    """Обработчик для смены перевода через текстовую команду (скрыт из главного меню, но доступен через справку)"""
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
    book_abbr = None
    for abbr, id_ in bible_data.book_abbr_dict.items():
        if id_ == book_id:
            book_abbr = abbr
            break
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
        from utils.text_utils import get_verses_parse_mode
        parse_mode = get_verses_parse_mode()

        for part in split_text(text):
            await message.answer(part, parse_mode=parse_mode)

        # Создаем кнопки действий для главы
        from utils.bible_data import create_chapter_action_buttons
        extra_buttons = await create_chapter_action_buttons(book_id, chapter, user_id=message.from_user.id)

        # Отправляем объединенную клавиатуру навигации с дополнительными кнопками
        await message.answer(
            "Выберите действие:",
            reply_markup=create_navigation_keyboard(
                has_previous, has_next, is_bookmarked, extra_buttons)
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
        "Введите ссылку на стих или отрывок в одном из форматов:\n"
        "<b>Книга глава</b> — вся глава (например: <code>Ин 3</code>)\n"
        "<b>Книга глава:стих</b> — один стих (например: <code>Ин 3:16</code>)\n"
        "<b>Книга глава:стих-стих</b> — диапазон стихов (например: <code>Ин 3:16-18</code>)"
    )


@router.message(
    lambda msg: re.match(
        r'^([а-яА-ЯёЁ0-9\s]+)\s+(\d+)(?::(\d+)(?:-(\d+))?)?$', msg.text.strip(), re.IGNORECASE) is not None
)
async def verse_reference(message: Message, state: FSMContext):
    """Обработчик ссылок на стихи, диапазоны и главы: 'Книга глава', 'Книга глава:стих', 'Книга глава:стих-стих'"""
    try:
        text, meta = await get_verse_by_reference(state, message.text)

        # Используем правильные настройки для библейского текста
        from utils.text_utils import get_verses_parse_mode
        parse_mode = get_verses_parse_mode()

        for part in split_text(text):
            await message.answer(part, parse_mode=parse_mode)
        match = re.match(
            r'^([а-яА-ЯёЁ0-9\s]+)\s+(\d+)(?::(\d+)(?:-(\d+))?)?$', message.text.strip(), re.IGNORECASE)
        if match:
            book_raw = match.group(1).strip()
            chapter = int(match.group(2))
            verse = match.group(3)
            book_abbr = bible_data.normalize_book_name(book_raw)
            book_id = bible_data.get_book_id(book_abbr)
            en_book = None
            en_to_ru = {
                "Gen": "Быт", "Exod": "Исх", "Lev": "Лев", "Num": "Чис", "Deut": "Втор", "Josh": "Нав", "Judg": "Суд", "Ruth": "Руф",
                "1Sam": "1Цар", "2Sam": "2Цар", "1Kgs": "3Цар", "2Kgs": "4Цар", "1Chr": "1Пар", "2Chr": "2Пар", "Ezra": "Езд", "Neh": "Неем",
                "Esth": "Есф", "Job": "Иов", "Ps": "Пс", "Prov": "Прит", "Eccl": "Еккл", "Song": "Песн", "Isa": "Ис", "Jer": "Иер",
                "Lam": "Плач", "Ezek": "Иез", "Dan": "Дан", "Hos": "Ос", "Joel": "Иоил", "Amos": "Ам", "Obad": "Авд", "Jonah": "Ион",
                "Mic": "Мих", "Nah": "Наум", "Hab": "Авв", "Zeph": "Соф", "Hag": "Агг", "Zech": "Зах", "Mal": "Мал",
                "Matt": "Мф", "Mark": "Мк", "Luke": "Лк", "John": "Ин", "Acts": "Деян", "Jas": "Иак", "1Pet": "1Пет", "2Pet": "2Пет",
                "1John": "1Ин", "2John": "2Ин", "3John": "3Ин", "Jude": "Иуд", "Rom": "Рим", "1Cor": "1Кор", "2Cor": "2Кор",
                "Gal": "Гал", "Eph": "Еф", "Phil": "Флп", "Col": "Кол", "1Thess": "1Фес", "2Thess": "2Фес", "1Tim": "1Тим",
                "2Tim": "2Тим", "Titus": "Тит", "Phlm": "Флм", "Heb": "Евр", "Rev": "Откр"
            }
            for en, ru in en_to_ru.items():
                if ru == book_abbr:
                    en_book = en
                    break
            buttons = []
            max_chapters = bible_data.max_chapters.get(book_id, 1)
            has_previous = chapter > 1
            has_next = chapter < max_chapters
            is_bookmarked = False
            # Для главы (если verse отсутствует или == 0): полноценная навигация и кнопки
            if not verse or verse == '0' or verse == 0:
                # Используем умную функцию создания кнопок
                from utils.bible_data import create_chapter_action_buttons
                extra_buttons = await create_chapter_action_buttons(
                    book_id, chapter, en_book, user_id=message.from_user.id
                )

                # Отправляем объединенную клавиатуру навигации с дополнительными кнопками
                await message.answer(
                    "Выберите действие:",
                    reply_markup=create_navigation_keyboard(
                        has_previous, has_next, is_bookmarked, extra_buttons)
                )
            else:
                # Для стиха — как было
                if book_id:
                    buttons.append([
                        InlineKeyboardButton(
                            text="Открыть всю главу",
                            callback_data=f"open_chapter_{book_abbr}_{chapter}"
                        )
                    ])
                # Кнопка толкования Лопухина (проверяем глобальную настройку)
                from config.settings import ENABLE_LOPUKHIN_COMMENTARY
                if ENABLE_LOPUKHIN_COMMENTARY and en_book:
                    commentary = None
                    if verse:
                        commentary = lopukhin_commentary.get_commentary(
                            en_book, chapter, int(verse))
                    if not commentary:
                        commentary = lopukhin_commentary.get_commentary(
                            en_book, chapter, 0)
                    if commentary:
                        # Проверяем сохраненное толкование Лопухина
                        saved_lopukhin_commentary = None
                        if book_id:
                            try:
                                from database.universal_manager import universal_db_manager
                                verse_start = int(verse) if verse else 0
                                saved_lopukhin_commentary = await universal_db_manager.get_saved_commentary(
                                    message.from_user.id, book_id, chapter, chapter, verse_start, verse_start, "lopukhin"
                                )
                            except:
                                pass

                        lopukhin_text = "📚 Обновить толкование Лопухина" if saved_lopukhin_commentary else "Толкование проф. Лопухина"
                        cb_data = f"open_commentary_{en_book}_{chapter}_{verse}"
                        buttons.append([
                            InlineKeyboardButton(
                                text=lopukhin_text,
                                callback_data=cb_data
                            )
                        ])
                if ENABLE_GPT_EXPLAIN:
                    # Проверяем сохраненное ИИ толкование
                    saved_ai_commentary = None
                    if book_id:
                        try:
                            from database.universal_manager import universal_db_manager
                            verse_start = int(verse) if verse else 0
                            saved_ai_commentary = await universal_db_manager.get_saved_commentary(
                                message.from_user.id, book_id, chapter, chapter, verse_start, verse_start, "ai"
                            )
                        except:
                            pass

                    ai_text = "🔄 Обновить толкование ИИ" if saved_ai_commentary else "🤖 Разбор от ИИ"
                    cb_data = f"gpt_explain_{en_book}_{chapter}_{verse}"
                    buttons.append([
                        InlineKeyboardButton(
                            text=ai_text,
                            callback_data=cb_data
                        )
                    ])
                if buttons:
                    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
                    await message.answer("Выберите действие:", reply_markup=kb)
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


def create_topics_keyboard(topics: list) -> list:
    """Создает клавиатуру с темами, используя умную сортировку по длине"""
    buttons = []
    
    # Добавляем заметную кнопку ИИ помощника в начало
    buttons.append([
        InlineKeyboardButton(
            text="🤖✨ Подобрать с ИИ помощником ✨",
            callback_data="ai_assistant"
        )
    ])
    
    # Формируем inline-клавиатуру с умной сортировкой по длине текста
    row = []
    for i, topic in enumerate(topics):
        button = InlineKeyboardButton(text=topic, callback_data=f"topic_{i}")
        
        # Если название темы длинное (больше 18 символов), размещаем на отдельной строке
        if len(topic) > 18:
            # Если есть незавершенный ряд, добавляем его
            if row:
                buttons.append(row)
                row = []
            # Добавляем длинную тему отдельной строкой
            buttons.append([button])
        else:
            # Короткие темы добавляем по 2 в ряд
            row.append(button)
            if len(row) == 2:
                buttons.append(row)
                row = []
    
    # Добавляем оставшиеся кнопки
    if row:
        buttons.append(row)
    
    # Дублируем кнопку ИИ помощника снизу
    buttons.append([
        InlineKeyboardButton(
            text="🤖✨ Подобрать с ИИ помощником ✨",
            callback_data="ai_assistant"
        )
    ])
    
    # Добавляем кнопку возврата в меню
    buttons.append([
        InlineKeyboardButton(
            text="🏠 Вернуться в меню",
            callback_data="back_to_menu"
        )
    ])
    
    return buttons

@router.callback_query(F.data == "back_to_topics")
async def back_to_topics(callback: CallbackQuery):
    """Возвращает к списку тем"""
    from utils.topics import get_topics_list_async
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    topics = await get_topics_list_async()
    
    buttons = create_topics_keyboard(topics)
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text("Выберите тему или воспользуйтесь ИИ помощником:", reply_markup=kb)
    await callback.answer()

@router.message(F.text == "🎯 Темы")
async def show_topics_menu(message: Message):
    from utils.topics import get_topics_list_async
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    topics = await get_topics_list_async()
    
    buttons = create_topics_keyboard(topics)
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("Выберите тему или воспользуйтесь ИИ помощником:", reply_markup=kb)


@router.callback_query(F.data.regexp(r'^topic_(\d+)$'))
async def show_topic_verses(callback: CallbackQuery, state: FSMContext):
    # При выборе новой темы — удалить предыдущий список стихов и все сообщения ниже
    data = await state.get_data() if state else {}
    prev_topic_msg_id = data.get('last_topic_msg_id')
    prev_verse_msg_id = data.get('last_topic_verse_msg_id')
    prev_commentary_msg_id = data.get('last_topic_commentary_msg_id')
    prev_ai_msg_id = data.get('last_topic_ai_msg_id')
    # Удаляем все сообщения ниже текущего (включая предыдущий список стихов, стих, толкования и разборы)
    for msg_id in [prev_topic_msg_id, prev_verse_msg_id, prev_commentary_msg_id, prev_ai_msg_id]:
        if msg_id:
            try:
                await callback.bot.delete_message(callback.message.chat.id, msg_id)
            except Exception:
                pass
    # Показываем новый список стихов
    from utils.topics import get_topics_list_async, get_verses_for_topic_async
    topics = await get_topics_list_async()
    idx = int(callback.data.split('_')[1])
    topic = topics[idx]
    verses = await get_verses_for_topic_async(topic)
    # Формируем inline-клавиатуру с кнопками по 2 в ряд
    buttons = []
    row = []
    for i, v in enumerate(verses):
        row.append(InlineKeyboardButton(text=v, callback_data=f"verse_{v}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    sent = await callback.message.answer(f'<b>{topic}</b>\n\nВыберите стих:', reply_markup=kb, parse_mode="HTML")
    # Сохраняем id сообщения со списком стихов
    if state and sent:
        await state.update_data(last_topic_msg_id=sent.message_id,
                                last_topic_verse_msg_id=None,
                                last_topic_commentary_msg_id=None,
                                last_topic_ai_msg_id=None)
    await callback.answer()


@router.callback_query(F.data.regexp(r'^verse_(.+)$'))
async def topic_verse_callback(callback: CallbackQuery, state: FSMContext):
    verse_ref = callback.data[len('verse_'):]
    from handlers.verse_reference import get_verse_by_reference
    # Удаляем предыдущий стих и все связанные сообщения (включая толкование и разбор от ИИ)
    data = await state.get_data() if state else {}
    prev_verse_msg_id = data.get('last_topic_verse_msg_id')
    prev_commentary_msg_id = data.get('last_topic_commentary_msg_id')
    prev_ai_msg_id = data.get('last_topic_ai_msg_id')
    for msg_id in [prev_verse_msg_id, prev_commentary_msg_id, prev_ai_msg_id]:
        if msg_id:
            try:
                await callback.bot.delete_message(callback.message.chat.id, msg_id)
            except Exception:
                pass
    # Отправить новый стих
    text, _ = await get_verse_by_reference(state, verse_ref)
    sent = None
    for part in split_text(text):
        sent = await callback.message.answer(part)
    # Сохраняем id нового сообщения со стихом
    if sent and state is not None:
        try:
            await state.update_data(last_topic_verse_msg_id=sent.message_id,
                                    last_topic_commentary_msg_id=None,
                                    last_topic_ai_msg_id=None)
        except Exception:
            pass
    # Добавить только inline-кнопки под стихом
    import re
    match = re.match(r"([А-Яа-яёЁ0-9\s]+)\s(\d+)(?::(\d+)(?:-(\d+))?)?", verse_ref)
    if match:
        book_raw = match.group(1).strip().lower()
        chapter = int(match.group(2))
        verse_start = match.group(3)
        verse_end = match.group(4) if match.group(4) else verse_start
        book_abbr = bible_data.normalize_book_name(book_raw)
        book_id = bible_data.get_book_id(book_abbr)
        en_book = None
        en_to_ru = {
            "Gen": "Быт", "Exod": "Исх", "Lev": "Лев", "Num": "Чис", "Deut": "Втор", "Josh": "Нав", "Judg": "Суд", "Ruth": "Руф",
            "1Sam": "1Цар", "2Sam": "2Цар", "1Kgs": "3Цар", "2Kgs": "4Цар", "1Chr": "1Пар", "2Chr": "2Пар", "Ezra": "Езд", "Neh": "Неем",
            "Esth": "Есф", "Job": "Иов", "Ps": "Пс", "Prov": "Прит", "Eccl": "Еккл", "Song": "Песн", "Isa": "Ис", "Jer": "Иер",
            "Lam": "Плач", "Ezek": "Иез", "Dan": "Дан", "Hos": "Ос", "Joel": "Иоил", "Amos": "Ам", "Obad": "Авд", "Jonah": "Ион",
            "Mic": "Мих", "Nah": "Наум", "Hab": "Авв", "Zeph": "Соф", "Hag": "Агг", "Zech": "Зах", "Mal": "Мал",
            "Matt": "Мф", "Mark": "Мк", "Luke": "Лк", "John": "Ин", "Acts": "Деян", "Jas": "Иак", "1Pet": "1Пет", "2Pet": "2Пет",
            "1John": "1Ин", "2John": "2Ин", "3John": "3Ин", "Jude": "Иуд", "Rom": "Рим", "1Cor": "1Кор", "2Cor": "2Кор",
            "Gal": "Гал", "Eph": "Еф", "Phil": "Флп", "Col": "Кол", "1Thess": "1Фес", "2Thess": "2Фес", "1Tim": "1Тим",
            "2Tim": "2Тим", "Titus": "Тит", "Phlm": "Флм", "Heb": "Евр", "Rev": "Откр"
        }
        for en, ru in en_to_ru.items():
            if ru == book_abbr:
                en_book = en
                break

        buttons = []
        action_row = []
        
        # Кнопка "Открыть всю главу"
        if book_id:
            action_row.append(
                InlineKeyboardButton(
                    text="📖 Открыть всю главу",
                    callback_data=f"open_chapter_{book_abbr}_{chapter}"
                )
            )

        # Кнопка толкования Лопухина (проверяем глобальную настройку)
        from config.settings import ENABLE_LOPUKHIN_COMMENTARY
        if ENABLE_LOPUKHIN_COMMENTARY and en_book:
            commentary = None
            if verse_start:
                commentary = lopukhin_commentary.get_commentary(
                    en_book, chapter, int(verse_start))
            if not commentary:
                commentary = lopukhin_commentary.get_commentary(
                    en_book, chapter, 0)
            if commentary:
                # Проверяем есть ли сохраненное толкование Лопухина для правильного текста кнопки
                saved_lopukhin_commentary = None
                if book_id:
                    try:
                        from database.universal_manager import universal_db_manager
                        verse_start_num = int(verse_start) if verse_start else 0
                        verse_end_num = int(verse_end) if verse_end else verse_start_num
                        saved_lopukhin_commentary = await universal_db_manager.get_saved_commentary(
                            callback.from_user.id, book_id, chapter, chapter, verse_start_num, verse_end_num, "lopukhin"
                        )
                    except:
                        pass

                # Определяем текст кнопки
                lopukhin_text = "📚 Обновить толкование Лопухина" if saved_lopukhin_commentary else "Толкование проф. Лопухина"

                # Формируем callback для диапазона стихов
                if verse_start and verse_end and verse_start != verse_end:
                    verse_callback = f"{verse_start}-{verse_end}"
                elif verse_start:
                    verse_callback = verse_start
                else:
                    verse_callback = "0"
                    
                cb_data = f"open_commentary_{en_book}_{chapter}_{verse_callback}"
                action_row.append(
                    InlineKeyboardButton(
                        text=lopukhin_text,
                        callback_data=cb_data
                    )
                )

        # Кнопка ИИ-разбора - используем умную функцию для правильного текста
        if ENABLE_GPT_EXPLAIN and book_id:
            # Проверяем есть ли сохраненное толкование для правильного текста кнопки
            saved_commentary = None
            try:
                from database.universal_manager import universal_db_manager
                verse_start_num = int(verse_start) if verse_start else 0
                verse_end_num = int(verse_end) if verse_end else verse_start_num
                saved_commentary = await universal_db_manager.get_saved_commentary(
                    callback.from_user.id, book_id, chapter, chapter, verse_start_num, verse_end_num, "ai"
                )
            except:
                pass

            # Определяем текст кнопки
            ai_text = "🔄 Обновить толкование ИИ" if saved_commentary else "🤖 Разбор от ИИ"

            # Формируем callback для диапазона стихов
            if verse_start and verse_end and verse_start != verse_end:
                verse_callback = f"{verse_start}-{verse_end}"
            elif verse_start:
                verse_callback = verse_start
            else:
                verse_callback = "0"
                
            cb_data = f"gpt_explain_{en_book}_{chapter}_{verse_callback}"
            action_row.append(
                InlineKeyboardButton(
                    text=ai_text,
                    callback_data=cb_data
                )
            )

        # Добавляем ряд кнопок действий (если есть)
        if action_row:
            buttons.append(action_row)
        
        # Добавляем кнопку "Назад к темам" для готовых тем
        buttons.append([
            InlineKeyboardButton(
                text="⬅️ Назад к темам",
                callback_data="back_to_topics"
            )
        ])

        # Применяем кнопки к сообщению
        if buttons and sent:
            kb = InlineKeyboardMarkup(inline_keyboard=buttons)
            await sent.edit_reply_markup(reply_markup=kb)
    await callback.answer()


# --- Толкование и ИИ-разбор: сохраняем id сообщений для последующего удаления ---
@router.callback_query(F.data.regexp(r'^open_commentary_([A-Za-z0-9]+)_(\d+)_(\d+)$'))
async def open_commentary_callback(callback: CallbackQuery, state: FSMContext):
    match = re.match(
        r'^open_commentary_([A-Za-z0-9]+)_(\d+)_(\d+)$', callback.data)
    if not match:
        await callback.answer("Ошибка запроса")
        return
    book = match.group(1)
    chapter = int(match.group(2))
    verse = int(match.group(3))
    from utils.lopukhin_commentary import lopukhin_commentary
    if verse == 0:
        # Перенаправляем на постраничный просмотр
        await open_commentary_chapter_paginated(callback)
        return
    commentary = lopukhin_commentary.get_commentary(book, chapter, verse)
    if not commentary:
        commentary = lopukhin_commentary.get_commentary(book, chapter, 0)
    if commentary:
        formatted, opts = format_ai_or_commentary(commentary)

        # Получаем информацию о пользователе и книге для кнопок сохранения
        user_id = callback.from_user.id if hasattr(
            callback, "from_user") else callback.message.from_user.id
        from utils.bible_data import bible_data
        ru_book = bible_data.book_synonyms.get(book.lower(), book)
        book_id = bible_data.get_book_id(ru_book)

        if book_id:
            # Проверяем, есть ли уже сохраненное толкование
            from database.universal_manager import universal_db_manager as db_manager
            verse_start = verse if verse != 0 else None
            saved_commentary = await db_manager.get_saved_commentary(
                user_id, book_id, chapter, None, verse_start, verse_start, "lopukhin")

            # Формируем callback_data для кнопки сохранения
            chapter_start = chapter
            chapter_end_str = "0"  # Всегда одна глава
            verse_start_str = str(
                verse_start) if verse_start is not None else "0"
            verse_end_str = str(
                verse_start) if verse_start is not None else "0"

            # Создаем кнопки сохранения
            save_buttons = []
            if saved_commentary:
                save_buttons = [
                    [InlineKeyboardButton(
                        text="🔄 Обновить толкование",
                        callback_data=f"save_commentary_{book_id}_{chapter_start}_{chapter_end_str}_{verse_start_str}_{verse_end_str}_lopukhin")]
                ]
            else:
                save_buttons = [
                    [InlineKeyboardButton(
                        text="💾 Сохранить толкование",
                        callback_data=f"save_commentary_{book_id}_{chapter_start}_{chapter_end_str}_{verse_start_str}_{verse_end_str}_lopukhin")]
                ]

            # Добавляем кнопку "Открыть всю главу" для стихов
            if verse != 0:
                # Получаем русское сокращение книги для callback
                ru_book_abbr = None
                for abbr, b_id in bible_data.book_abbr_dict.items():
                    if b_id == book_id:
                        ru_book_abbr = abbr
                        break

                if ru_book_abbr:
                    open_chapter_button = [
                        InlineKeyboardButton(
                            text="Открыть всю главу",
                            callback_data=f"open_chapter_{ru_book_abbr}_{chapter}"
                        )
                    ]
                    # Добавляем кнопку в начало списка
                    save_buttons.insert(0, open_chapter_button)

            # Отправляем сообщение с кнопками
            if save_buttons:
                keyboard = InlineKeyboardMarkup(inline_keyboard=save_buttons)
                msg = await callback.message.answer(formatted, reply_markup=keyboard, **opts)
            else:
                msg = await callback.message.answer(formatted, **opts)

            # Сохраняем данные толкования в состоянии для возможного сохранения
            if state:
                await state.update_data(
                    last_lopukhin_commentary=commentary,
                    last_lopukhin_reference=f"{ru_book} {chapter}:{verse}" if verse != 0 else f"{ru_book} {chapter}",
                    last_lopukhin_book_id=book_id,
                    last_lopukhin_chapter=chapter,
                    last_lopukhin_chapter_end=None,  # Всегда одна глава
                    last_lopukhin_verse=verse,
                    last_lopukhin_verse_end=verse if verse != 0 else None,
                    last_topic_commentary_msg_id=msg.message_id
                )
        else:
            msg = await callback.message.answer(formatted, **opts)
            if state:
                await state.update_data(last_topic_commentary_msg_id=msg.message_id)
    else:
        await callback.message.answer("Толкование не найдено.")
    await callback.answer()


@router.callback_query(F.data.regexp(r'^open_commentary_([A-Za-z0-9]+)_(\d+)_0$'))
async def open_commentary_chapter_paginated(callback: CallbackQuery, state: FSMContext = None):
    match = re.match(
        r'^open_commentary_([A-Za-z0-9]+)_(\d+)_0$', callback.data)
    if not match:
        await callback.answer("Ошибка запроса")
        return
    book = match.group(1)
    chapter = int(match.group(2))
    from utils.lopukhin_commentary import lopukhin_commentary
    all_comments = lopukhin_commentary.get_all_commentaries_for_chapter(
        book, chapter)
    if not all_comments:
        await callback.message.answer("Толкования на главу не найдено.")
        await callback.answer()
        return
    # Не удаляем оригинальное сообщение, чтобы навигация осталась
    await show_commentary_page(callback, book, chapter, all_comments, 0, state)
    await callback.answer()


@router.callback_query(F.data.regexp(r'^commentary_page_([A-Za-z0-9]+)_(\d+)_(\d+)$'))
async def commentary_page_callback(callback: CallbackQuery, state: FSMContext = None):
    match = re.match(
        r'^commentary_page_([A-Za-z0-9]+)_(\d+)_(\d+)$', callback.data)
    if not match:
        await callback.answer("Ошибка запроса")
        return
    book = match.group(1)
    chapter = int(match.group(2))
    idx = int(match.group(3))
    from utils.lopukhin_commentary import lopukhin_commentary
    all_comments = lopukhin_commentary.get_all_commentaries_for_chapter(
        book, chapter)
    # Редактируем текущее сообщение с толкованием вместо удаления навигации
    await show_commentary_page(callback, book, chapter, all_comments, idx, state, edit_message=True)
    await callback.answer()


async def show_commentary_page(callback, book, chapter, all_comments, idx, state=None, edit_message=False):
    # Убираем дубли по номеру стиха (verse): только первое вхождение
    seen = set()
    filtered_comments = []
    for v, text in all_comments:
        if v not in seen:
            filtered_comments.append((v, text))
            seen.add(v)
    total = len(filtered_comments)
    v, text = filtered_comments[idx]
    if v == 0:
        title = f"Толкование на главу {chapter} (вступление):"
    else:
        title = f"{chapter}:{v}:"
    nav_kb = []
    if idx > 0:
        nav_kb.append(InlineKeyboardButton(text="⬅️ Назад",
                                           callback_data=f"commentary_page_{book}_{chapter}_{idx-1}"))
    if idx < total - 1:
        nav_kb.append(InlineKeyboardButton(text="Продолжить ➡️",
                                           callback_data=f"commentary_page_{book}_{chapter}_{idx+1}"))
    # Кнопки "Толкование проф. Лопухина" и "Разбор от ИИ" для всей главы
    extra_kb = []
    if idx == 0:
        # Кнопка толкования Лопухина (проверяем глобальную настройку)
        from config.settings import ENABLE_LOPUKHIN_COMMENTARY
        if ENABLE_LOPUKHIN_COMMENTARY:
            extra_kb.append(InlineKeyboardButton(
                text="Толкование проф. Лопухина",
                callback_data=f"open_commentary_{book}_{chapter}_0"
            ))
        from config.ai_settings import ENABLE_GPT_EXPLAIN
        if ENABLE_GPT_EXPLAIN:
            extra_kb.append(InlineKeyboardButton(
                text="🤖 Разбор от ИИ",
                callback_data=f"gpt_explain_{book}_{chapter}_0"
            ))
    # Добавляем кнопки сохранения для толкования Лопухина
    save_buttons = []
    if callback:  # Проверяем что callback есть
        # Получаем информацию о пользователе
        user_id = callback.from_user.id if hasattr(
            callback, "from_user") else callback.message.from_user.id

        # Получаем book_id для сохранения
        from utils.bible_data import bible_data
        ru_book = bible_data.book_synonyms.get(book.lower(), book)
        book_id = bible_data.get_book_id(ru_book)

        if book_id:
            # Проверяем, есть ли уже сохраненное толкование
            from database.universal_manager import universal_db_manager as db_manager
            verse_start = v if v != 0 else None

            try:
                saved_commentary = await db_manager.get_saved_commentary(
                    user_id, book_id, chapter, None, verse_start, verse_start, "lopukhin")

                # Формируем callback_data для кнопки сохранения
                chapter_start = chapter
                chapter_end_str = "0"  # Всегда одна глава
                verse_start_str = str(
                    verse_start) if verse_start is not None else "0"
                verse_end_str = str(
                    verse_start) if verse_start is not None else "0"

                # Создаем кнопку сохранения
                if saved_commentary:
                    save_buttons.append(InlineKeyboardButton(
                        text="🔄 Обновить толкование",
                        callback_data=f"save_commentary_{book_id}_{chapter_start}_{chapter_end_str}_{verse_start_str}_{verse_end_str}_lopukhin"))
                else:
                    save_buttons.append(InlineKeyboardButton(
                        text="💾 Сохранить толкование",
                        callback_data=f"save_commentary_{book_id}_{chapter_start}_{chapter_end_str}_{verse_start_str}_{verse_end_str}_lopukhin"))

                # Добавляем кнопку "Открыть всю главу" для стихов
                if v != 0:
                    # Получаем русское сокращение книги для callback
                    ru_book_abbr = None
                    for abbr, b_id in bible_data.book_abbr_dict.items():
                        if b_id == book_id:
                            ru_book_abbr = abbr
                            break

                    if ru_book_abbr:
                        open_chapter_button = InlineKeyboardButton(
                            text="Открыть всю главу",
                            callback_data=f"open_chapter_{ru_book_abbr}_{chapter}"
                        )
                        save_buttons.insert(0, open_chapter_button)
            except Exception as e:
                logger.error(f"Ошибка проверки сохраненного толкования: {e}")

    # Формируем клавиатуру
    keyboard_rows = []
    if nav_kb:
        keyboard_rows.append(nav_kb)
    if save_buttons:
        # Добавляем кнопки сохранения по одной в ряд
        for button in save_buttons:
            keyboard_rows.append([button])
    if extra_kb:
        keyboard_rows.append(extra_kb)

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)

    # Отправляем или редактируем толкование с учётом настроек форматирования
    formatted, opts = format_ai_or_commentary(text, title)

    if edit_message:
        # Редактируем существующее сообщение (для навигации по страницам)
        try:
            await callback.message.edit_text(formatted, reply_markup=markup, **opts)
            # Сохраняем данные в состояние для возможного сохранения толкования
            if state:
                from utils.bible_data import bible_data
                ru_book = bible_data.book_synonyms.get(book.lower(), book)
                book_id = bible_data.get_book_id(ru_book)

                await state.update_data(
                    last_lopukhin_commentary=text,
                    last_lopukhin_reference=f"{ru_book} {chapter}:{v}" if v != 0 else f"{ru_book} {chapter}",
                    last_lopukhin_book_id=book_id,
                    last_lopukhin_chapter=chapter,
                    last_lopukhin_chapter_end=None,
                    last_lopukhin_verse=v,
                    last_lopukhin_verse_end=v if v != 0 else None
                )
        except Exception as e:
            # Если редактирование не удалось, отправляем новое сообщение
            msg = await callback.message.answer(formatted, reply_markup=markup, **opts)
            if state:
                # Получаем book_id для состояния
                from utils.bible_data import bible_data
                ru_book = bible_data.book_synonyms.get(book.lower(), book)
                book_id = bible_data.get_book_id(ru_book)

                await state.update_data(
                    last_topic_commentary_msg_id=msg.message_id,
                    last_lopukhin_commentary=text,
                    last_lopukhin_reference=f"{ru_book} {chapter}:{v}" if v != 0 else f"{ru_book} {chapter}",
                    last_lopukhin_book_id=book_id,
                    last_lopukhin_chapter=chapter,
                    last_lopukhin_chapter_end=None,
                    last_lopukhin_verse=v,
                    last_lopukhin_verse_end=v if v != 0 else None
                )
    else:
        # Отправляем новое сообщение (первоначальный показ толкования)
        msg = await callback.message.answer(formatted, reply_markup=markup, **opts)
        # Сохраняем id сообщения с толкованием и данные для возможного сохранения
        if state:
            # Получаем book_id для состояния
            from utils.bible_data import bible_data
            ru_book = bible_data.book_synonyms.get(book.lower(), book)
            book_id = bible_data.get_book_id(ru_book)

            await state.update_data(
                last_topic_commentary_msg_id=msg.message_id,
                last_lopukhin_commentary=text,
                last_lopukhin_reference=f"{ru_book} {chapter}:{v}" if v != 0 else f"{ru_book} {chapter}",
                last_lopukhin_book_id=book_id,
                last_lopukhin_chapter=chapter,
                last_lopukhin_chapter_end=None,
                last_lopukhin_verse=v,
                last_lopukhin_verse_end=v if v != 0 else None
            )


@router.callback_query(F.data.regexp(r'^gpt_explain_([A-Za-z0-9]+)_(\d+)_(.+)$'))
async def gpt_explain_callback(callback: CallbackQuery, state: FSMContext = None):
    import re
    # Сразу отвечаем на callback чтобы избежать timeout
    await callback.answer("🤖 Генерирую AI-разбор...")

    # Изменяем кнопку на анимированную версию
    try:
        current_markup = callback.message.reply_markup
        if current_markup and current_markup.inline_keyboard:
            new_buttons = []
            for row in current_markup.inline_keyboard:
                new_row = []
                for button in row:
                    if button.callback_data and button.callback_data == callback.data:
                        # Заменяем кнопку "Разбор от ИИ" на анимированную
                        new_row.append(InlineKeyboardButton(
                            text="⏳ Генерирую разбор...",
                            callback_data=button.callback_data
                        ))
                    else:
                        new_row.append(button)
                new_buttons.append(new_row)

            from aiogram.types import InlineKeyboardMarkup
            new_markup = InlineKeyboardMarkup(inline_keyboard=new_buttons)
            await callback.message.edit_reply_markup(reply_markup=new_markup)
    except Exception as e:
        logger.error(f"Ошибка изменения кнопки AI: {e}")

    # --- AI LIMIT CHECK ---
    user_id = callback.from_user.id if hasattr(
        callback, "from_user") else callback.message.from_user.id
    from handlers.text_messages import ai_check_and_increment_db
    if not await ai_check_and_increment_db(user_id):
        await callback.message.answer("Вы исчерпали лимит ИИ-запросов на сегодня.")
        return
    match = re.match(
        r'^gpt_explain_([A-Za-z0-9]+)_(\d+)_(.+)$', callback.data)
    if not match:
        await callback.answer("Ошибка запроса к ИИ")
        return
    book = match.group(1)
    chapter = int(match.group(2))
    verse_part = match.group(3)
    
    # Парсим часть со стихом (может быть "0", "5", "5-10")
    if verse_part == "0":
        verse = 0
        verse_end = None
    elif "-" in verse_part:
        verse_parts = verse_part.split("-")
        if len(verse_parts) >= 2 and verse_parts[0].strip() and verse_parts[1].strip():
            verse = int(verse_parts[0].strip())
            verse_end = int(verse_parts[1].strip())
        else:
            # Если не удалось распарсить диапазон, используем как одиночный стих
            try:
                verse = int(verse_part.replace("-", ""))
                verse_end = None
            except ValueError:
                verse = 0
                verse_end = None
    else:
        verse = int(verse_part)
        verse_end = None
    # Получаем текст главы или стиха
    text = ""
    # Формируем ссылку для get_verse_by_reference с русским сокращением
    from utils.bible_data import bible_data
    ru_book = bible_data.book_synonyms.get(book.lower(), book)
    book_id = bible_data.get_book_id(ru_book)
    
    # Формируем ссылку в зависимости от типа запроса
    if verse == 0:
        reference = f"{ru_book} {chapter}"
    elif verse_end is not None:
        reference = f"{ru_book} {chapter}:{verse}-{verse_end}"
    else:
        reference = f"{ru_book} {chapter}:{verse}"

    # Обновляем состояние для корректной навигации
    if book_id and state:
        from middleware.state import set_chosen_book, set_current_chapter
        await set_chosen_book(state, book_id)
        await set_current_chapter(state, chapter)
    if verse == 0:
        # Исправление: передаём числовой ID книги, а не строку
        if not book_id:
            await callback.message.answer(f"Книга '{ru_book}' не найдена.")
            await callback.answer()
            return
        # Используем корректный код перевода для синодального (rst)
        text = await bible_api.get_formatted_chapter(book_id, chapter, "rst")
    else:
        from handlers.verse_reference import get_verse_by_reference
        st = state if state is not None else None
        
        # Отладочная информация для диагностики проблемы
        logger.info(f"DEBUG: Обработка ссылки '{reference}' для пользователя {user_id}")
        logger.info(f"DEBUG: book='{book}', ru_book='{ru_book}', book_id={book_id}")
        logger.info(f"DEBUG: chapter={chapter}, verse={verse}, verse_end={verse_end}")
        
        try:
            text, _ = await get_verse_by_reference(st, reference)
            logger.info(f"DEBUG: get_verse_by_reference успешно вернул текст длиной {len(text) if text else 0} символов")
        except Exception as e:
            logger.error(f"DEBUG: Ошибка в get_verse_by_reference: {e}")
            text, _ = await get_verse_by_reference(None, reference)
    # Проверка на ошибку формата
    if text.startswith("Неверный формат ссылки") or text.startswith("Книга '"):
        await callback.message.answer(text)
        await callback.answer()
        return
    # Формируем запрос к ИИ
    prompt = f"Объясни смысл следующего текста:\n\n{text}\n\nОтветь кратко и по существу."
    try:
        response = await ask_gpt_explain(prompt)
        formatted, opts = format_ai_or_commentary(
            response, title="🤖 Разбор от ИИ")

        # Проверяем, есть ли уже сохраненное толкование
        from database.universal_manager import universal_db_manager as db_manager
        verse_start_num = verse if verse != 0 else None
        verse_end_num = verse_end if verse_end is not None else verse_start_num
        saved_commentary = await db_manager.get_saved_commentary(
            user_id, book_id, chapter, None, verse_start_num, verse_end_num, "ai")

        # Разбиваем на части и отправляем
        text_parts = list(split_text(formatted))
        for idx, part in enumerate(text_parts):
            if idx == len(text_parts) - 1:  # Последняя часть - добавляем кнопки
                # Создаем кнопки без кнопки AI (exclude_ai=True)
                from utils.bible_data import create_chapter_action_buttons
                action_buttons = await create_chapter_action_buttons(
                    book_id, chapter, book, exclude_ai=True, user_id=callback.from_user.id)

                # Добавляем кнопку для сохранения толкования
                save_buttons = []

                # Формируем callback_data для новой схемы
                chapter_start = chapter
                chapter_end_str = "0"  # Всегда одна глава
                verse_start_str = str(
                    verse_start_num) if verse_start_num is not None else "0"
                # Для диапазона стихов используем verse_end_num
                verse_end_str = str(
                    verse_end_num) if verse_end_num is not None else "0"

                if saved_commentary:
                    save_buttons = [
                        [InlineKeyboardButton(
                            text="🔄 Обновить толкование",
                            callback_data=f"save_commentary_{book_id}_{chapter_start}_{chapter_end_str}_{verse_start_str}_{verse_end_str}_ai")]
                    ]
                else:
                    save_buttons = [
                        [InlineKeyboardButton(
                            text="💾 Сохранить толкование",
                            callback_data=f"save_commentary_{book_id}_{chapter_start}_{chapter_end_str}_{verse_start_str}_{verse_end_str}_ai")]
                    ]

                if verse == 0:  # Для главы - добавляем навигацию
                    # Навигация между главами
                    has_previous = chapter > 1
                    max_chapter = bible_data.max_chapters.get(book_id, 0)
                    has_next = chapter < max_chapter

                    # Проверяем закладки
                    from middleware.state import get_bookmarks
                    bookmarks = await get_bookmarks(state)
                    book_name = bible_data.get_book_name(book_id)
                    bookmark_key = f"{book_name} {chapter}"
                    is_bookmarked = bookmark_key in bookmarks

                    # Создаем полную клавиатуру навигации с кнопками сохранения
                    from keyboards.main import create_navigation_keyboard
                    keyboard = create_navigation_keyboard(
                        has_previous, has_next, is_bookmarked, action_buttons + save_buttons)

                    msg = await callback.message.answer(part, reply_markup=keyboard, **opts)
                else:  # Для стиха - только кнопки действий
                    # Получаем русское сокращение книги для callback
                    ru_book_abbr = None
                    for abbr, b_id in bible_data.book_abbr_dict.items():
                        if b_id == book_id:
                            ru_book_abbr = abbr
                            break

                    # Добавляем кнопку "Открыть всю главу" в начало action_buttons
                    if ru_book_abbr:
                        open_chapter_button = [
                            InlineKeyboardButton(
                                text="Открыть всю главу",
                                callback_data=f"open_chapter_{ru_book_abbr}_{chapter}"
                            )
                        ]
                        # Объединяем все кнопки: "Открыть всю главу" + action_buttons + save_buttons
                        all_buttons = [open_chapter_button] + \
                            action_buttons + save_buttons
                    else:
                        # Если не найдено сокращение, только action_buttons + save_buttons
                        all_buttons = action_buttons + save_buttons

                    # Добавляем кнопку возврата в зависимости от контекста
                    if state:
                        data = await state.get_data()
                        # Проверяем, есть ли данные от ИИ помощника
                        if data.get('verse_references') and data.get('problem_text'):
                            # Пользователь пришел от ИИ помощника
                            all_buttons.append([
                                InlineKeyboardButton(
                                    text="⬅️ Вернуться к отрывкам",
                                    callback_data="back_to_ai_verses"
                                )
                            ])
                        else:
                            # Пользователь пришел из готовых тем
                            all_buttons.append([
                                InlineKeyboardButton(
                                    text="⬅️ Назад к темам",
                                    callback_data="back_to_topics"
                                )
                            ])

                    if all_buttons:
                        keyboard = InlineKeyboardMarkup(
                            inline_keyboard=all_buttons)
                        msg = await callback.message.answer(part, reply_markup=keyboard, **opts)
                    else:
                        msg = await callback.message.answer(part, **opts)

                # Возвращаем кнопку "🤖 Разбор от ИИ" обратно после загрузки
                try:
                    current_markup = callback.message.reply_markup
                    if current_markup and current_markup.inline_keyboard:
                        new_buttons = []
                        for row in current_markup.inline_keyboard:
                            new_row = []
                            for button in row:
                                if button.callback_data and button.callback_data == callback.data and "⏳" in button.text:
                                    # Возвращаем кнопку обратно к "🤖 Разбор от ИИ"
                                    new_row.append(InlineKeyboardButton(
                                        text="🤖 Разбор от ИИ",
                                        callback_data=button.callback_data
                                    ))
                                else:
                                    new_row.append(button)
                            new_buttons.append(new_row)

                        from aiogram.types import InlineKeyboardMarkup
                        new_markup = InlineKeyboardMarkup(
                            inline_keyboard=new_buttons)
                        await callback.message.edit_reply_markup(reply_markup=new_markup)
                except Exception as e:
                    logger.error(f"Ошибка возврата кнопки AI: {e}")

                # Сохраняем данные толкования в состоянии для возможного сохранения
                if state:
                    await state.update_data(
                        last_ai_commentary=response,
                        last_ai_reference=reference,
                        last_ai_book_id=book_id,
                        last_ai_chapter=chapter,  # Для совместимости, в save_callback это будет chapter_start
                        last_ai_chapter_end=None,  # Всегда одна глава для тем
                        last_ai_verse=verse,
                        # Для диапазонов стихов используем verse_end_num
                        last_ai_verse_end=verse_end_num if verse_end_num is not None else (verse if verse != 0 else None),
                        last_topic_ai_msg_id=msg.message_id
                    )
            else:
                msg = await callback.message.answer(part, **opts)

            if state:
                await state.update_data(last_topic_ai_msg_id=msg.message_id)
    except Exception as e:
        logger.error(f"Ошибка при обращении к ИИ: {e}")
        await callback.message.answer("Произошла ошибка при обращении к ИИ. Попробуйте позже.")

        # Возвращаем кнопку "🤖 Разбор от ИИ" обратно даже при ошибке
        try:
            current_markup = callback.message.reply_markup
            if current_markup and current_markup.inline_keyboard:
                new_buttons = []
                for row in current_markup.inline_keyboard:
                    new_row = []
                    for button in row:
                        if button.callback_data and button.callback_data == callback.data and "⏳" in button.text:
                            # Возвращаем кнопку обратно к "🤖 Разбор от ИИ"
                            new_row.append(InlineKeyboardButton(
                                text="🤖 Разбор от ИИ",
                                callback_data=button.callback_data
                            ))
                        else:
                            new_row.append(button)
                    new_buttons.append(new_row)

                from aiogram.types import InlineKeyboardMarkup
                new_markup = InlineKeyboardMarkup(inline_keyboard=new_buttons)
                await callback.message.edit_reply_markup(reply_markup=new_markup)
        except Exception as button_error:
            logger.error(
                f"Ошибка возврата кнопки AI при ошибке: {button_error}")


@router.message(F.text.in_(get_topics_list()))
async def topic_selected(message: Message):
    from utils.topics import get_verses_for_topic
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    topic = message.text.strip()
    verses = get_verses_for_topic(topic)
    # Формируем inline-клавиатуру с кнопками по 2 в ряд
    buttons = []
    row = []
    for i, v in enumerate(verses):
        row.append(InlineKeyboardButton(text=v, callback_data=f"verse_{v}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(f'<b>{topic}</b>\n\nВыберите стих:', reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.regexp(r'^open_chapter_([а-яА-Я0-9]+)_(\d+)$'))
async def open_full_chapter_callback(callback: CallbackQuery, state: FSMContext):
    # Удаляем предыдущую главу и все связанные сообщения (толкование, ИИ-разборы)
    data = await state.get_data() if state else {}
    prev_chapter_msg_id = data.get('last_chapter_msg_id')
    prev_commentary_msg_id = data.get('last_topic_commentary_msg_id')
    prev_ai_msg_id = data.get('last_topic_ai_msg_id')
    for msg_id in [prev_chapter_msg_id, prev_commentary_msg_id, prev_ai_msg_id]:
        if msg_id:
            try:
                await callback.bot.delete_message(callback.message.chat.id, msg_id)
            except Exception:
                pass
    match = re.match(r'^open_chapter_([а-яА-Я0-9]+)_(\d+)$', callback.data)
    if not match:
        await callback.answer("Ошибка запроса")
        return
    book_abbr = match.group(1)
    chapter = int(match.group(2))
    # Всегда нормализуем сокращение
    book_abbr = bible_data.normalize_book_name(book_abbr)
    book_id = bible_data.get_book_id(book_abbr)
    if not book_id:
        await callback.answer("Книга не найдена")
        return
    translation = await get_current_translation(state)
    text = await bible_api.get_formatted_chapter(book_id, chapter, translation)
    sent = None
    from utils.text_utils import get_verses_parse_mode
    parse_mode = get_verses_parse_mode()

    for part in split_text(text):
        sent = await callback.message.answer(part, parse_mode=parse_mode)
    # Сохраняем id сообщения с главой и сбрасываем все связанные сообщения
    if state and sent:
        await state.update_data(
            last_chapter_msg_id=sent.message_id,
            last_topic_verse_msg_id=None,
            last_topic_commentary_msg_id=None,
            last_topic_ai_msg_id=None,
            last_topic_msg_id=None
        )
    # Клавиатура навигации по главам
    max_chapters = bible_data.max_chapters.get(book_id, 1)
    has_previous = chapter > 1
    has_next = chapter < max_chapters
    is_bookmarked = False
    # Кнопки для главы: Толкование Лопухина и разбор от ИИ (всегда, даже если нет толкования)
    en_book = None
    en_to_ru = {
        "Gen": "Быт", "Exod": "Исх", "Lev": "Лев", "Num": "Чис", "Deut": "Втор", "Josh": "Нав", "Judg": "Суд", "Ruth": "Руф",
        "1Sam": "1Цар", "2Sam": "2Цар", "1Kgs": "3Цар", "2Kgs": "4Цар", "1Chr": "1Пар", "2Chr": "2Пар", "Ezra": "Езд", "Neh": "Неем",
        "Esth": "Есф", "Job": "Иов", "Ps": "Пс", "Prov": "Прит", "Eccl": "Еккл", "Song": "Песн", "Isa": "Ис", "Jer": "Иер",
        "Lam": "Плач", "Ezek": "Иез", "Dan": "Дан", "Hos": "Ос", "Joel": "Иоил", "Amos": "Ам", "Obad": "Авд", "Jonah": "Ион",
        "Mic": "Мих", "Nah": "Наум", "Hab": "Авв", "Zeph": "Соф", "Hag": "Агг", "Zech": "Зах", "Mal": "Мал",
        "Matt": "Мф", "Mark": "Мк", "Luke": "Лк", "John": "Ин", "Acts": "Деян", "Jas": "Иак", "1Pet": "1Пет", "2Pet": "2Пет",
        "1John": "1Ин", "2John": "2Ин", "3John": "3Ин", "Jude": "Иуд", "Rom": "Рим", "1Cor": "1Кор", "2Cor": "2Кор",
        "Gal": "Гал", "Eph": "Еф", "Phil": "Флп", "Col": "Кол", "1Thess": "1Фес", "2Thess": "2Фес", "1Tim": "1Тим",
        "2Tim": "2Тим", "Titus": "Тит", "Phlm": "Флм", "Heb": "Евр", "Rev": "Откр"
    }
    for en, ru in en_to_ru.items():
        if ru == book_abbr:
            en_book = en
            break
    # Используем умную функцию создания кнопок
    from utils.bible_data import create_chapter_action_buttons
    extra_buttons = await create_chapter_action_buttons(
        book_id, chapter, en_book, user_id=callback.from_user.id
    )

    # Отправляем объединенную клавиатуру навигации с дополнительными кнопками
    await callback.message.answer(
        "Выберите действие:",
        reply_markup=create_navigation_keyboard(
            has_previous, has_next, is_bookmarked, extra_buttons)
    )
    await callback.answer()


@router.message(F.text == "/clean_on")
async def enable_cleaning(message: Message, state: FSMContext):
    """Включить удаление связанных сообщений для пользователя."""
    await state.update_data(enable_delete_related_messages=True)
    await message.answer("Удаление предыдущих сообщений теперь ВКЛЮЧЕНО для вас.")


@router.message(F.text == "/clean_off")
async def disable_cleaning(message: Message, state: FSMContext):
    """Отключить удаление связанных сообщений для пользователя."""
    await state.update_data(enable_delete_related_messages=False)
    await message.answer("Удаление предыдущих сообщений теперь ОТКЛЮЧЕНО для вас.")


async def get_user_cleaning_setting(state: FSMContext) -> bool:
    """Получить настройку удаления сообщений для пользователя."""
    if not state:
        return ENABLE_DELETE_RELATED_MESSAGES_DEFAULT
    data = await state.get_data()
    return data.get("enable_delete_related_messages", ENABLE_DELETE_RELATED_MESSAGES_DEFAULT)


async def delete_related_messages(callback, state: FSMContext):
    """
    Удаляет связанные сообщения: главу, толкование, ИИ-разбор (и для тем — список стихов), если они есть в state.
    Работает только если включено для пользователя.
    """
    if not await get_user_cleaning_setting(state):
        return
    if not state:
        return
    data = await state.get_data()
    msg_keys = [
        'last_chapter_msg_id',
        'last_topic_verse_msg_id',
        'last_topic_commentary_msg_id',
        'last_topic_ai_msg_id',
        'last_topic_msg_id',
    ]
    for key in msg_keys:
        msg_id = data.get(key)
        if msg_id:
            try:
                await callback.bot.delete_message(callback.message.chat.id, msg_id)
            except Exception:
                pass


def format_ai_or_commentary(text, title=None):
    """
    Форматирует текст для вывода в Telegram как цитата.
    title: если задан, будет выделен жирным
    """
    # Возвращаем к формату цитат как было раньше
    result = f"<blockquote>{text}</blockquote>"

    # Добавляем заголовок если есть
    if title:
        title = f"<b>{title}</b>"
        result = f"{title}\n\n{result}"

    return result, {"parse_mode": "HTML"}


@router.message(F.text == "📚 План чтения")
async def reading_plan_menu(message: Message, state: FSMContext):
    from services.universal_reading_plans import universal_reading_plans_service
    plans = universal_reading_plans_service.get_all_plans()
    if not plans:
        await message.answer("Планы чтения не найдены.")
        return
    # Получаем текущий выбранный план из state
    user_data = await state.get_data()
    current_plan_id = user_data.get('current_reading_plan')
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=(f"👉 {plan.title}" if plan.plan_id ==
                      current_plan_id else plan.title),
                callback_data=f"readingplan_{plan.plan_id}")]
            for plan in plans
        ]
    )
    await message.answer("Выберите план чтения:", reply_markup=kb)


@router.callback_query(F.data.regexp(r'^readingplan_(.+?)(?:_page_(\d+))?$'))
async def reading_plan_days(callback: CallbackQuery, state: FSMContext):
    from services.universal_reading_plans import universal_reading_plans_service

    # Более надежный способ парсинга callback_data
    callback_parts = callback.data.split('_')
    if len(callback_parts) >= 2:
        if callback_parts[-2] == 'page' and callback_parts[-1].isdigit():
            # Формат: readingplan_planX_page_Y
            page = int(callback_parts[-1])
            plan_id = '_'.join(callback_parts[1:-2])
        else:
            # Формат: readingplan_planX
            page = 0
            plan_id = '_'.join(callback_parts[1:])
    else:
        await callback.answer("Ошибка обработки данных")
        return

    # Получаем план из универсального сервиса
    plan = universal_reading_plans_service.get_plan(plan_id)
    if not plan:
        await callback.answer("План не найден")
        return
    await state.update_data(current_reading_plan=plan_id)
    user_id = callback.from_user.id
    from database.universal_manager import universal_db_manager as db_manager
    completed_days = set(await db_manager.get_reading_progress(user_id, plan_id))
    total = len(plan.days)
    done = len(completed_days)
    header = f"<b>План:</b> {plan.title}\n<b>Прогресс:</b> {done} из {total} дней"

    # Упрощенная логика пагинации
    per_page = 5

    # Если план содержит мало дней, показываем все на одной странице
    if total <= per_page:
        start = 0
        end = total
    else:
        if page == 0 and completed_days:
            # На первой странице показываем умную навигацию:
            # последний прочитанный день + следующие непрочитанные
            last_completed = max(completed_days) if completed_days else 0

            # Находим индекс последнего прочитанного дня
            last_completed_idx = -1
            for i, (day_num, _) in enumerate(plan.days):
                if day_num == last_completed:
                    last_completed_idx = i
                    break

            if last_completed_idx >= 0:
                # Показываем последний прочитанный + 4 следующих
                start = last_completed_idx
                end = min(start + per_page, len(plan.days))
            else:
                # Если не найден, показываем с начала
                start = 0
                end = min(per_page, len(plan.days))
        else:
            # Обычная пагинация для других страниц
            start = page * per_page
            end = min(start + per_page, len(plan.days))

    days_slice = plan.days[start:end]
    buttons = []
    for day_num, reading_text in days_slice:
        # Определяем иконку в зависимости от прогресса частей дня
        parts = [p.strip() for p in reading_text.split(';') if p.strip()]
        total_parts = len(parts)
        completed_parts = set(
            await db_manager.get_reading_part_progress(user_id, plan_id, day_num))
        completed_parts_count = len(completed_parts)

        # Улучшенная система значков с прогрессом
        if completed_parts_count == total_parts and total_parts > 0:
            mark = "✅"  # Все части прочитаны
            progress_text = ""
        elif completed_parts_count > 0:
            mark = "📖"  # Частично прочитано
            progress_text = f" ({completed_parts_count}/{total_parts})"
        else:
            mark = "⭕"  # Ничего не прочитано
            progress_text = f" (0/{total_parts})" if total_parts > 1 else ""

        short = reading_text
        short = re.sub(r'Евангелие от ', '', short)
        short = re.sub(r'Послание к ', '', short)
        short = re.sub(r'Книга ', '', short)
        short = re.sub(r'Притчи Соломоновы', 'Притчи', short)
        short = re.sub(r'Псалтырь', 'Пс', short)
        short = re.sub(r'Деяния апостолов', 'Деян', short)
        short = re.sub(r'Матфея', 'Мф', short)
        short = re.sub(r'Марка', 'Мк', short)
        short = re.sub(r'Луки', 'Лк', short)
        short = re.sub(r'Иоанна', 'Ин', short)

        # Укорачиваем текст если он слишком длинный
        if len(short) > 45:
            short = short[:42] + "..."

        btn_text = f"{mark} День {day_num}{progress_text} - {short}"
        buttons.append([
            InlineKeyboardButton(
                text=btn_text,
                callback_data=f"readingday_{plan_id}_{day_num}"
            )
        ])
    # Навигационные кнопки
    nav_buttons = []
    if start > 0:
        nav_buttons.append(InlineKeyboardButton(
            text="⬅️ Назад", callback_data=f"readingplan_{plan_id}_page_{page-1}"))
    if end < total:
        nav_buttons.append(InlineKeyboardButton(
            text="Далее ➡️", callback_data=f"readingplan_{plan_id}_page_{page+1}"))
    if nav_buttons:
        buttons.append(nav_buttons)

    # Кнопка возврата к списку планов
    buttons.append([InlineKeyboardButton(
        text="⬅️ К списку планов",
        callback_data="back_to_reading_plans"
    )])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(header, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.regexp(r'^readingday_(.+)_(\d+)$'))
async def reading_plan_day(callback: CallbackQuery, state: FSMContext):
    from services.universal_reading_plans import universal_reading_plans_service
    m = re.match(r'^readingday_(.+)_(\d+)$', callback.data)
    plan_id, day = m.group(1), int(m.group(2))

    plan = universal_reading_plans_service.get_plan(plan_id)
    if not plan:
        await callback.answer("План не найден")
        return

    # Находим чтение для этого дня
    reading_text = None
    for day_num, reading in plan.days:
        if day_num == day:
            reading_text = reading
            break

    if not reading_text:
        await callback.answer("День не найден")
        return

    user_id = callback.from_user.id
    from database.universal_manager import universal_db_manager as db_manager
    completed = await db_manager.is_reading_day_completed(user_id, plan_id, day)

    # Разбиваем чтение на части по символу ";"
    parts = [p.strip() for p in reading_text.split(';') if p.strip()]

    # Проверяем прогресс отдельных частей
    completed_parts = set(
        await db_manager.get_reading_part_progress(user_id, plan_id, day))

    # Подсчитываем общий прогресс дня
    total_parts = len(parts)
    completed_count = len(completed_parts)

    # Добавляем логирование для отладки
    logger = logging.getLogger(__name__)
    logger.info(
        f"[PROGRESS] Отображение дня: user_id={user_id}, plan_id={plan_id}, day={day}")
    logger.info(
        f"[PROGRESS] Всего частей: {total_parts}, завершено: {completed_count}")
    logger.info(
        f"[PROGRESS] Список завершенных частей: {list(completed_parts)}")

    # Определяем статус дня
    if completed_count == total_parts and total_parts > 0:
        day_status = "✅ Все части прочитаны"
        day_icon = "✅"
    elif completed_count > 0:
        day_status = f"📖 Прочитано: {completed_count} из {total_parts}"
        day_icon = "📖"
    else:
        day_status = f"⭕ Не прочитано: 0 из {total_parts}"
        day_icon = "⭕"

    # Формируем кнопки для каждой части
    entry_buttons = []
    for i, part in enumerate(parts):
        # Улучшенные значки для частей
        if i in completed_parts:
            part_icon = "✅"
            part_text = f"{part_icon} {part}"
        else:
            part_icon = "📄"
            part_text = f"{part_icon} {part}"

        entry_buttons.append([
            InlineKeyboardButton(
                text=part_text,
                callback_data=f"readingtext_{plan_id}_{day}_{i}"
            )
        ])

    # Добавляем кнопки управления
    control_buttons = [
        [InlineKeyboardButton(
            text="⬅️ Назад к списку дней",
            callback_data=f"readingplan_{plan_id}"
        )]
    ]

    kb = InlineKeyboardMarkup(
        inline_keyboard=entry_buttons + control_buttons
    )

    # Формируем улучшенный текст с прогрессом
    message_text = (
        f"<b>📋 План:</b> {plan.title}\n"
        f"<b>{day_icon} День {day}:</b> {day_status}\n\n"
        f"<b>📖 Чтение на день:</b>\n"
        f"<i>{reading_text}</i>"
    )

    await callback.message.edit_text(
        message_text,
        reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.regexp(r'^readingtext_'))
async def reading_plan_text(callback: CallbackQuery, state: FSMContext):
    import logging
    # Импортируем все необходимые функции в начале, чтобы избежать UnboundLocalError
    from utils.text_utils import split_text
    from handlers.verse_reference import get_verse_by_reference
    from services.universal_reading_plans import universal_reading_plans_service

    parts = callback.data.split('_')
    if len(parts) == 4:  # readingtext_{plan_id}_{day}_{part_idx}
        _, *plan_id_parts, day, part_idx = parts
        plan_id = '_'.join(plan_id_parts)
        day = int(day)
        part_idx = int(part_idx)

        logging.warning(
            f"[reading_plan_text] callback_data={callback.data} plan_id={plan_id} day={day} part_idx={part_idx}")

        plan = universal_reading_plans_service.get_plan(plan_id)
        if not plan:
            await callback.answer("План не найден")
            return

        # Находим чтение для этого дня
        reading_text = None
        for day_num, reading in plan.days:
            if day_num == day:
                reading_text = reading
                break

        if not reading_text:
            await callback.answer("День не найден")
            return

        # Разбиваем чтение на части по символу ";"
        reading_parts = [p.strip()
                         for p in reading_text.split(';') if p.strip()]

        if part_idx >= len(reading_parts):
            await callback.answer("Отрывок не найден")
            return

        # Получаем нужную часть чтения
        reading_part = reading_parts[part_idx]
        logging.warning(f"[reading_plan_text] reading_part={reading_part}")

        # Получаем текст главы/стиха
        text, meta = await get_verse_by_reference(state, reading_part)
        user_id = callback.from_user.id

        # Проверяем, прочитана ли эта часть
        from database.universal_manager import universal_db_manager as db_manager
        part_completed = await db_manager.is_reading_part_completed(
            user_id, plan_id, day, part_idx)

        # Формируем кнопки под текстом главы
        action_buttons = [
            [InlineKeyboardButton(
                text="✅ Прочитано" if not part_completed else "Уже отмечено",
                callback_data=f"readingpartdone_{plan_id}_{day}_{part_idx}" if not part_completed else "noop"
            )],
            [InlineKeyboardButton(
                text="🤖 Разбор от ИИ",
                callback_data=f"readingai_{plan_id}_{day}_{part_idx}"
            )],
            [InlineKeyboardButton(
                text="⬅️ Назад к дню",
                callback_data=f"readingday_{plan_id}_{day}"
            )]
        ]

        kb = InlineKeyboardMarkup(inline_keyboard=action_buttons)

        # Получаем правильный режим парсинга для библейского текста
        from utils.text_utils import get_verses_parse_mode
        parse_mode = get_verses_parse_mode()

        # Разбиваем длинный текст
        text_parts = list(split_text(text))
        for idx, text_part in enumerate(text_parts):
            if idx == len(text_parts) - 1:  # Последняя часть - добавляем кнопки
                await callback.message.answer(text_part, parse_mode=parse_mode, reply_markup=kb)
            else:
                await callback.message.answer(text_part, parse_mode=parse_mode)
        await callback.answer()


@router.callback_query(F.data == "back_to_reading_plans")
async def back_to_reading_plans(callback: CallbackQuery, state: FSMContext):
    """Возврат к списку планов чтения"""
    from services.universal_reading_plans import universal_reading_plans_service
    plans = universal_reading_plans_service.get_all_plans()
    if not plans:
        await callback.message.edit_text("Планы чтения не найдены.")
        return

    # Получаем текущий выбранный план из state
    user_data = await state.get_data()
    current_plan_id = user_data.get('current_reading_plan')
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=(f"👉 {plan.title}" if plan.plan_id ==
                      current_plan_id else plan.title),
                callback_data=f"readingplan_{plan.plan_id}")]
            for plan in plans
        ]
    )
    await callback.message.edit_text("Выберите план чтения:", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.regexp(r'^readingdone_(.+)_(\d+)$'))
async def mark_reading_done(callback: CallbackQuery):
    """Отметить день как прочитанный"""
    import re
    from database.universal_manager import universal_db_manager as db_manager

    m = re.match(r'^readingdone_(.+)_(\d+)$', callback.data)
    if not m:
        await callback.answer("Ошибка обработки")
        return

    plan_id = m.group(1)
    day = int(m.group(2))
    user_id = callback.from_user.id

    # Отмечаем день как прочитанный в базе данных
    await db_manager.mark_reading_day_completed(user_id, plan_id, day)

    # Обновляем кнопку
    await callback.answer("✅ День отмечен как прочитанный!")

    # Перезагружаем страницу с днем для обновления кнопки
    from services.universal_reading_plans import universal_reading_plans_service
    plan = universal_reading_plans_service.get_plan(plan_id)
    if not plan:
        return

    # Находим чтение для этого дня
    reading_text = None
    for day_num, reading in plan.days:
        if day_num == day:
            reading_text = reading
            break

    if not reading_text:
        return

    # Проверяем новый статус
    completed = await db_manager.is_reading_day_completed(user_id, plan_id, day)

    # Разбиваем чтение на части по символу ";"
    parts = [p.strip() for p in reading_text.split(';') if p.strip()]

    # Формируем кнопки для каждой части
    entry_buttons = []
    for i, part in enumerate(parts):
        entry_buttons.append([
            InlineKeyboardButton(
                text=part,
                callback_data=f"readingtext_{plan_id}_{day}_{i}"
            )
        ])

    # Добавляем кнопки управления
    control_buttons = [
        [InlineKeyboardButton(
            text="✅ Прочитано" if not completed else "Уже отмечено",
            callback_data=f"readingdone_{plan_id}_{day}" if not completed else "noop"
        )],
        [InlineKeyboardButton(
            text="⬅️ Назад к списку дней",
            callback_data=f"readingplan_{plan_id}"
        )]
    ]

    kb = InlineKeyboardMarkup(
        inline_keyboard=entry_buttons + control_buttons
    )
    await callback.message.edit_reply_markup(reply_markup=kb)


@router.callback_query(F.data.regexp(r'^readingpartdone_(.+)_(\d+)_(\d+)$'))
async def mark_reading_part_done(callback: CallbackQuery):
    """Отметить часть дня как прочитанную"""
    import re
    import logging
    from database.universal_manager import universal_db_manager as db_manager

    logger = logging.getLogger(__name__)

    m = re.match(r'^readingpartdone_(.+)_(\d+)_(\d+)$', callback.data)
    if not m:
        await callback.answer("Ошибка обработки")
        return

    plan_id = m.group(1)
    day = int(m.group(2))
    part_idx = int(m.group(3))
    user_id = callback.from_user.id

    logger.info(
        f"[PROGRESS] Отмечаем часть как прочитанную: user_id={user_id}, plan_id={plan_id}, day={day}, part_idx={part_idx}")

    # Отмечаем часть как прочитанную в базе данных
    result = await db_manager.mark_reading_part_completed(user_id, plan_id, day, part_idx)
    logger.info(f"[PROGRESS] Результат сохранения: {result}")

    # Проверяем, действительно ли часть отмечена
    part_completed = await db_manager.is_reading_part_completed(user_id, plan_id, day, part_idx)
    logger.info(f"[PROGRESS] Статус после сохранения: {part_completed}")

    if part_completed:
        await callback.answer("✅ Часть отмечена как прочитанная!")
    else:
        await callback.answer("❌ Ошибка при сохранении прогресса!")
        logger.error(
            f"[PROGRESS] Не удалось сохранить прогресс для user_id={user_id}, plan_id={plan_id}, day={day}, part_idx={part_idx}")

    # Обновляем кнопки с реальным статусом
    action_buttons = [
        [InlineKeyboardButton(
            text="✅ Прочитано" if not part_completed else "Уже отмечено",
            callback_data=f"readingpartdone_{plan_id}_{day}_{part_idx}" if not part_completed else "noop"
        )],
        [InlineKeyboardButton(
            text="🤖 Разбор от ИИ",
            callback_data=f"readingai_{plan_id}_{day}_{part_idx}"
        )],
        [InlineKeyboardButton(
            text="⬅️ Назад к дню",
            callback_data=f"readingday_{plan_id}_{day}"
        )]
    ]

    kb = InlineKeyboardMarkup(inline_keyboard=action_buttons)
    await callback.message.edit_reply_markup(reply_markup=kb)


@router.callback_query(F.data.regexp(r'^readingai_(.+)_(\d+)_(\d+)$'))
async def reading_ai_callback(callback: CallbackQuery, state: FSMContext):
    """Показать ИИ-разбор для части плана чтения"""
    import re
    from services.universal_reading_plans import universal_reading_plans_service

    # Сразу отвечаем на callback чтобы избежать timeout
    await callback.answer("🤖 Генерирую AI-разбор...")

    # Изменяем кнопку на анимированную версию
    try:
        current_markup = callback.message.reply_markup
        if current_markup and current_markup.inline_keyboard:
            new_buttons = []
            for row in current_markup.inline_keyboard:
                new_row = []
                for button in row:
                    if button.callback_data and button.callback_data == callback.data:
                        # Заменяем кнопку "Разбор от ИИ" на анимированную
                        new_row.append(InlineKeyboardButton(
                            text="⏳ Генерирую разбор...",
                            callback_data=button.callback_data
                        ))
                    else:
                        new_row.append(button)
                new_buttons.append(new_row)

            from aiogram.types import InlineKeyboardMarkup
            new_markup = InlineKeyboardMarkup(inline_keyboard=new_buttons)
            await callback.message.edit_reply_markup(reply_markup=new_markup)
    except Exception as e:
        logger.error(f"Ошибка изменения кнопки AI в планах: {e}")

    # --- AI LIMIT CHECK ---
    user_id = callback.from_user.id
    if not await ai_check_and_increment_db(user_id):
        await callback.message.answer("Вы исчерпали лимит ИИ-запросов на сегодня.")
        return

    m = re.match(r'^readingai_(.+)_(\d+)_(\d+)$', callback.data)
    if not m:
        await callback.answer("Ошибка обработки")
        return

    plan_id = m.group(1)
    day = int(m.group(2))
    part_idx = int(m.group(3))

    # Получаем информацию о части чтения
    plan = universal_reading_plans_service.get_plan(plan_id)
    if not plan:
        await callback.answer("План не найден")
        return

    # Находим чтение для этого дня
    reading_text = None
    for day_num, reading in plan.days:
        if day_num == day:
            reading_text = reading
            break

    if not reading_text:
        await callback.answer("День не найден")
        return

    # Получаем нужную часть чтения
    reading_parts = [p.strip() for p in reading_text.split(';') if p.strip()]
    if part_idx >= len(reading_parts):
        await callback.answer("Отрывок не найден")
        return

    reading_part = reading_parts[part_idx]

    # Формируем запрос к ИИ напрямую с названием части
    prompt = f"Объясни смысл и основные темы следующего библейского отрывка: {reading_part}\n\nОтветь кратко и по существу, расскажи о ключевых моментах и духовном значении."

    try:
        response = await ask_gpt_explain(prompt)
        formatted, opts = format_ai_or_commentary(
            response, title="🤖 Разбор от ИИ")

        # Парсим reading_part для извлечения информации о книге и главах для сохранения
        from utils.bible_data import bible_data
        book_id = None
        chapter_start = None
        chapter_end = None
        verse_start = None
        verse_end = None

        # Пытаемся распарсить ссылку типа "Быт 1:1-2:25"
        try:
            import re
            logger.info(f"Парсим ссылку: '{reading_part}'")

            # Паттерн для ссылок типа "Быт 1:1-2:25", "Быт 1-2", "Быт 1:1-31", "Быт 1"
            patterns = [
                # "Быт 1:1-2:25" - диапазон через главы (5 групп)
                (r'^([А-Яа-яё\s\d]+)\s+(\d+):(\d+)-(\d+):(\d+)$', 'cross_chapter'),
                # "Быт 1:1-31" - диапазон стихов в одной главе (4 группы)
                (r'^([А-Яа-яё\s\d]+)\s+(\d+):(\d+)-(\d+)$', 'verse_range'),
                # "Быт 1-2" - диапазон глав (3 группы)
                (r'^([А-Яа-яё\s\d]+)\s+(\d+)-(\d+)$', 'chapter_range'),
                # "Быт 1:1" - один стих (3 группы)
                (r'^([А-Яа-яё\s\d]+)\s+(\d+):(\d+)$', 'single_verse'),
                # "Быт 1" - вся глава (2 группы)
                (r'^([А-Яа-яё\s\d]+)\s+(\d+)$', 'single_chapter')
            ]

            for pattern, pattern_type in patterns:
                match = re.match(pattern, reading_part.strip())
                if match:
                    book_name = match.group(1).strip()
                    logger.info(
                        f"Найдена книга: '{book_name}', тип: {pattern_type}")

                    if pattern_type == 'cross_chapter':  # "Быт 1:1-2:25"
                        chapter_start = int(match.group(2))
                        verse_start = int(match.group(3))
                        chapter_end = int(match.group(4))
                        verse_end = int(match.group(5))
                        logger.info(
                            f"Диапазон через главы: {chapter_start}:{verse_start}-{chapter_end}:{verse_end}")

                    elif pattern_type == 'verse_range':  # "Быт 1:1-31"
                        chapter_start = int(match.group(2))
                        chapter_end = None  # Одна глава
                        verse_start = int(match.group(3))
                        verse_end = int(match.group(4))
                        logger.info(
                            f"Диапазон стихов: {chapter_start}:{verse_start}-{verse_end}")

                    elif pattern_type == 'chapter_range':  # "Быт 1-2"
                        chapter_start = int(match.group(2))
                        chapter_end = int(match.group(3))
                        verse_start = None
                        verse_end = None
                        logger.info(
                            f"Диапазон глав: {chapter_start}-{chapter_end}")

                    elif pattern_type == 'single_verse':  # "Быт 1:1"
                        chapter_start = int(match.group(2))
                        chapter_end = None  # Одна глава
                        verse_start = int(match.group(3))
                        verse_end = verse_start
                        logger.info(
                            f"Один стих: {chapter_start}:{verse_start}")

                    elif pattern_type == 'single_chapter':  # "Быт 1"
                        chapter_start = int(match.group(2))
                        chapter_end = None  # Одна глава
                        verse_start = None
                        verse_end = None
                        logger.info(f"Одна глава: {chapter_start}")

                    # Получаем book_id
                    book_id = bible_data.get_book_id(book_name)
                    logger.info(
                        f"book_id: {book_id}, chapter_start: {chapter_start}, chapter_end: {chapter_end}, verse_start: {verse_start}, verse_end: {verse_end}")
                    break

        except Exception as parse_error:
            logger.error(
                f"Ошибка парсинга ссылки {reading_part}: {parse_error}")

        # Проверяем, есть ли уже сохраненное толкование (если удалось распарсить)
        saved_commentary = None
        if book_id and chapter_start is not None:
            from database.universal_manager import universal_db_manager as db_manager
            saved_commentary = await db_manager.get_saved_commentary(
                user_id, book_id, chapter_start, chapter_end, verse_start, verse_end, "ai")

        from utils.text_utils import split_text
        text_parts = list(split_text(formatted))

        # Отправляем все части текста
        for idx, part in enumerate(text_parts):
            if idx == len(text_parts) - 1:  # Последняя часть - добавляем кнопки
                # Проверяем, прочитана ли эта часть
                from database.universal_manager import universal_db_manager as db_manager
                user_id = callback.from_user.id
                part_completed = await db_manager.is_reading_part_completed(
                    user_id, plan_id, day, part_idx)

                # Кнопки под ИИ-разбором
                ai_buttons = [
                    [InlineKeyboardButton(
                        text="✅ Прочитано" if not part_completed else "Уже отмечено",
                        callback_data=f"readingpartdone_{plan_id}_{day}_{part_idx}" if not part_completed else "noop"
                    )],
                    [InlineKeyboardButton(
                        text="⬅️ Назад к дню",
                        callback_data=f"readingday_{plan_id}_{day}"
                    )]
                ]

                # Добавляем кнопку сохранения толкования, если удалось распарсить ссылку
                if book_id and chapter_start is not None:
                    # Формируем callback_data с правильной обработкой None
                    chapter_end_str = chapter_end if chapter_end is not None else "0"
                    verse_start_str = verse_start if verse_start is not None else "0"
                    verse_end_str = verse_end if verse_end is not None else "0"

                    if saved_commentary:
                        ai_buttons.insert(-1, [InlineKeyboardButton(
                            text="🔄 Обновить толкование",
                            callback_data=f"save_commentary_{book_id}_{chapter_start}_{chapter_end_str}_{verse_start_str}_{verse_end_str}_ai"
                        )])
                    else:
                        ai_buttons.insert(-1, [InlineKeyboardButton(
                            text="💾 Сохранить толкование",
                            callback_data=f"save_commentary_{book_id}_{chapter_start}_{chapter_end_str}_{verse_start_str}_{verse_end_str}_ai"
                        )])

                kb = InlineKeyboardMarkup(inline_keyboard=ai_buttons)
                msg = await callback.message.answer(part, reply_markup=kb, **opts)

                # Возвращаем кнопку "🤖 Разбор от ИИ" обратно после загрузки
                try:
                    current_markup = callback.message.reply_markup
                    if current_markup and current_markup.inline_keyboard:
                        new_buttons = []
                        for row in current_markup.inline_keyboard:
                            new_row = []
                            for button in row:
                                if button.callback_data and button.callback_data == callback.data and "⏳" in button.text:
                                    # Возвращаем кнопку обратно к "🤖 Разбор от ИИ"
                                    new_row.append(InlineKeyboardButton(
                                        text="🤖 Разбор от ИИ",
                                        callback_data=button.callback_data
                                    ))
                                else:
                                    new_row.append(button)
                            new_buttons.append(new_row)

                        from aiogram.types import InlineKeyboardMarkup
                        new_markup = InlineKeyboardMarkup(
                            inline_keyboard=new_buttons)
                        await callback.message.edit_reply_markup(reply_markup=new_markup)
                except Exception as e:
                    logger.error(f"Ошибка возврата кнопки AI в планах: {e}")

                # Сохраняем данные толкования в состоянии для возможного сохранения
                if state and book_id and chapter_start is not None:
                    await state.update_data(
                        last_ai_commentary=response,
                        last_ai_reference=reading_part,
                        last_ai_book_id=book_id,
                        last_ai_chapter=chapter_start,
                        last_ai_chapter_end=chapter_end,  # Добавляем chapter_end
                        last_ai_verse=verse_start or 0,
                        last_ai_verse_end=verse_end or 0,  # Добавляем verse_end
                        last_topic_ai_msg_id=msg.message_id
                    )
            else:
                msg = await callback.message.answer(part, **opts)

            if state:
                await state.update_data(last_topic_ai_msg_id=msg.message_id)
    except Exception as e:
        logger.error(f"Ошибка при обращении к ИИ: {e}")
        await callback.message.answer("Произошла ошибка при обращении к ИИ. Попробуйте позже.")

        # Возвращаем кнопку "🤖 Разбор от ИИ" обратно даже при ошибке
        try:
            current_markup = callback.message.reply_markup
            if current_markup and current_markup.inline_keyboard:
                new_buttons = []
                for row in current_markup.inline_keyboard:
                    new_row = []
                    for button in row:
                        if button.callback_data and button.callback_data == callback.data and "⏳" in button.text:
                            # Возвращаем кнопку обратно к "🤖 Разбор от ИИ"
                            new_row.append(InlineKeyboardButton(
                                text="🤖 Разбор от ИИ",
                                callback_data=button.callback_data
                            ))
                        else:
                            new_row.append(button)
                    new_buttons.append(new_row)

                from aiogram.types import InlineKeyboardMarkup
                new_markup = InlineKeyboardMarkup(inline_keyboard=new_buttons)
                await callback.message.edit_reply_markup(reply_markup=new_markup)
        except Exception as button_error:
            logger.error(
                f"Ошибка возврата кнопки AI при ошибке в планах: {button_error}")


# Обработчики для сохранения/удаления толкований
@router.callback_query(F.data.regexp(r'^save_commentary_(\d+)_(\d+)_(\d+)_(\d+)_(\d+)_(ai|lopukhin)$'))
async def save_commentary_callback(callback: CallbackQuery, state: FSMContext):
    """Сохраняет толкование пользователя"""
    import re
    from database.universal_manager import universal_db_manager as db_manager
    from utils.bible_data import bible_data
    from utils.text_formatter import format_reference_display

    match = re.match(
        r'^save_commentary_(\d+)_(\d+)_(\d+)_(\d+)_(\d+)_(ai|lopukhin)$', callback.data)
    if not match:
        await callback.answer("Ошибка сохранения")
        return

    book_id = int(match.group(1))
    chapter_start = int(match.group(2))
    chapter_end_raw = int(match.group(3))
    verse_start_raw = int(match.group(4))
    verse_end_raw = int(match.group(5))
    commentary_type = match.group(6)
    user_id = callback.from_user.id

    # Преобразуем "0" обратно в None для chapter_end и verse_start/verse_end
    chapter_end = chapter_end_raw if chapter_end_raw != 0 else None
    verse_start = verse_start_raw if verse_start_raw != 0 else None
    verse_end = verse_end_raw if verse_end_raw != 0 else None

    # Получаем данные толкования из состояния
    if not state:
        await callback.answer("Данные толкования не найдены")
        return

    data = await state.get_data()
    commentary_text = data.get('last_ai_commentary', '') if commentary_type == 'ai' else data.get(
        'last_lopukhin_commentary', '')

    if not commentary_text:
        await callback.answer("Текст толкования не найден")
        return

    # Формируем ссылку для отображения
    book_name = bible_data.get_book_name(book_id)

    # Формируем reference_text в зависимости от типа ссылки
    if chapter_end is not None and chapter_end != chapter_start:
        # Диапазон глав: "Быт 1-2" или "Быт 1:1-2:25"
        if verse_start is not None:
            reference_text = f"{book_name} {chapter_start}:{verse_start}-{chapter_end}:{verse_end or verse_start}"
        else:
            reference_text = f"{book_name} {chapter_start}-{chapter_end}"
    else:
        # Одна глава: "Быт 1" или "Быт 1:1" или "Быт 1:1-31"
        if verse_start is not None:
            if verse_end is not None and verse_end != verse_start:
                reference_text = f"{book_name} {chapter_start}:{verse_start}-{verse_end}"
            else:
                reference_text = f"{book_name} {chapter_start}:{verse_start}"
        else:
            reference_text = f"{book_name} {chapter_start}"

    # Сохраняем толкование
    success = await db_manager.save_commentary(
        user_id, book_id, chapter_start, chapter_end, verse_start, verse_end,
        reference_text, commentary_text, commentary_type
    )

    if success:
        await callback.answer("✅ Толкование сохранено!")

        # Обновляем кнопку с "Сохранить" на "Обновить"
        try:
            current_markup = callback.message.reply_markup
            if current_markup and current_markup.inline_keyboard:
                new_buttons = []

                for row in current_markup.inline_keyboard:
                    new_row = []
                    for button in row:
                        if button.callback_data and button.callback_data.startswith('save_commentary_'):
                            # Заменяем кнопку "Сохранить" на "Обновить"
                            new_row.append(InlineKeyboardButton(
                                text="🔄 Обновить толкование",
                                callback_data=button.callback_data
                            ))
                        else:
                            new_row.append(button)
                    new_buttons.append(new_row)

                from aiogram.types import InlineKeyboardMarkup
                new_markup = InlineKeyboardMarkup(inline_keyboard=new_buttons)
                await callback.message.edit_reply_markup(reply_markup=new_markup)
        except Exception as e:
            logger.error(f"Ошибка обновления кнопки: {e}")
    else:
        await callback.answer("❌ Ошибка сохранения")


@router.callback_query(F.data == "show_saved_commentaries")
async def show_saved_commentaries(callback: CallbackQuery, state: FSMContext):
    """Показывает список сохраненных толкований пользователя"""
    from database.universal_manager import universal_db_manager as db_manager
    from utils.text_formatter import create_commentary_summary

    user_id = callback.from_user.id
    commentaries = await db_manager.get_user_commentaries(user_id, 20)

    if not commentaries:
        await callback.message.answer("У вас нет сохраненных толкований.")
        await callback.answer()
        return

    text = "📚 <b>Ваши сохраненные толкования:</b>\n\n"
    buttons = []

    # Показываем только первые 10
    for i, commentary in enumerate(commentaries[:10], 1):
        reference = commentary.get('reference_text', '')
        commentary_text = commentary.get('commentary_text', '')
        commentary_type = commentary.get('commentary_type', 'ai')

        # Создаем краткое резюме
        summary = create_commentary_summary(commentary_text, 100)

        # Иконка в зависимости от типа
        icon = "🤖" if commentary_type == 'ai' else "📖"

        text += f"{i}. {icon} <b>{reference}</b>\n<i>{summary}</i>\n\n"

        # Добавляем кнопку для просмотра
        buttons.append([InlineKeyboardButton(
            text=f"{i}. {reference}",
            callback_data=f"view_saved_{commentary['id']}"
        )])

    if len(commentaries) > 10:
        text += f"<i>...и еще {len(commentaries) - 10} толкований</i>"

    # Добавляем кнопку закрытия
    buttons.append([InlineKeyboardButton(
        text="❌ Закрыть",
        callback_data="close_message"
    )])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "noop")
async def noop_handler(callback: CallbackQuery):
    """Обработчик для неактивных кнопок"""
    await callback.answer()


# --- Обработчики для тестирования и отладки ---
@router.message(F.text == "/debug")
async def debug_command(message: Message, state: FSMContext):
    """Команда для отладки и тестирования"""
    user_id = message.from_user.id
    await message.answer(f"Ваш ID: {user_id}\n\nТекущие данные состояния:\n{await state.get_data()}")
