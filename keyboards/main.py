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
            KeyboardButton(text="📅 Планы чтения"),
            KeyboardButton(text="📝 Мои закладки"),
        ],
        [
            KeyboardButton(text="📚 Темы"),
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
    # Количество книг на одной странице
    books_per_page = 10

    # Получаем список книг для текущей страницы
    book_ids = bible_data.book_values
    book_names = bible_data.book_names

    # Формируем пары (id, name) для страницы
    total_books = len(book_ids)
    start_idx = page * books_per_page
    end_idx = min(start_idx + books_per_page, total_books)

    buttons = []

    # Добавляем кнопки для книг
    for i in range(start_idx, end_idx):
        book_id = book_ids[i]
        book_name = book_names[i]
        buttons.append([
            InlineKeyboardButton(
                text=book_name,
                callback_data=f"select_book_{book_id}"
            )
        ])

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


def create_navigation_keyboard(has_previous: bool = False, has_next: bool = True, is_bookmarked: bool = False) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для навигации по главам.

    Args:
        has_previous: Есть ли предыдущая глава
        has_next: Есть ли следующая глава
        is_bookmarked: Добавлена ли глава в закладки

    Returns:
        Клавиатура с кнопками навигации
    """
    logger = logging.getLogger(__name__)
    logger.info(
        f"Создание клавиатуры навигации: has_previous={has_previous}, has_next={has_next}, is_bookmarked={is_bookmarked}")

    buttons = []

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

    if navigation_buttons:
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
        # Если это список кортежей из БД
        if bookmarks and isinstance(bookmarks, list) and isinstance(bookmarks[0], tuple):
            logger.info("Обработка закладок из БД")
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
    """Создает клавиатуру для выбора планов чтения"""
    from services.reading_plans import reading_plans_service

    buttons = []

    # Получаем все доступные планы
    plans = reading_plans_service.get_all_plans()

    for plan in plans:
        buttons.append([
            InlineKeyboardButton(
                text=f"📅 {plan.title} ({plan.total_days} дней)",
                callback_data=f"select_plan_{plan.plan_id}"
            )
        ])

    # Кнопка для просмотра активных планов пользователя
    buttons.append([
        InlineKeyboardButton(
            text="📋 Мои активные планы",
            callback_data="my_reading_plans"
        )
    ])

    # Возврат в меню
    buttons.append([
        InlineKeyboardButton(
            text="🏠 Вернуться в меню",
            callback_data="back_to_menu"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_plan_day_keyboard(plan_id: str, day: int, is_completed: bool = False,
                             has_previous: bool = False, has_next: bool = False,
                             references: list = None) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для дня плана чтения

    Args:
        plan_id: ID плана чтения
        day: номер дня
        is_completed: отмечен ли день как прочитанный
        has_previous: есть ли предыдущий день
        has_next: есть ли следующий день
        references: список отрывков для чтения
    """
    buttons = []

    # Кнопки для отрывков чтения
    if references:
        for i, ref in enumerate(references):
            # Ограничиваем длину текста кнопки
            button_text = ref if len(ref) <= 30 else ref[:27] + "..."
            buttons.append([
                InlineKeyboardButton(
                    text=f"📖 {i+1}. {button_text}",
                    callback_data=f"reading_ref_{plan_id}_{day}_{i}"
                )
            ])

    # Кнопки навигации по дням
    nav_buttons = []
    if has_previous:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Предыдущий день",
                callback_data=f"plan_day_{plan_id}_{day-1}"
            )
        )

    if has_next:
        nav_buttons.append(
            InlineKeyboardButton(
                text="➡️ Следующий день",
                callback_data=f"plan_day_{plan_id}_{day+1}"
            )
        )

    if nav_buttons:
        buttons.append(nav_buttons)

    # Кнопка отметки как прочитанного
    if is_completed:
        buttons.append([
            InlineKeyboardButton(
                text="✅ Прочитано",
                callback_data=f"unmark_day_{plan_id}_{day}"
            )
        ])
    else:
        buttons.append([
            InlineKeyboardButton(
                text="📖 Отметить как прочитанное",
                callback_data=f"mark_day_{plan_id}_{day}"
            )
        ])

    # Кнопка возврата к плану
    buttons.append([
        InlineKeyboardButton(
            text="📋 Вернуться к плану",
            callback_data=f"view_plan_{plan_id}"
        )
    ])

    # Возврат в меню планов
    buttons.append([
        InlineKeyboardButton(
            text="📅 Планы чтения",
            callback_data="reading_plans"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_plan_overview_keyboard(plan_id: str, current_day: int = 1) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для обзора плана чтения

    Args:
        plan_id: ID плана чтения
        current_day: текущий день плана
    """
    buttons = []

    # Кнопка текущего дня
    buttons.append([
        InlineKeyboardButton(
            text=f"📖 День {current_day} (текущий)",
            callback_data=f"plan_day_{plan_id}_{current_day}"
        )
    ])

    # Кнопка прогресса
    buttons.append([
        InlineKeyboardButton(
            text="📊 Показать прогресс",
            callback_data=f"plan_progress_{plan_id}"
        )
    ])

    # Кнопка выбора дня
    buttons.append([
        InlineKeyboardButton(
            text="📅 Выбрать день",
            callback_data=f"plan_select_day_{plan_id}"
        )
    ])

    # Кнопка очистки прогресса
    buttons.append([
        InlineKeyboardButton(
            text="🗑️ Очистить прогресс",
            callback_data=f"clear_progress_{plan_id}"
        )
    ])

    # Возврат к планам
    buttons.append([
        InlineKeyboardButton(
            text="📅 Планы чтения",
            callback_data="reading_plans"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_user_plans_keyboard(user_plans) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру с активными планами пользователя

    Args:
        user_plans: список планов пользователя
    """
    from services.reading_plans import reading_plans_service

    buttons = []

    if user_plans:
        for user_plan in user_plans:
            plan_id = user_plan['plan_id']
            current_day = user_plan['current_day']

            # Получаем информацию о плане
            plan = reading_plans_service.get_plan(plan_id)
            if plan:
                buttons.append([
                    InlineKeyboardButton(
                        text=f"📋 {plan.title} (день {current_day}/{plan.total_days})",
                        callback_data=f"view_plan_{plan_id}"
                    )
                ])
    else:
        buttons.append([
            InlineKeyboardButton(
                text="Нет активных планов",
                callback_data="reading_plans"
            )
        ])

    # Кнопка добавления нового плана
    buttons.append([
        InlineKeyboardButton(
            text="➕ Добавить план",
            callback_data="reading_plans"
        )
    ])

    # Возврат в меню
    buttons.append([
        InlineKeyboardButton(
            text="🏠 Вернуться в меню",
            callback_data="back_to_menu"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_reading_navigation_keyboard(references: list, current_ref: int = 0,
                                       plan_id: str = None, day: int = None,
                                       is_bookmarked: bool = False) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для навигации по чтениям дня плана

    Args:
        references: список ссылок для чтения
        current_ref: индекс текущей ссылки
        plan_id: ID плана чтения
        day: номер дня
        is_bookmarked: добавлена ли текущая ссылка в закладки
    """
    buttons = []

    # Навигация по ссылкам дня
    if len(references) > 1:
        nav_buttons = []

        if current_ref > 0:
            nav_buttons.append(
                InlineKeyboardButton(
                    text="⬅️ Предыдущее чтение",
                    callback_data=f"reading_ref_{plan_id}_{day}_{current_ref-1}"
                )
            )

        if current_ref < len(references) - 1:
            nav_buttons.append(
                InlineKeyboardButton(
                    text="➡️ Следующее чтение",
                    callback_data=f"reading_ref_{plan_id}_{day}_{current_ref+1}"
                )
            )

        if nav_buttons:
            buttons.append(nav_buttons)

    # Кнопки для толкований и разборов (как в обычном поиске)
    buttons.append([
        InlineKeyboardButton(
            text="📝 Толкование Лопухина",
            callback_data=f"lopukhin_reading_{plan_id}_{day}_{current_ref}"
        )
    ])

    buttons.append([
        InlineKeyboardButton(
            text="🤖 ИИ-разбор",
            callback_data=f"ai_reading_{plan_id}_{day}_{current_ref}"
        )
    ])

    # Кнопка закладки
    bookmark_text = "🗑️ Удалить закладку" if is_bookmarked else "📌 Добавить закладку"
    bookmark_data = f"remove_bookmark_reading_{plan_id}_{day}_{current_ref}" if is_bookmarked else f"add_bookmark_reading_{plan_id}_{day}_{current_ref}"

    buttons.append([
        InlineKeyboardButton(
            text=bookmark_text,
            callback_data=bookmark_data
        )
    ])

    # Возврат к дню плана
    if plan_id and day:
        buttons.append([
            InlineKeyboardButton(
                text="📅 Вернуться к дню",
                callback_data=f"plan_day_{plan_id}_{day}"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
