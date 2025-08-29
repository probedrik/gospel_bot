"""
Обработчик ИИ помощника для подбора библейских отрывков по проблемам пользователя.
"""
import logging
import re
import html
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup


from handlers.text_messages import ai_check_and_increment_db, format_ai_or_commentary
from utils.api_client import bible_api, ask_gpt_bible_verses
from utils.bible_data import bible_data
from utils.text_utils import split_text, get_verses_parse_mode
from database.universal_manager import universal_db_manager as db_manager

# Инициализация логгера
logger = logging.getLogger(__name__)

# Создаем роутер для ИИ помощника
router = Router()


class AIAssistantStates(StatesGroup):
    waiting_for_problem = State()
    showing_verses = State()


@router.callback_query(F.data == "ai_assistant")
async def start_ai_assistant(callback: CallbackQuery, state: FSMContext):
    """Начинает процесс подбора стихов с ИИ помощником"""
    user_id = callback.from_user.id

    # Проверяем лимит ИИ
    if not await ai_check_and_increment_db(user_id):
        from config.ai_settings import AI_DAILY_LIMIT
        await callback.answer(
            f"❌ Превышен дневной лимит ИИ-запросов ({AI_DAILY_LIMIT}). Попробуйте завтра.",
            show_alert=True
        )
        return

    # Устанавливаем состояние ожидания описания проблемы
    await state.set_state(AIAssistantStates.waiting_for_problem)

    await callback.message.answer(
        "🤖 <b>ИИ помощник для подбора библейских отрывков</b>\n\n"
        "Опишите кратко вашу проблему или ситуацию, с которой вы столкнулись. "
        "ИИ поможет подобрать 3-5 подходящих библейских отрывков, которые могут помочь "
        "в переживании и преодолении этих трудностей.\n\n"
        "Например:\n"
        "• Чувствую тревогу и беспокойство\n"
        "• Переживаю трудности в отношениях\n"
        "• Ищу утешение после потери\n"
        "• Нужна мудрость для принятия решения\n\n"
        "Напишите ваше сообщение:",
        parse_mode="HTML"
    )

    await callback.answer()


@router.message(AIAssistantStates.waiting_for_problem)
async def process_problem_description(message: Message, state: FSMContext):
    """Обрабатывает описание проблемы и запрашивает подходящие стихи у ИИ"""
    user_id = message.from_user.id
    problem_text = message.text.strip()

    if len(problem_text) < 10:
        await message.answer(
            "❌ Пожалуйста, опишите проблему более подробно (минимум 10 символов)."
        )
        return

    if len(problem_text) > 500:
        await message.answer(
            "❌ Описание слишком длинное. Пожалуйста, опишите проблему кратко (до 500 символов)."
        )
        return

    # Проверяем квоту ИИ перед выполнением запроса
    try:
        from services.ai_quota_manager import ai_quota_manager
        can_use_ai = await ai_quota_manager.check_and_increment_usage(user_id)

        if not can_use_ai:
            quota_info = await ai_quota_manager.get_user_quota_info(user_id)
            await message.answer(
                f"❌ **Дневной лимит ИИ исчерпан**\n\n"
                f"📊 Использовано: {quota_info['used_today']}/{quota_info['daily_limit']}\n"
                f"⏰ Новые запросы через: {quota_info['hours_until_reset']} ч.\n\n"
                f"💡 Используйте поиск по темам или сохраненные разборы!",
                parse_mode="Markdown"
            )
            await state.clear()
            return
    except Exception as e:
        logger.error(f"Ошибка проверки квоты ИИ: {e}")
        # Продолжаем выполнение, если проверка квоты не удалась

    # Очищаем состояние
    await state.clear()

    # Показываем индикатор загрузки
    loading_msg = await message.answer("🔄 ИИ подбирает подходящие библейские отрывки...")

    try:
        # Запрашиваем подходящие стихи у ИИ
        verses_response = await ask_gpt_bible_verses(problem_text)

        if not verses_response or verses_response.startswith("Извините"):
            await loading_msg.edit_text(
                "❌ Не удалось получить рекомендации от ИИ. Попробуйте позже или обратитесь к разделу 'Темы'."
            )
            return

        # Парсим ответ ИИ и извлекаем ссылки на стихи
        verse_references = parse_ai_response(verses_response)

        if not verse_references:
            await loading_msg.edit_text(
                "❌ ИИ не смог подобрать подходящие стихи. Попробуйте переформулировать вашу проблему или обратитесь к разделу 'Темы'."
            )
            return

        # Создаем кнопки со ссылками на стихи
        buttons = []
        for verse_ref in verse_references[:5]:  # Ограничиваем до 5 стихов
            buttons.append([
                InlineKeyboardButton(
                    text=verse_ref,
                    callback_data=f"ai_verse_{verse_ref}"
                )
            ])

        # Добавляем кнопку возврата в меню
        buttons.append([
            InlineKeyboardButton(
                text="🏠 Вернуться в меню",
                callback_data="back_to_menu"
            )
        ])

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        # Приводим ответ к тому же стилю, что и разбор главы: цитата + обычный текст
        import re as _re
        cleaned_ai_text = _re.sub(r'<[^>]*>', '', verses_response).strip()
        formatted_text, opts = format_ai_or_commentary(
            cleaned_ai_text,
            title="🤖 Рекомендации ИИ"
        )

        # Разбиваем на части, чтобы избежать обрезки Telegram (4096 символов)
        text_parts = list(split_text(formatted_text))

        # Отправляем частями: последняя часть — с кнопками
        for idx, part in enumerate(text_parts):
            is_last = idx == len(text_parts) - 1
            if idx == 0:
                await loading_msg.edit_text(
                    part,
                    parse_mode=opts.get("parse_mode", "HTML"),
                    reply_markup=keyboard if is_last else None
                )
            else:
                await message.answer(
                    part,
                    parse_mode=opts.get("parse_mode", "HTML"),
                    reply_markup=keyboard if is_last else None
                )

        # Сохраняем данные для возможности возврата
        await state.set_state(AIAssistantStates.showing_verses)
        await state.update_data(
            problem_text=problem_text,
            verse_references=verse_references,
            verses_message_text=formatted_text
        )

    except Exception as e:
        logger.error(f"Ошибка при обработке запроса к ИИ: {e}", exc_info=True)
        await loading_msg.edit_text(
            "❌ Произошла ошибка при обработке запроса. Попробуйте позже."
        )


@router.callback_query(F.data.startswith("ai_verse_"))
async def show_ai_recommended_verse(callback: CallbackQuery, state: FSMContext):
    """Показывает рекомендованный ИИ стих"""
    verse_ref = callback.data[len("ai_verse_"):]

    try:
        # Получаем текст стиха
        from handlers.verse_reference import get_verse_by_reference
        text, _ = await get_verse_by_reference(state, verse_ref)

        if text.startswith("Ошибка"):
            await callback.answer("❌ Не удалось найти указанный стих")
            return

        # Отправляем текст стиха
        parse_mode = get_verses_parse_mode()
        for part in split_text(text):
            await callback.message.answer(part, parse_mode=parse_mode)

        # Создаем кнопки для дополнительных действий
        buttons = await create_ai_verse_buttons(verse_ref, callback.from_user.id, from_ai_assistant=True)

        if buttons:
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
            await callback.message.answer(
                "Выберите действие:",
                reply_markup=keyboard
            )

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при показе стиха: {e}", exc_info=True)
        await callback.answer("❌ Произошла ошибка при получении стиха")


async def create_ai_verse_buttons(verse_ref: str, user_id: int, from_ai_assistant: bool = False) -> list:
    """Создает кнопки для действий со стихом, рекомендованным ИИ"""
    buttons = []

    # Парсим ссылку на стих
    import re
    match = re.match(
        r"([А-Яа-яёЁ0-9\s]+)\s(\d+)(?::(\d+)(?:-(\d+))?)?", verse_ref)
    if not match:
        return buttons

    book_raw = match.group(1).strip().lower()
    chapter = int(match.group(2))
    verse_start = match.group(3)
    verse_end = match.group(4) if match.group(4) else verse_start

    book_abbr = bible_data.normalize_book_name(book_raw)
    book_id = bible_data.get_book_id(book_abbr)

    if not book_id:
        return buttons

    # Создаем ряд кнопок для максимального использования ширины
    action_row = []

    # Кнопка "Разбор ИИ"
    from config.ai_settings import ENABLE_GPT_EXPLAIN
    if ENABLE_GPT_EXPLAIN:
        # Проверяем есть ли сохраненное толкование
        saved_commentary = None
        try:
            verse_start_num = int(verse_start) if verse_start else 0
            verse_end_num = int(verse_end) if verse_end else verse_start_num
            saved_commentary = await db_manager.get_saved_commentary(
                user_id, book_id, chapter, chapter, verse_start_num, verse_end_num, "ai"
            )
        except:
            pass

        # Определяем текст кнопки
        ai_text = "🔄 Обновить разбор ИИ" if saved_commentary else "🤖 Разбор от ИИ"

        # Получаем английское название книги для callback
        en_to_ru = {
            "Gen": "Быт", "Exod": "Исх", "Lev": "Лев", "Num": "Чис", "Deut": "Втор",
            "Josh": "Нав", "Judg": "Суд", "Ruth": "Руф", "1Sam": "1Цар", "2Sam": "2Цар",
            "1Kgs": "3Цар", "2Kgs": "4Цар", "1Chr": "1Пар", "2Chr": "2Пар", "Ezra": "Езд",
            "Neh": "Неем", "Esth": "Есф", "Job": "Иов", "Ps": "Пс", "Prov": "Прит",
            "Eccl": "Еккл", "Song": "Песн", "Isa": "Ис", "Jer": "Иер", "Lam": "Плач",
            "Ezek": "Иез", "Dan": "Дан", "Hos": "Ос", "Joel": "Иоил", "Amos": "Ам",
            "Obad": "Авд", "Jonah": "Ион", "Mic": "Мих", "Naum": "Наум", "Hab": "Авв",
            "Zeph": "Соф", "Hag": "Агг", "Zech": "Зах", "Mal": "Мал", "Matt": "Мф",
            "Mark": "Мк", "Luke": "Лк", "John": "Ин", "Acts": "Деян", "Jas": "Иак",
            "1Pet": "1Пет", "2Pet": "2Пет", "1John": "1Ин", "2John": "2Ин", "3John": "3Ин",
            "Jude": "Иуд", "Rom": "Рим", "1Cor": "1Кор", "2Cor": "2Кор", "Gал": "Гал",
            "Eph": "Еф", "Phil": "Флп", "Col": "Кол", "1Thess": "1Фес", "2Thess": "2Фес",
            "1Tim": "1Тим", "2Tim": "2Тим", "Titus": "Тит", "Phlm": "Флм", "Heb": "Евр",
            "Rev": "Откр"
        }

        en_book = None
        for en, ru in en_to_ru.items():
            if ru == book_abbr:
                en_book = en
                break

        if en_book:
            # Формируем callback для диапазона стихов
            if verse_start and verse_end and verse_start != verse_end:
                verse_callback = f"{verse_start}-{verse_end}"
            else:
                verse_callback = verse_start if verse_start else "0"

            # Добавляем кнопку "Разбор ИИ" в ряд
            action_row.append(
                InlineKeyboardButton(
                    text=ai_text,
                    callback_data=f"gpt_explain_{en_book}_{chapter}_{verse_callback}"
                )
            )

    # Кнопка "Открыть всю главу" в том же ряду
    action_row.append(
        InlineKeyboardButton(
            text="📖 Открыть всю главу",
            callback_data=f"open_chapter_{book_abbr}_{chapter}"
        )
    )

    # Добавляем ряд кнопок действий
    if action_row:
        buttons.append(action_row)

    # Кнопка закладки для стиха/диапазона стихов
    from utils.bookmark_utils import create_bookmark_button
    from handlers.bookmark_handlers import check_if_bookmarked

    verse_start_num = int(verse_start) if verse_start else None
    verse_end_num = int(
        verse_end) if verse_end and verse_end != verse_start else None

    # Проверяем, добавлен ли стих в закладки
    is_bookmarked = await check_if_bookmarked(
        user_id, book_id, chapter, None, verse_start_num, verse_end_num
    )

    bookmark_button = create_bookmark_button(
        book_id=book_id,
        chapter_start=chapter,
        verse_start=verse_start_num,
        verse_end=verse_end_num,
        is_bookmarked=is_bookmarked
    )

    buttons.append([bookmark_button])

    # Кнопка возврата (зависит от того, откуда пришел пользователь)
    if from_ai_assistant:
        buttons.append([
            InlineKeyboardButton(
                text="⬅️ Вернуться к отрывкам",
                callback_data="back_to_ai_verses"
            )
        ])
    else:
        buttons.append([
            InlineKeyboardButton(
                text="🏠 Вернуться в меню",
                callback_data="back_to_menu"
            )
        ])

    return buttons


@router.callback_query(F.data == "back_to_ai_verses")
async def back_to_ai_verses(callback: CallbackQuery, state: FSMContext):
    """Возвращает к списку отрывков от ИИ помощника"""
    try:
        # Получаем сохраненные данные
        data = await state.get_data()
        problem_text = data.get('problem_text')
        verse_references = data.get('verse_references')
        verses_message_text = data.get('verses_message_text')

        if not verse_references:
            await callback.answer("❌ Данные отрывков не найдены")
            return

        # Создаем кнопки со ссылками на стихи заново
        buttons = []
        for verse_ref in verse_references[:5]:  # Ограничиваем до 5 стихов
            buttons.append([
                InlineKeyboardButton(
                    text=verse_ref,
                    callback_data=f"ai_verse_{verse_ref}"
                )
            ])

        # Добавляем кнопку возврата в меню
        buttons.append([
            InlineKeyboardButton(
                text="🏠 Вернуться в меню",
                callback_data="back_to_menu"
            )
        ])

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        await callback.message.edit_text(
            verses_message_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при возврате к отрывкам: {e}", exc_info=True)
        await callback.answer("❌ Произошла ошибка")


def parse_ai_response(response: str) -> list:
    """Извлекает ссылки на библейские стихи из произвольного текста ответа ИИ.

    Поддерживает форматы с диапазонами и одиночными стихами. Ищет по всему тексту,
    а не только по разделителям ';', чтобы работать с новыми промптами с описаниями.
    """
    if not response or response.startswith("Извините"):
        return []

    # Нормализация текста: заменяем типографские тире на обычный дефис
    text = response.replace("\u2013", "-").replace("\u2014", "-")
    # Упрощаем множественные пробелы
    import re as _re
    text = _re.sub(r"\s+", " ", text)

    # Регулярка: Название/сокращение книги (рус), пробел, глава:стих[-стих]
    # Примеры: "Мф 6:25-34", "Пс 22:1-6", "Иак 1:5", "Рим 8:28"
    # Допускаем точку в сокращениях (напр. "Ин.") и разные тире
    pattern = r"([А-Яа-яЁё0-9][А-Яа-яЁё0-9\.\s]{0,30})\s(\d+):(\d+)(?:[-](\d+))?"
    matches = _re.findall(pattern, text)

    candidates = []
    for book, chapter, verse_start, verse_end in matches:
        book_clean = _re.sub(r"\s+", " ", book).strip().rstrip('.')
        if verse_end:
            ref = f"{book_clean} {chapter}:{verse_start}-{verse_end}"
        else:
            ref = f"{book_clean} {chapter}:{verse_start}"
        candidates.append(ref)

    # Удаляем дубли, сохраняем порядок
    seen = set()
    valid_refs = []
    for ref in candidates:
        if ref not in seen:
            seen.add(ref)
            valid_refs.append(ref)

    logger.info(
        f"Извлечено {len(valid_refs)} валидных ссылок из ответа ИИ: {valid_refs}")
    return valid_refs
