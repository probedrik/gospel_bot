"""
Обработчики текстовых сообщений бота.
"""
from config.settings import MARKDOWN_ENABLED, MARKDOWN_MODE, MARKDOWN_BOLD_TITLE, MARKDOWN_QUOTE, MARKDOWN_ESCAPE
import logging
import re
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
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
from database.db_manager import db_manager

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
        "• 📚 Тематические подборки стихов (кнопка '📚 Темы' в главном меню)\n"
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
        for part in split_text(text):
            await message.answer(part)

        # Получаем английское сокращение для поиска в комментарии
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
        buttons = []
        if en_book:
            buttons.append([
                InlineKeyboardButton(
                    text="Толкование проф. Лопухина",
                    callback_data=f"open_commentary_{en_book}_{chapter}_0"
                )
            ])
            if ENABLE_GPT_EXPLAIN:
                buttons.append([
                    InlineKeyboardButton(
                        text="🤖 Разбор от ИИ",
                        callback_data=f"gpt_explain_{en_book}_{chapter}_0"
                    )
                ])
        if buttons:
            kb = InlineKeyboardMarkup(inline_keyboard=buttons)
            await message.answer("Доступны дополнительные действия:", reply_markup=kb)
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
        for part in split_text(text):
            await message.answer(part)
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
                # Клавиатура навигации по главам
                nav_kb = create_navigation_keyboard(
                    has_previous, has_next, is_bookmarked)
                await message.answer(
                    f"{bible_data.get_book_name(book_id)}, глава {chapter}",
                    reply_markup=nav_kb
                )
                # Кнопки "Толкование проф. Лопухина" и "🤖 Разбор от ИИ"
                extra_buttons = []
                if en_book:
                    extra_buttons.append([
                        InlineKeyboardButton(
                            text="Толкование проф. Лопухина",
                            callback_data=f"open_commentary_{en_book}_{chapter}_0"
                        )
                    ])
                if ENABLE_GPT_EXPLAIN:
                    extra_buttons.append([
                        InlineKeyboardButton(
                            text="🤖 Разбор от ИИ",
                            callback_data=f"gpt_explain_{en_book}_{chapter}_0"
                        )
                    ])
                if extra_buttons:
                    kb = InlineKeyboardMarkup(inline_keyboard=extra_buttons)
                    await message.answer("Доступны дополнительные действия:", reply_markup=kb)
            else:
                # Для стиха — как было
                if book_id:
                    buttons.append([
                        InlineKeyboardButton(
                            text="Открыть всю главу",
                            callback_data=f"open_chapter_{book_abbr}_{chapter}"
                        )
                    ])
                if en_book:
                    from utils.lopukhin_commentary import lopukhin_commentary
                    commentary = None
                    if verse:
                        commentary = lopukhin_commentary.get_commentary(
                            en_book, chapter, int(verse))
                    if not commentary:
                        commentary = lopukhin_commentary.get_commentary(
                            en_book, chapter, 0)
                    if commentary:
                        cb_data = f"open_commentary_{en_book}_{chapter}_{verse}"
                        buttons.append([
                            InlineKeyboardButton(
                                text="Толкование проф. Лопухина",
                                callback_data=cb_data
                            )
                        ])
                if ENABLE_GPT_EXPLAIN:
                    cb_data = f"gpt_explain_{en_book}_{chapter}_{verse}"
                    buttons.append([
                        InlineKeyboardButton(
                            text="🤖 Разбор от ИИ",
                            callback_data=cb_data
                        )
                    ])
                if buttons:
                    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
                    await message.answer("Доступны дополнительные действия:", reply_markup=kb)
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


@router.message(F.text == "📚 Темы")
async def show_topics_menu(message: Message):
    from utils.topics import get_topics_list
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    topics = get_topics_list()
    # Формируем inline-клавиатуру с кнопками по 2 в ряд
    buttons = []
    row = []
    for i, topic in enumerate(topics):
        row.append(InlineKeyboardButton(
            text=topic, callback_data=f"topic_{i}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("Выберите тему:", reply_markup=kb)


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
    topics = get_topics_list()
    idx = int(callback.data.split('_')[1])
    topic = topics[idx]
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
    match = re.match(r"([А-Яа-яёЁ0-9\s]+)\s(\d+)(?::(\d+)(-\d+)?)?", verse_ref)
    if match:
        book_raw = match.group(1).strip().lower()
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
        if book_id:
            buttons.append([
                InlineKeyboardButton(
                    text="Открыть всю главу", callback_data=f"open_chapter_{book_abbr}_{chapter}")
            ])
        if en_book:
            commentary = None
            if verse:
                commentary = lopukhin_commentary.get_commentary(
                    en_book, chapter, int(verse))
            if not commentary:
                commentary = lopukhin_commentary.get_commentary(
                    en_book, chapter, 0)
            if commentary:
                if not verse or verse == '0' or verse == 0:
                    cb_data = f"open_commentary_{en_book}_{chapter}_0"
                else:
                    cb_data = f"open_commentary_{en_book}_{chapter}_{verse}"
                buttons.append([
                    InlineKeyboardButton(
                        text="Толкование проф. Лопухина",
                        callback_data=cb_data
                    )
                ])
        if ENABLE_GPT_EXPLAIN:
            if verse is not None:
                cb_data = f"gpt_explain_{en_book}_{chapter}_{verse}"
            else:
                cb_data = f"gpt_explain_{en_book}_{chapter}_0"
            buttons.append([
                InlineKeyboardButton(
                    text="🤖 Разбор от ИИ",
                    callback_data=cb_data
                )
            ])
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
        msg = await callback.message.answer(formatted, **opts)
        if state:
            await state.update_data(last_topic_commentary_msg_id=msg.message_id)
    else:
        await callback.message.answer("Толкование не найдено.")
    await callback.answer()


@router.callback_query(F.data.regexp(r'^open_commentary_([A-Za-z0-9]+)_(\d+)_0$'))
async def open_commentary_chapter_paginated(callback: CallbackQuery):
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
    # Сохраняем в state список комментариев
    await callback.message.delete()
    await show_commentary_page(callback, book, chapter, all_comments, 0)


@router.callback_query(F.data.regexp(r'^commentary_page_([A-Zazl0-9]+)_(\d+)_(\d+)$'))
async def commentary_page_callback(callback: CallbackQuery):
    match = re.match(
        r'^commentary_page_([A-Zazl0-9]+)_(\d+)_(\d+)$', callback.data)
    if not match:
        await callback.answer("Ошибка запроса")
        return
    book = match.group(1)
    chapter = int(match.group(2))
    idx = int(match.group(3))
    from utils.lopukhin_commentary import lopukhin_commentary
    all_comments = lopukhin_commentary.get_all_commentaries_for_chapter(
        book, chapter)
    await callback.message.delete()
    await show_commentary_page(callback, book, chapter, all_comments, idx)


async def show_commentary_page(callback, book, chapter, all_comments, idx):
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
    markup = InlineKeyboardMarkup(
        inline_keyboard=[nav_kb] if nav_kb else [] +
        ([extra_kb] if extra_kb else [])
    )
    # Отправляем толкование с учётом настроек форматирования
    formatted, opts = format_ai_or_commentary(text, title)
    msg = await callback.message.answer(formatted, reply_markup=markup, **opts)
    # Сохраняем id сообщения с толкованием
    if state:
        await state.update_data(last_topic_commentary_msg_id=msg.message_id)


@router.callback_query(F.data.regexp(r'^gpt_explain_([A-Za-z0-9]+)_(\d+)_(\d+)$'))
async def gpt_explain_callback(callback: CallbackQuery, state: FSMContext = None):
    import re
    # --- AI LIMIT CHECK ---
    user_id = callback.from_user.id if hasattr(
        callback, "from_user") else callback.message.from_user.id
    from handlers.text_messages import ai_check_and_increment_db
    if not await ai_check_and_increment_db(user_id):
        await callback.message.answer("Вы исчерпали лимит ИИ-запросов на сегодня.")
        await callback.answer()
        return
    match = re.match(
        r'^gpt_explain_([A-Za-z0-9]+)_(\d+)_(\d+)$', callback.data)
    if not match:
        await callback.answer("Ошибка запроса к ИИ")
        return
    book = match.group(1)
    chapter = int(match.group(2))
    verse = int(match.group(3))
    # Получаем текст главы или стиха
    text = ""
    # Формируем ссылку для get_verse_by_reference с русским сокращением
    from utils.bible_data import bible_data
    ru_book = bible_data.book_synonyms.get(book.lower(), book)
    book_id = bible_data.get_book_id(ru_book)
    reference = f"{ru_book} {chapter}:{verse}" if verse != 0 else f"{ru_book} {chapter}"
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
        try:
            text, _ = await get_verse_by_reference(st, reference)
        except Exception:
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
        for part in split_text(formatted):
            msg = await callback.message.answer(part, **opts)
            if state:
                await state.update_data(last_topic_ai_msg_id=msg.message_id)
    except Exception as e:
        logger.error(f"Ошибка при обращении к ИИ: {e}")
        await callback.message.answer("Произошла ошибка при обращении к ИИ. Попробуйте позже.")
    await callback.answer()


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
    # Удаляем предыдущую главу и все связанные сообщения (толкования, ИИ-разборы)
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
    for part in split_text(text):
        sent = await callback.message.answer(part)
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
    await callback.message.answer(
        f"{bible_data.get_book_name(book_id)}, глава {chapter}",
        reply_markup=create_navigation_keyboard(
            has_previous, has_next, is_bookmarked)
    )
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
    extra_buttons = []
    if en_book:
        extra_buttons.append([
            InlineKeyboardButton(
                text="Толкование проф. Лопухина",
                callback_data=f"open_commentary_{en_book}_{chapter}_0"
            )
        ])
    if ENABLE_GPT_EXPLAIN:
        extra_buttons.append([
            InlineKeyboardButton(
                text="🤖 Разбор от ИИ",
                callback_data=f"gpt_explain_{en_book}_{chapter}_0"
            )
        ])
    if extra_buttons:
        kb = InlineKeyboardMarkup(inline_keyboard=extra_buttons)
        await callback.message.answer("Доступны дополнительные действия:", reply_markup=kb)
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
    Форматирует текст для вывода в Telegram с учётом настроек Markdown/MarkdownV2/HTML.
    title: если задан, будет выделен жирным (или как цитата, если включено)
    """
    if not MARKDOWN_ENABLED:
        return f"{title}\n\n{text}" if title else text, {}
    mode = MARKDOWN_MODE
    result = text
    if MARKDOWN_ESCAPE and mode.lower() == "markdownv2":
        # Экранируем все спецсимволы строго по Telegram MarkdownV2
        def escape_md(s):
            # Важно: сначала экранируем обратный слэш, потом остальные символы!
            s = s.replace('\\', '\\\\')
            chars = r'_ * [ ] ( ) ~ ` > # + - = | { } . !'
            for c in chars.split():
                s = s.replace(c, f'\\{c}')
            return s
        result = escape_md(result)
        if title:
            title = escape_md(title)
    if MARKDOWN_BOLD_TITLE and title:
        if mode.lower() == "markdownv2":
            title = f"*{title}*"
        elif mode.lower() == "markdown":
            title = f"**{title}**"
        elif mode.lower() == "html":
            title = f"<b>{title}</b>"
    if MARKDOWN_QUOTE:
        # Каждая строка как цитата
        result = '\n'.join(f"> {line}" for line in result.splitlines())
    if title:
        result = f"{title}\n\n{result}"
    return result, {"parse_mode": mode}
