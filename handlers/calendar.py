"""
Обработчики для функционала православного календаря
"""
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup

from utils.orthodox_calendar import orthodox_calendar
from keyboards.calendar import create_calendar_keyboard, create_calendar_settings_keyboard
from services.ai_settings_manager import ai_settings_manager
from config.settings import ADMIN_USER_ID

logger = logging.getLogger(__name__)
router = Router()


async def show_calendar_for_date(message: Message, state: FSMContext, target_date: datetime = None, user_id: int = None):
    """Показывает календарь для указанной даты"""
    try:
        if target_date is None:
            target_date = datetime.now()

        if user_id is None:
            user_id = message.from_user.id

        # Получаем настройки календаря из Supabase
        settings = await get_calendar_default_settings(user_id)
        logger.info(
            f"Настройки календаря из Supabase (show_calendar_for_date): {settings}")

        # Получаем данные календаря
        calendar_html = await orthodox_calendar.get_calendar_data(target_date, settings)

        if not calendar_html:
            await message.answer("❌ Не удалось получить данные календаря")
            return

        # Парсим HTML в структурированные данные
        calendar_data = orthodox_calendar.parse_calendar_content(calendar_html)

        # Форматируем сообщение
        message_text = _format_calendar_message(calendar_data, target_date)

        # Создаем клавиатуру
        keyboard = create_calendar_keyboard(
            target_date,
            calendar_data.get('scripture_references', []),
            show_settings=True,
            user_id=user_id
        )

        await message.answer(message_text, reply_markup=keyboard, parse_mode='HTML')

    except Exception as e:
        logger.error(f"Ошибка при показе календаря: {e}", exc_info=True)
        await message.answer("❌ Ошибка при получении календаря")


async def show_calendar_for_callback(callback: CallbackQuery, state: FSMContext, target_date: datetime = None):
    """Показывает календарь для указанной даты (версия для callback)"""
    try:
        if target_date is None:
            target_date = datetime.now()

        user_id = callback.from_user.id

        # Получаем настройки календаря из Supabase
        settings = await get_calendar_default_settings(user_id)
        logger.info(
            f"Настройки календаря из Supabase (show_calendar_for_callback): {settings}")

        # Получаем данные календаря
        calendar_html = await orthodox_calendar.get_calendar_data(target_date, settings)

        if not calendar_html:
            await callback.answer("❌ Не удалось получить данные календаря")
            return

        # Парсим HTML в структурированные данные
        calendar_data = orthodox_calendar.parse_calendar_content(calendar_html)

        # Форматируем сообщение
        message_text = _format_calendar_message(calendar_data, target_date)

        # Создаем клавиатуру
        keyboard = create_calendar_keyboard(
            target_date,
            calendar_data.get('scripture_references', []),
            show_settings=True,
            user_id=user_id
        )

        try:
            await callback.message.edit_text(message_text, reply_markup=keyboard, parse_mode='HTML')
        except Exception:
            # Если не удалось отредактировать, отправляем новое сообщение
            await callback.message.answer(message_text, reply_markup=keyboard, parse_mode='HTML')

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при показе календаря: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при получении календаря")


def _format_calendar_message(calendar_data: Dict[str, Any], target_date: datetime) -> str:
    """Форматирует сообщение календаря"""
    parts = []

    # Добавляем дату
    if calendar_data.get('date'):
        parts.append(f"📅 <b>{calendar_data['date']}</b>")

    # Добавляем заголовок (седмица, глас)
    if calendar_data.get('header'):
        header_text = calendar_data['header'].replace('<br>', '\n').strip()
        # Убираем лишние HTML и форматируем
        header_clean = re.sub(r'<[^>]+>', '', header_text)
        if header_clean:
            parts.append(f"⛪ <i>{header_clean}</i>")

    # Добавляем память святых
    if calendar_data.get('saints'):
        parts.append(f"<b>📿 Память святых:</b>")
        for saint in calendar_data['saints']:
            saint_clean = saint.strip()
            if saint_clean:
                parts.append(f"• {saint_clean}")

    # Добавляем чтения дня (текст + кнопки)
    if calendar_data.get('scripture_readings'):
        parts.append(f"<b>📖 Чтения дня:</b>")
        for reading in calendar_data['scripture_readings']:
            parts.append(f"• {reading}")
        parts.append(f"<i>📱 Открыть чтения кнопками ниже</i>")

    # Добавляем тропари если включены
    if calendar_data.get('tropars'):
        parts.append(f"\n<b>🎵 Тропари:</b>")
        for tropar in calendar_data['tropars']:
            if tropar.strip():
                parts.append(tropar)

    # Если нет никакого контента, добавляем дату по умолчанию
    if not parts:
        parts.append(f"📅 <b>{target_date.strftime('%d.%m.%Y')}</b>")
        parts.append("📋 Данные календаря недоступны")

    result = "\n".join(parts)
    logger.info(f"Сформированное сообщение календаря: {result[:200]}...")
    return result


async def get_calendar_default_settings(user_id: int) -> Dict[str, Any]:
    """Получает настройки календаря по умолчанию из базы данных"""
    try:
        # Используем готовую функцию из ai_settings_manager
        settings = await ai_settings_manager.get_calendar_default_settings()
        return settings

    except Exception as e:
        logger.error(f"Ошибка при получении настроек календаря: {e}")
        # Возвращаем настройки по умолчанию
        return {
            'header': True,
            'lives': 4,
            'tropars': 0,
            'scripture': 1,
            'date_format': True
        }


@router.callback_query(F.data == "calendar_today")
async def calendar_today_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик для показа календаря на сегодня"""
    await show_calendar_for_callback(callback, state, datetime.now())


@router.callback_query(F.data.startswith("calendar_date_"))
async def calendar_date_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик для показа календаря на конкретную дату"""
    try:
        # Извлекаем дату из callback_data
        date_str = callback.data.replace("calendar_date_", "")
        year, month, day = map(int, date_str.split("_"))
        target_date = datetime(year, month, day)

        await show_calendar_for_callback(callback, state, target_date)

    except Exception as e:
        logger.error(f"Ошибка при обработке даты календаря: {e}")
        await callback.answer("❌ Ошибка при обработке даты")


@router.callback_query(F.data.startswith("scripture_read_complex_"))
async def scripture_read_complex(callback: CallbackQuery, state: FSMContext):
    """Обработчик для сложных чтений с несколькими частями"""
    try:
        logger.info(
            f"scripture_read_complex вызван с данными: {callback.data}")

        # Парсим callback_data: scripture_read_complex_book_id_chapter_verse_start_verse_end|book_id_chapter_verse_start_verse_end|...
        data_part = callback.data.replace("scripture_read_complex_", "")
        ref_parts = data_part.split("|")
        logger.info(f"Части сложного чтения: {ref_parts}")

        from utils.bible_data import bible_data
        from handlers.verse_reference import get_verse_by_reference
        from utils.text_utils import get_verses_parse_mode, split_text
        from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

        # Отмечаем что пользователь пришел из календаря
        await state.update_data(from_calendar=True)

        all_texts = []
        all_references = []
        combined_book_ids = set()
        combined_chapters = set()

        # Обрабатываем каждую часть
        for ref_part in ref_parts:
            parts = ref_part.split("_")
            if len(parts) != 4:
                continue

            book_id = int(parts[0])
            chapter = int(parts[1])
            verse_start = int(parts[2])
            verse_end = int(parts[3])

            combined_book_ids.add(book_id)
            combined_chapters.add(chapter)

            book_name = bible_data.get_book_name(book_id)
            if not book_name:
                continue

            if verse_start == verse_end:
                reference = f"{book_name} {chapter}:{verse_start}"
            else:
                reference = f"{book_name} {chapter}:{verse_start}-{verse_end}"

            all_references.append(reference)
            logger.info(f"Добавляем ссылку: {reference}")

            # Получаем текст для каждой части
            text, meta = await get_verse_by_reference(state, reference)
            all_texts.append(f"<b>{reference}</b>\n{text}")

        # Объединяем все тексты
        combined_text = "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━\n\n".join(all_texts)

        parse_mode = get_verses_parse_mode()
        for part in split_text(combined_text):
            await callback.message.answer(part, parse_mode=parse_mode)

        # Создаем кнопки действий
        # Если все части из одной книги, используем первую для кнопок
        if len(combined_book_ids) == 1:
            book_id = list(combined_book_ids)[0]
            chapter = list(combined_chapters)[0] if len(
                combined_chapters) == 1 else min(combined_chapters)

            from utils.bible_data import create_chapter_action_buttons, get_english_book_abbreviation
            from config.ai_settings import ENABLE_GPT_EXPLAIN

            en_book = get_english_book_abbreviation(book_id)

            all_buttons = []

            # Добавляем кнопку для каждой главы если несколько глав
            if len(combined_chapters) > 1:
                for ch in sorted(combined_chapters):
                    ru_book_abbr = None
                    for abbr, b_id in bible_data.book_abbr_dict.items():
                        if b_id == book_id:
                            ru_book_abbr = abbr
                            break

                    if ru_book_abbr:
                        all_buttons.append([
                            InlineKeyboardButton(
                                text=f"📖 Открыть главу {ch}",
                                callback_data=f"open_chapter_{ru_book_abbr}_{ch}"
                            )
                        ])

            # Создаем специальную кнопку ИИ разбора для сложного чтения
            if ENABLE_GPT_EXPLAIN:
                # Формируем данные всех частей для передачи в ИИ
                complex_parts = []
                for ref_part in ref_parts:
                    parts = ref_part.split("_")
                    if len(parts) == 4:
                        complex_parts.append(ref_part)

                if complex_parts:
                    all_buttons.append([
                        InlineKeyboardButton(
                            text="🤖 Разбор сложного чтения от ИИ",
                            callback_data=f"gpt_explain_complex_{'|'.join(complex_parts)}"
                        )
                    ])

            # Добавляем стандартные кнопки действий только для первой главы (без ИИ разбора)
            action_buttons = await create_chapter_action_buttons(
                book_id, chapter, en_book, user_id=callback.from_user.id,
                exclude_ai=True  # Исключаем стандартную кнопку ИИ
            )

            if action_buttons:
                all_buttons.extend(action_buttons)

            if all_buttons:
                await callback.message.answer(
                    "Выберите действие:",
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=all_buttons)
                )

        logger.info("Сложное чтение показано успешно")
        await callback.answer()

    except Exception as e:
        await callback.answer("❌ Ошибка при показе сложного чтения", show_alert=True)
        logger.error(f"Ошибка при показе сложного чтения: {e}", exc_info=True)


@router.callback_query(F.data.startswith("scripture_read_"))
async def scripture_read(callback: CallbackQuery, state: FSMContext):
    """Обработчик для чтения Евангельских отрывков"""
    try:
        logger.info(f"scripture_read вызван с данными: {callback.data}")

        # Парсим callback_data: scripture_read_book_id_chapter_verse_start_verse_end
        parts = callback.data.split("_")
        logger.info(f"Части callback_data: {parts}")

        if len(parts) != 6:
            await callback.answer("❌ Неверный формат данных", show_alert=True)
            return

        book_id = int(parts[2])
        chapter = int(parts[3])
        verse_start = int(parts[4])
        verse_end = int(parts[5])
        logger.info(
            f"Парсинг успешен: book_id={book_id}, chapter={chapter}, verse_start={verse_start}, verse_end={verse_end}")

        from utils.bible_data import bible_data
        book_name = bible_data.get_book_name(book_id)
        logger.info(f"Название книги: {book_name}")

        if not book_name:
            await callback.answer("❌ Книга не найдена", show_alert=True)
            return

        if verse_start == verse_end:
            reference = f"{book_name} {chapter}:{verse_start}"
        else:
            reference = f"{book_name} {chapter}:{verse_start}-{verse_end}"

        logger.info(f"Сформированная ссылка: {reference}")
        logger.info(f"Используем ID: {book_id}")

        from handlers.verse_reference import get_verse_by_reference
        from utils.text_utils import get_verses_parse_mode, split_text
        from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
        from utils.bible_data import create_chapter_action_buttons, get_english_book_abbreviation

        # Отмечаем что пользователь пришел из календаря
        await state.update_data(from_calendar=True)

        text, meta = await get_verse_by_reference(state, reference)

        parse_mode = get_verses_parse_mode()
        for part in split_text(text):
            await callback.message.answer(part, parse_mode=parse_mode)

        ru_book_abbr = None
        for abbr, b_id in bible_data.book_abbr_dict.items():
            if b_id == book_id:
                ru_book_abbr = abbr
                break

        en_book = get_english_book_abbreviation(book_id)
        action_buttons = await create_chapter_action_buttons(
            book_id, chapter, en_book, user_id=callback.from_user.id,
            verse_start=verse_start, verse_end=verse_end
        )

        all_buttons = []
        if ru_book_abbr:
            open_chapter_button = [
                InlineKeyboardButton(
                    text="📖 Открыть всю главу",
                    callback_data=f"open_chapter_{ru_book_abbr}_{chapter}"
                )
            ]
            all_buttons.append(open_chapter_button)

        if action_buttons:
            all_buttons.extend(action_buttons)

        if all_buttons:
            await callback.message.answer(
                "Выберите действие:",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=all_buttons)
            )
        else:
            logger.warning("Не удалось создать кнопки для чтения")

        logger.info("Чтение показано успешно")
        await callback.answer()
        logger.info("Callback обработан успешно")

    except (ValueError, IndexError) as e:
        await callback.answer("❌ Ошибка при открытии чтения", show_alert=True)
        logger.error(f"Ошибка при обработке scripture_read: {e}")
    except Exception as e:
        await callback.answer("❌ Ошибка при показе Евангельского чтения", show_alert=True)
        logger.error(
            f"Ошибка при показе Евангельского чтения: {e}", exc_info=True)


@router.callback_query(F.data == "separator")
async def separator_handler(callback: CallbackQuery):
    """Обработчик для разделителя - ничего не делает"""
    await callback.answer()


@router.callback_query(F.data == "calendar_back")
async def calendar_back_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик для возврата к календарю"""
    try:
        # Показываем календарь для текущей даты
        from datetime import datetime
        await show_calendar_for_callback(callback, state, datetime.now())
    except Exception as e:
        logger.error(f"Ошибка при возврате к календарю: {e}")
        await callback.answer("❌ Ошибка при возврате к календарю")


@router.callback_query(F.data == "calendar_setting_lives_next")
async def toggle_lives_setting(callback: CallbackQuery, state: FSMContext):
    """Переключает настройку жития святых (циклически 0-6)"""
    try:
        user_id = callback.from_user.id
        current_value = await ai_settings_manager.get_setting(user_id, 'calendar_default_lives')
        current_value = int(current_value) if isinstance(
            current_value, (int, str)) and str(current_value).isdigit() else 4

        # Циклический переход 0 -> 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 0
        new_value = (current_value + 1) % 7

        await ai_settings_manager.set_calendar_default_setting(user_id, 'lives', new_value)

        # Обновляем клавиатуру
        settings = await get_calendar_default_settings(user_id)
        keyboard = create_calendar_settings_keyboard(settings)

        try:
            await callback.message.edit_reply_markup(reply_markup=keyboard)
        except Exception:
            pass  # Игнорируем ошибки редактирования

        await callback.answer(f"Жития святых: {new_value}")

    except Exception as e:
        logger.error(f"Ошибка при переключении настройки lives: {e}")
        await callback.answer("❌ Ошибка при изменении настройки")


@router.callback_query(F.data == "calendar_setting_tropars_next")
async def toggle_tropars_setting(callback: CallbackQuery, state: FSMContext):
    """Переключает настройку тропарей (циклически 0-2)"""
    try:
        user_id = callback.from_user.id
        current_value = await ai_settings_manager.get_setting(user_id, 'calendar_default_tropars')
        current_value = int(current_value) if isinstance(
            current_value, (int, str)) and str(current_value).isdigit() else 0

        # Циклический переход 0 -> 1 -> 2 -> 0
        new_value = (current_value + 1) % 3

        await ai_settings_manager.set_calendar_default_setting(user_id, 'tropars', new_value)

        # Обновляем клавиатуру
        settings = await get_calendar_default_settings(user_id)
        keyboard = create_calendar_settings_keyboard(settings)

        try:
            await callback.message.edit_reply_markup(reply_markup=keyboard)
        except Exception:
            pass  # Игнорируем ошибки редактирования

        await callback.answer(f"Тропари: {new_value}")

    except Exception as e:
        logger.error(f"Ошибка при переключении настройки tropars: {e}")
        await callback.answer("❌ Ошибка при изменении настройки")


@router.callback_query(F.data == "calendar_setting_scripture_next")
async def toggle_scripture_setting(callback: CallbackQuery, state: FSMContext):
    """Переключает настройку Евангельских чтений (циклически 0-2)"""
    try:
        user_id = callback.from_user.id
        current_value = await ai_settings_manager.get_setting(user_id, 'calendar_default_scripture')
        current_value = int(current_value) if isinstance(
            current_value, (int, str)) and str(current_value).isdigit() else 1

        # Циклический переход 0 -> 1 -> 2 -> 0
        new_value = (current_value + 1) % 3

        await ai_settings_manager.set_calendar_default_setting(user_id, 'scripture', new_value)

        # Обновляем клавиатуру
        settings = await get_calendar_default_settings(user_id)
        keyboard = create_calendar_settings_keyboard(settings)

        try:
            await callback.message.edit_reply_markup(reply_markup=keyboard)
        except Exception:
            pass  # Игнорируем ошибки редактирования

        await callback.answer(f"Евангельские чтения: {new_value}")

    except Exception as e:
        logger.error(f"Ошибка при переключении настройки scripture: {e}")
        await callback.answer("❌ Ошибка при изменении настройки")


@router.callback_query(F.data == "calendar_settings")
async def calendar_settings_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик для настроек календаря"""
    try:
        user_id = callback.from_user.id

        # Проверяем права админа
        if user_id != ADMIN_USER_ID:
            await callback.answer("❌ Доступ запрещен", show_alert=True)
            return

        # Получаем текущие настройки
        settings = await get_calendar_default_settings(user_id)

        # Создаем клавиатуру настроек
        keyboard = create_calendar_settings_keyboard(settings)

        settings_text = "⚙️ <b>Настройки календаря</b>\n\n"
        settings_text += f"📿 Жития святых: {settings.get('lives', 4)}\n"
        settings_text += f"🎵 Тропари: {settings.get('tropars', 0)}\n"
        settings_text += f"📖 Евангельские чтения: {settings.get('scripture', 1)}\n"
        settings_text += f"📅 Формат даты: {'Включен' if settings.get('date_format', True) else 'Отключен'}\n"
        settings_text += f"📋 Заголовок: {'Включен' if settings.get('header', True) else 'Отключен'}"

        try:
            await callback.message.edit_text(settings_text, reply_markup=keyboard, parse_mode='HTML')
        except Exception:
            await callback.message.answer(settings_text, reply_markup=keyboard, parse_mode='HTML')

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при показе настроек календаря: {e}")
        await callback.answer("❌ Ошибка при показе настроек")


@router.callback_query(F.data == "calendar_settings_reset")
async def reset_calendar_settings(callback: CallbackQuery, state: FSMContext):
    """Сброс настроек календаря к значениям по умолчанию"""
    try:
        user_id = callback.from_user.id

        # Проверяем права админа
        if user_id != ADMIN_USER_ID:
            await callback.answer("❌ Доступ запрещен", show_alert=True)
            return

        # Устанавливаем значения по умолчанию
        await ai_settings_manager.set_calendar_default_setting(user_id, 'header', True)
        await ai_settings_manager.set_calendar_default_setting(user_id, 'lives', 4)
        await ai_settings_manager.set_calendar_default_setting(user_id, 'tropars', 0)
        await ai_settings_manager.set_calendar_default_setting(user_id, 'scripture', 1)
        await ai_settings_manager.set_calendar_default_setting(user_id, 'date_format', True)

        # Обновляем клавиатуру
        settings = await get_calendar_default_settings(user_id)
        keyboard = create_calendar_settings_keyboard(settings)

        settings_text = "⚙️ <b>Настройки календаря</b>\n\n"
        settings_text += f"📿 Жития святых: {settings.get('lives', 4)}\n"
        settings_text += f"🎵 Тропари: {settings.get('tropars', 0)}\n"
        settings_text += f"📖 Евангельские чтения: {settings.get('scripture', 1)}\n"
        settings_text += f"📅 Формат даты: {'Включен' if settings.get('date_format', True) else 'Отключен'}\n"
        settings_text += f"📋 Заголовок: {'Включен' if settings.get('header', True) else 'Отключен'}"

        try:
            await callback.message.edit_text(settings_text, reply_markup=keyboard, parse_mode='HTML')
        except Exception:
            pass  # Игнорируем ошибки редактирования

        await callback.answer("✅ Настройки сброшены к значениям по умолчанию")

    except Exception as e:
        logger.error(f"Ошибка при сбросе настроек календаря: {e}")
        await callback.answer("❌ Ошибка при сбросе настроек")
