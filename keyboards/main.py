"""
Основные клавиатуры для пользовательского интерфейса бота.
"""
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
import logging

from utils.bible_data import bible_data
from config.settings import ENABLE_WORD_SEARCH


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Создает и возвращает основную клавиатуру бота"""
    buttons = [
        [
            KeyboardButton(text="📖 Выбрать книгу"),
            KeyboardButton(text="🔍 Найти стих"),
        ],
        [
            KeyboardButton(text="📚 План чтения"),
            KeyboardButton(text="📝 Мои закладки"),
        ],
        [
            KeyboardButton(text="🎯 Темы"),
            KeyboardButton(text="❓ Помощь"),
        ]
    ]

    # Добавляем кнопку поиска по слову только если функция включена
    if ENABLE_WORD_SEARCH:
        buttons.append([
            KeyboardButton(text="🔍 Поиск по слову"),
        ])

    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )


def create_book_keyboard(page: int = 0) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру с книгами Библии, разделенную на страницы

    Args:
        page: номер страницы (начиная с 0)
    """
    # Количество книг на одной странице (увеличиваем для трех столбцов)
    books_per_page = 15  # 5 рядов по 3 книги

    # Получаем список книг для текущей страницы
    book_ids = bible_data.book_values
    book_names = bible_data.book_names

    # Формируем пары (id, name) для страницы
    total_books = len(book_ids)
    start_idx = page * books_per_page
    end_idx = min(start_idx + books_per_page, total_books)

    buttons = []

    # Добавляем кнопки для книг по 3 в ряд
    row = []
    for i in range(start_idx, end_idx):
        book_id = book_ids[i]
        book_name = book_names[i]
        row.append(
            InlineKeyboardButton(
                text=book_name,
                callback_data=f"select_book_{book_id}"
            )
        )

        # Если набрали 3 кнопки в ряд, добавляем ряд и начинаем новый
        if len(row) == 3:
            buttons.append(row)
            row = []

    # Добавляем оставшиеся кнопки, если есть
    if row:
        buttons.append(row)

    # Добавляем навигационные кнопки
    nav_buttons = []

    # Кнопка предыдущей страницы
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"nav_page_{page-1}"
            )
        )

    # Кнопка следующей страницы
    if end_idx < total_books:
        nav_buttons.append(
            InlineKeyboardButton(
                text="Вперед ➡️",
                callback_data=f"nav_page_{page+1}"
            )
        )

    if nav_buttons:
        buttons.append(nav_buttons)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_navigation_keyboard(has_previous: bool = False, has_next: bool = True, is_bookmarked: bool = False, extra_buttons: list = None) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для навигации по главам.

    Args:
        has_previous: Есть ли предыдущая глава
        has_next: Есть ли следующая глава
        is_bookmarked: Добавлена ли глава в закладки
        extra_buttons: Дополнительные кнопки для добавления

    Returns:
        Клавиатура с кнопками навигации
    """
    logger = logging.getLogger(__name__)
    logger.info(
        f"Создание клавиатуры навигации: has_previous={has_previous}, has_next={has_next}, is_bookmarked={is_bookmarked}")

    buttons = []

    # Добавляем дополнительные кнопки (толкование, ИИ) в начале
    if extra_buttons:
        buttons.extend(extra_buttons)

    # Добавляем кнопки навигации
    navigation_buttons = []

    if has_previous:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Предыдущая глава",
                                 callback_data="prev_chapter")
        )

    if has_next:
        navigation_buttons.append(
            InlineKeyboardButton(text="➡️ Следующая глава",
                                 callback_data="next_chapter")
        )

    # Если есть кнопки навигации, добавляем их
    if navigation_buttons:
        # Если только одна кнопка - она занимает всю ширину
        # Если две кнопки - они делят ширину пополам
        if len(navigation_buttons) == 1:
            buttons.append([navigation_buttons[0]])
        else:
            buttons.append(navigation_buttons)

    # Кнопка для добавления/удаления закладок
    bookmark_data = "bookmark_info" if is_bookmarked else "add_bookmark"
    bookmark_text = "🗑️ Удалить закладку" if is_bookmarked else "📌 Добавить закладку"

    logger.info(f"Добавлена кнопка '{bookmark_text}' в клавиатуру навигации")

    buttons.append([
        InlineKeyboardButton(text=bookmark_text, callback_data=bookmark_data)
    ])

    # Возврат в меню
    buttons.append([
        InlineKeyboardButton(
            text="🏠 Вернуться в меню",
            callback_data="back_to_menu"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_translations_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для выбора перевода Библии"""
    buttons = [
        [
            InlineKeyboardButton(
                text="Синодальный перевод",
                callback_data="translation_rst"
            )
        ],
        [
            InlineKeyboardButton(
                text="Современный перевод РБО",
                callback_data="translation_rbo"
            )
        ],
        [
            InlineKeyboardButton(
                text="🏠 Вернуться в меню",
                callback_data="back_to_menu"
            )
        ]
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_bookmarks_keyboard(bookmarks) -> InlineKeyboardMarkup:
    """Создает клавиатуру с закладками пользователя

    Args:
        bookmarks: список закладок в формате [(book_id, chapter, display_text), ...] 
                   или в формате словаря если из FSM
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Создание клавиатуры закладок, получено: {bookmarks}")

    buttons = []

    # Добавляем кнопки для закладок
    try:
        # Если это список кортежей из БД (SQLite)
        if bookmarks and isinstance(bookmarks, list) and len(bookmarks) > 0 and isinstance(bookmarks[0], tuple):
            logger.info("Обработка закладок из БД (SQLite - кортежи)")
            for bookmark in bookmarks:
                if len(bookmark) >= 3:  # Проверяем, что в кортеже достаточно элементов
                    book_id, chapter, display_text = bookmark[0], bookmark[1], bookmark[2]
                    # Проверяем, что текст является строкой
                    if not isinstance(display_text, str):
                        from utils.bible_data import bible_data
                        book_name = bible_data.get_book_name(book_id)
                        display_text = f"{book_name} {chapter}"
                        logger.warning(
                            f"Преобразован некорректный формат display_text: {bookmark[2]} -> {display_text}")

                    buttons.append([
                        InlineKeyboardButton(
                            text=display_text,
                            callback_data=f"bookmark_{book_id}_{chapter}"
                        )
                    ])
        # Если это список словарей из БД (Supabase/PostgreSQL)
        elif bookmarks and isinstance(bookmarks, list) and len(bookmarks) > 0 and isinstance(bookmarks[0], dict):
            logger.info(
                "Обработка закладок из БД (Supabase/PostgreSQL - словари)")
            for bookmark in bookmarks:
                book_id = bookmark.get('book_id')
                chapter = bookmark.get('chapter')
                display_text = bookmark.get('display_text')

                # Проверяем, что есть необходимые поля
                if book_id is not None and chapter is not None:
                    # Проверяем, что текст является строкой
                    if not isinstance(display_text, str) or not display_text:
                        from utils.bible_data import bible_data
                        book_name = bible_data.get_book_name(book_id)
                        display_text = f"{book_name} {chapter}"
                        logger.warning(
                            f"Создан display_text для закладки: {display_text}")

                    buttons.append([
                        InlineKeyboardButton(
                            text=display_text,
                            callback_data=f"bookmark_{book_id}_{chapter}"
                        )
                    ])
        # Если это словарь из FSM
        elif bookmarks and isinstance(bookmarks, dict):
            logger.info("Обработка закладок из State (словарь)")
            for key, data in bookmarks.items():
                if isinstance(data, dict) and 'book_id' in data and 'chapter' in data:
                    book_id = data['book_id']
                    chapter = data['chapter']

                    # Проверяем наличие display_text, если нет - создаем
                    if 'display_text' in data and isinstance(data['display_text'], str):
                        display_text = data['display_text']
                    else:
                        # Если display_text отсутствует или это не строка, генерируем его
                        from utils.bible_data import bible_data
                        book_name = bible_data.get_book_name(book_id)
                        display_text = f"{book_name} {chapter}"
                        logger.warning(
                            f"Сгенерирован display_text для закладки: {display_text}")

                    buttons.append([
                        InlineKeyboardButton(
                            text=display_text,
                            callback_data=f"bookmark_{book_id}_{chapter}"
                        )
                    ])
    except Exception as e:
        logger.error(f"Ошибка при обработке закладок: {e}", exc_info=True)
        # В случае ошибки добавим кнопку с предупреждением
        buttons.append([
            InlineKeyboardButton(
                text="⚠️ Ошибка обработки закладок",
                callback_data="back_to_menu"
            )
        ])

    # Если список закладок пуст, добавим информационное сообщение
    if not buttons:
        buttons.append([
            InlineKeyboardButton(
                text="Нет сохраненных закладок",
                callback_data="back_to_menu"
            )
        ])
    else:
        # Добавляем кнопку очистки всех закладок
        buttons.append([
            InlineKeyboardButton(
                text="🗑 Очистить все закладки",
                callback_data="clear_bookmarks"
            )
        ])

    # Добавляем кнопку возврата в меню
    buttons.append([
        InlineKeyboardButton(
            text="🏠 Вернуться в меню",
            callback_data="back_to_menu"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_reading_plans_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру с планами чтения"""
    buttons = [
        [
            InlineKeyboardButton(
                text="📖 Евангелие на каждый день",
                callback_data="select_plan_gospel_daily"
            )
        ],
        [
            InlineKeyboardButton(
                text="📚 Классический план за 1 год",
                callback_data="select_plan_classic_year"
            )
        ],
        [
            InlineKeyboardButton(
                text="📜 План ВЗ и НЗ",
                callback_data="select_plan_ot_nt_plan"
            )
        ],
        [
            InlineKeyboardButton(
                text="📋 Мои планы",
                callback_data="my_reading_plans"
            )
        ],
        [
            InlineKeyboardButton(
                text="🏠 Вернуться в меню",
                callback_data="back_to_menu"
            )
        ]
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_plan_overview_keyboard(plan_id: str, current_day: int) -> InlineKeyboardMarkup:
    """Создает клавиатуру для просмотра конкретного плана"""
    buttons = [
        [
            InlineKeyboardButton(
                text=f"📖 Читать день {current_day}",
                callback_data=f"plan_day_{plan_id}_{current_day}"
            )
        ],
        [
            InlineKeyboardButton(
                text="📊 Показать прогресс",
                callback_data=f"plan_progress_{plan_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="📅 Выбрать день",
                callback_data=f"plan_select_day_{plan_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🗑 Очистить прогресс",
                callback_data=f"clear_progress_{plan_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад к планам",
                callback_data="reading_plans"
            )
        ]
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_plan_day_keyboard(plan_id: str, day: int, has_previous: bool = False, has_next: bool = False, is_completed: bool = False) -> InlineKeyboardMarkup:
    """Создает клавиатуру для конкретного дня плана"""
    buttons = []

    # Навигация по дням
    nav_buttons = []
    if has_previous:
        prev_day = day - 1
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Предыдущий день",
                callback_data=f"plan_day_{plan_id}_{prev_day}"
            )
        )

    if has_next:
        next_day = day + 1
        nav_buttons.append(
            InlineKeyboardButton(
                text="➡️ Следующий день",
                callback_data=f"plan_day_{plan_id}_{next_day}"
            )
        )

    if nav_buttons:
        buttons.append(nav_buttons)

    # Кнопка отметки о прочтении
    if is_completed:
        buttons.append([
            InlineKeyboardButton(
                text="✅ Отметить как непрочитанное",
                callback_data=f"unmark_day_{plan_id}_{day}"
            )
        ])
    else:
        buttons.append([
            InlineKeyboardButton(
                text="✅ Отметить как прочитанное",
                callback_data=f"mark_day_{plan_id}_{day}"
            )
        ])

    # Кнопка возврата к плану
    buttons.append([
        InlineKeyboardButton(
            text="⬅️ Вернуться к плану",
            callback_data=f"view_plan_{plan_id}"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_user_plans_keyboard(user_plans) -> InlineKeyboardMarkup:
    """Создает клавиатуру с планами пользователя"""
    buttons = []

    # Добавляем кнопки для планов пользователя
    if user_plans:
        for plan in user_plans:
            # Предполагаем, что plan это словарь с plan_id и другими данными
            plan_id = plan.get('plan_id') if isinstance(
                plan, dict) else plan[0]

            # Получаем название плана
            plan_name = "План чтения"
            if plan_id == "gospel_daily":
                plan_name = "📖 Евангелие на каждый день"
            elif plan_id == "classic_year":
                plan_name = "📚 Классический план за 1 год"
            elif plan_id == "ot_nt_plan":
                plan_name = "📜 План ВЗ и НЗ"

            buttons.append([
                InlineKeyboardButton(
                    text=plan_name,
                    callback_data=f"view_plan_{plan_id}"
                )
            ])

    # Кнопка возврата
    buttons.append([
        InlineKeyboardButton(
            text="⬅️ Назад к планам",
            callback_data="reading_plans"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_reading_navigation_keyboard(plan_id: str, day: int, has_previous: bool = False, has_next: bool = False, is_bookmarked: bool = False) -> InlineKeyboardMarkup:
    """Создает клавиатуру для навигации по чтению"""
    buttons = []

    # Навигация по дням
    nav_buttons = []
    if has_previous:
        prev_day = day - 1
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Предыдущий",
                callback_data=f"plan_day_{plan_id}_{prev_day}"
            )
        )

    if has_next:
        next_day = day + 1
        nav_buttons.append(
            InlineKeyboardButton(
                text="➡️ Следующий",
                callback_data=f"plan_day_{plan_id}_{next_day}"
            )
        )

    if nav_buttons:
        buttons.append(nav_buttons)

    # Кнопка закладки
    if is_bookmarked:
        buttons.append([
            InlineKeyboardButton(
                text="🗑️ Удалить закладку",
                callback_data=f"remove_bookmark_reading_{plan_id}_{day}"
            )
        ])
    else:
        buttons.append([
            InlineKeyboardButton(
                text="📌 Добавить закладку",
                callback_data=f"add_bookmark_reading_{plan_id}_{day}"
            )
        ])

    # Кнопка возврата
    buttons.append([
        InlineKeyboardButton(
            text="⬅️ Вернуться к дню",
            callback_data=f"plan_day_{plan_id}_{day}"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
