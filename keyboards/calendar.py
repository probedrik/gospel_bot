"""
Клавиатуры для православного календаря
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config.settings import ADMIN_USER_ID


def create_calendar_keyboard(current_date: datetime = None,
                             scripture_references: List[Dict] = None,
                             show_settings: bool = True,
                             has_full_content: bool = False,
                             user_id: int = None) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для православного календаря

    Args:
        current_date: Текущая дата календаря
        scripture_references: Список ссылок на Евангельские чтения
        show_settings: Показывать ли кнопку настроек
    """
    if current_date is None:
        current_date = datetime.now()

    buttons = []

    # Кнопки навигации по датам
    prev_date = current_date - timedelta(days=1)
    next_date = current_date + timedelta(days=1)

    nav_buttons = []

    # Кнопка "Назад" (предыдущий день)
    nav_buttons.append(
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"calendar_date_{prev_date.strftime('%Y_%m_%d')}"
        )
    )

    # Кнопка "Сегодня"
    if current_date.date() != datetime.now().date():
        nav_buttons.append(
            InlineKeyboardButton(
                text="📅 Сегодня",
                callback_data="calendar_today"
            )
        )

    # Кнопка "Вперед" (следующий день)
    nav_buttons.append(
        InlineKeyboardButton(
            text="Вперёд ➡️",
            callback_data=f"calendar_date_{next_date.strftime('%Y_%m_%d')}"
        )
    )

    # Кнопки для Евангельских чтений
    if scripture_references:
        reading_buttons = []

        # Группируем ссылки по full_text (исходному чтению) для обработки сложных ссылок
        grouped_refs = {}
        for ref in scripture_references:
            full_text = ref.get('full_text', ref['display_text'])
            if full_text not in grouped_refs:
                grouped_refs[full_text] = []
            grouped_refs[full_text].append(ref)

        # Создаем кнопки для каждой группы
        for full_text, refs in grouped_refs.items():
            if len(refs) > 1:
                # Сложное чтение с несколькими частями
                # Создаем одну кнопку с callback для всех частей
                ref_parts = []
                for ref in refs:
                    ref_parts.append(
                        f"{ref['book_id']}_{ref['chapter']}_{ref['verse_start']}_{ref['verse_end']}")

                # Создаем краткое отображение для сложного чтения
                first_ref = refs[0]
                if len(refs) == 2 and refs[1]['chapter'] == first_ref['chapter'] + 1:
                    # Межглавный переход: показываем как "Книга гл1:стих-гл2:стих"
                    second_ref = refs[1]
                    button_text = f"📖 {first_ref['book_name']} {first_ref['chapter']}:{first_ref['verse_start']}-{second_ref['chapter']}:{second_ref['verse_end']}"
                else:
                    # Обычное сложное чтение
                    button_text = f"📖 {first_ref['display_text']}..."
                # Ограничиваем длину callback_data до 64 байт, как требует Telegram
                raw_data = f"scripture_read_complex_{'|'.join(ref_parts)}"
                callback_data = raw_data[:64]

                reading_buttons.append(
                    InlineKeyboardButton(
                        text=button_text,
                        callback_data=callback_data
                    )
                )
            else:
                # Простое чтение с одной частью
                ref = refs[0]
                # Простое чтение: формируем и уменьшаем при необходимости
                raw_simple = f"scripture_read_{ref['book_id']}_{ref['chapter']}_{ref['verse_start']}_{ref['verse_end']}"
                simple_cb = raw_simple[:64]
                reading_buttons.append(
                    InlineKeyboardButton(
                        text=f"📖 {ref['display_text']}",
                        callback_data=simple_cb
                    )
                )

        # Добавляем кнопки, разделяя на строки если больше 3
        if reading_buttons:
            if len(reading_buttons) <= 3:
                # До 3 кнопок - в одну строку
                buttons.append(reading_buttons)
            else:
                # Больше 3 кнопок - разделяем на строки по 3
                for i in range(0, len(reading_buttons), 3):
                    row = reading_buttons[i:i + 3]
                    buttons.append(row)

        # Добавляем разделитель после чтений
        buttons.append([
            InlineKeyboardButton(
                text="━━━━━━━━━━━━━━━━━━━━━━━━━",
                callback_data="separator"
            )
        ])

    # Кнопки навигации по датам (теперь после чтений)
    buttons.append(nav_buttons)

    # Кнопки для дополнительного контента (если сообщение было сокращено)
    if has_full_content:
        content_buttons = []
        content_buttons.append(
            InlineKeyboardButton(
                text="👼 Жития святых",
                callback_data=f"calendar_show_lives_{current_date.strftime('%Y_%m_%d')}"
            )
        )
        content_buttons.append(
            InlineKeyboardButton(
                text="🎵 Тропари",
                callback_data=f"calendar_show_tropars_{current_date.strftime('%Y_%m_%d')}"
            )
        )
        buttons.append(content_buttons)

    # Кнопка настроек календаря (только для админа)
    if show_settings and user_id and user_id == ADMIN_USER_ID:
        buttons.append([
            InlineKeyboardButton(
                text="⚙️ Настройки календаря",
                callback_data="calendar_settings"
            )
        ])

    # Кнопка возврата в главное меню
    buttons.append([
        InlineKeyboardButton(
            text="🏠 Главное меню",
            callback_data="back_to_main"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_calendar_settings_keyboard(current_settings: Dict[str, Any] = None) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру настроек календаря

    Args:
        current_settings: Текущие настройки календаря
    """
    if current_settings is None:
        current_settings = {
            'header': True,
            'lives': 4,
            'tropars': 0,  # 0 = отключено
            'scripture': 1,  # 1 = с заголовком
            'date_format': True
        }

    buttons = []

    # Заголовок
    buttons.append([
        InlineKeyboardButton(
            text="📅 Настройки православного календаря",
            callback_data="noop"
        )
    ])

    # Настройки отображения (boolean)
    boolean_settings = [
        ('header', 'Заголовок календаря', '✨'),
        ('date_format', 'Формат даты', '📆')
    ]

    for setting_key, setting_name, icon in boolean_settings:
        is_enabled = current_settings.get(setting_key, True)
        status = "✅" if is_enabled else "❌"

        buttons.append([
            InlineKeyboardButton(
                text=f"{icon} {setting_name}",
                callback_data="noop"
            ),
            InlineKeyboardButton(
                text=status,
                callback_data=f"calendar_setting_toggle_{setting_key}"
            )
        ])

    # Специальная настройка для тропарей (0, 1, 2)
    tropars_value = current_settings.get('tropars', 0)
    tropars_options = {
        0: "❌ Выкл",
        1: "✅ С заголовком",
        2: "📝 Без заголовка"
    }

    buttons.append([
        InlineKeyboardButton(
            text="🎵 Тропари",
            callback_data="noop"
        ),
        InlineKeyboardButton(
            text=tropars_options.get(tropars_value, f"❓ {tropars_value}"),
            callback_data=f"calendar_setting_tropars_next"
        )
    ])

    # Специальная настройка для Евангельских чтений (0, 1, 2)
    scripture_value = current_settings.get('scripture', 1)
    scripture_options = {
        0: "❌ Выкл",
        1: "✅ С заголовком",
        2: "📝 Без заголовка"
    }

    buttons.append([
        InlineKeyboardButton(
            text="📖 Евангельские чтения",
            callback_data="noop"
        ),
        InlineKeyboardButton(
            text=scripture_options.get(
                scripture_value, f"❓ {scripture_value}"),
            callback_data=f"calendar_setting_scripture_next"
        )
    ])

    # Специальная настройка для жития святых (integer)
    lives_value = current_settings.get('lives', 4)
    lives_options = {
        0: "❌ Выкл",
        1: "📋 Краткие",
        2: "📝 Подробные",
        3: "📚 Полные",
        4: "⭐ Основные",
        5: "🔍 Расширенные",
        6: "📖 Максимум"
    }

    buttons.append([
        InlineKeyboardButton(
            text="👼 Жития святых",
            callback_data="noop"
        ),
        InlineKeyboardButton(
            text=lives_options.get(lives_value, f"❓ {lives_value}"),
            callback_data=f"calendar_setting_lives_next"
        )
    ])

    # Кнопки управления
    buttons.append([
        InlineKeyboardButton(
            text="🔄 Сбросить настройки",
            callback_data="calendar_settings_reset"
        )
    ])

    buttons.append([
        InlineKeyboardButton(
            text="⬅️ Назад к календарю",
            callback_data="calendar_back"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_scripture_reading_keyboard(book_id: int, chapter: int,
                                      verse_start: int, verse_end: int,
                                      has_ai_enabled: bool = True) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для чтения Евангелия из календаря

    Args:
        book_id: ID книги
        chapter: Номер главы
        verse_start: Начальный стих
        verse_end: Конечный стих
        has_ai_enabled: Включена ли функция ИИ
    """
    buttons = []

    # Кнопка "Открыть полную главу"
    from utils.bible_data import bible_data
    book_abbr = None
    for abbr, b_id in bible_data.book_abbr_dict.items():
        if b_id == book_id:
            book_abbr = abbr
            break

    if book_abbr:
        buttons.append([
            InlineKeyboardButton(
                text="📖 Открыть полную главу",
                callback_data=f"open_chapter_{book_abbr}_{chapter}"
            )
        ])

    # Кнопка "Добавить в закладки"
    buttons.append([
        InlineKeyboardButton(
            text="🔖 Добавить в закладки",
            callback_data=f"add_bookmark_{book_id}_{chapter}_{verse_start}_{verse_end}"
        )
    ])

    # Кнопка "Разбор от ИИ" если включена
    if has_ai_enabled:
        from utils.bible_data import get_english_book_abbreviation
        en_book = get_english_book_abbreviation(book_id)
        if en_book:
            buttons.append([
                InlineKeyboardButton(
                    text="🤖 Разбор от ИИ",
                    callback_data=f"gpt_explain_{en_book}_{chapter}_{verse_start}"
                )
            ])

    # Кнопка возврата к календарю
    buttons.append([
        InlineKeyboardButton(
            text="⬅️ Назад к календарю",
            callback_data="calendar_back"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
