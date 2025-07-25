"""
Клавиатуры для работы с закладками
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict, Any


def create_bookmarks_menu_keyboard() -> InlineKeyboardMarkup:
    """Создает главное меню закладок"""
    buttons = [
        [
            InlineKeyboardButton(
                text="📖 Закладки Библии",
                callback_data="bookmarks_bible"
            )
        ],
        [
            InlineKeyboardButton(
                text="💬 Сохраненные разборы",
                callback_data="bookmarks_commentaries"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад в главное меню",
                callback_data="back_to_main"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_bookmarks_list_keyboard(bookmarks: List[Dict], page: int = 0, 
                                  bookmark_type: str = "bible", total_pages: int = 1) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру со списком закладок (максимум 16 на странице в 2 столбца)
    
    Args:
        bookmarks: Список закладок для отображения
        page: Текущая страница (начиная с 0)
        bookmark_type: Тип закладок ("bible" или "commentaries")
        total_pages: Общее количество страниц
    """
    buttons = []
    
    # Добавляем закладки по 2 в ряд (максимум 16 на странице = 8 рядов)
    for i in range(0, len(bookmarks), 2):
        row = []
        
        # Первая закладка в ряду
        bookmark1 = bookmarks[i]
        button1_text = format_bookmark_button_text(bookmark1, bookmark_type)
        button1_callback = f"open_bookmark_{bookmark_type}_{page * 16 + i}"
        row.append(InlineKeyboardButton(text=button1_text, callback_data=button1_callback))
        
        # Вторая закладка в ряду (если есть)
        if i + 1 < len(bookmarks):
            bookmark2 = bookmarks[i + 1]
            button2_text = format_bookmark_button_text(bookmark2, bookmark_type)
            button2_callback = f"open_bookmark_{bookmark_type}_{page * 16 + i + 1}"
            row.append(InlineKeyboardButton(text=button2_text, callback_data=button2_callback))
        
        buttons.append(row)
    
    # Добавляем навигацию по страницам
    if total_pages > 1:
        nav_row = []
        
        # Кнопка "Назад" (если не первая страница)
        if page > 0:
            nav_row.append(InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"bookmarks_page_{bookmark_type}_{page - 1}"
            ))
        
        # Показываем текущую страницу
        nav_row.append(InlineKeyboardButton(
            text=f"📄 {page + 1}/{total_pages}",
            callback_data="noop"
        ))
        
        # Кнопка "Далее" (если не последняя страница)
        if page < total_pages - 1:
            nav_row.append(InlineKeyboardButton(
                text="Далее ➡️",
                callback_data=f"bookmarks_page_{bookmark_type}_{page + 1}"
            ))
        
        buttons.append(nav_row)
    
    # Кнопка возврата в меню закладок
    buttons.append([
        InlineKeyboardButton(
            text="⬅️ К типам закладок",
            callback_data="bookmarks_menu"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def format_bookmark_button_text(bookmark: Dict, bookmark_type: str) -> str:
    """
    Форматирует текст кнопки закладки
    
    Args:
        bookmark: Данные закладки
        bookmark_type: Тип закладки ("bible" или "commentaries")
    """
    if bookmark_type == "bible":
        # Для библейских закладок: "Книга Глава:Стих"
        book_name = bookmark.get('book_name', 'Неизвестно')
        chapter_start = bookmark.get('chapter_start')
        chapter_end = bookmark.get('chapter_end')
        verse_start = bookmark.get('verse_start')
        verse_end = bookmark.get('verse_end')
        
        # Формируем текст ссылки
        if chapter_end and chapter_end != chapter_start:
            # Диапазон глав
            reference = f"{book_name} {chapter_start}-{chapter_end}"
        elif verse_start and verse_end and verse_start != verse_end:
            # Диапазон стихов
            reference = f"{book_name} {chapter_start}:{verse_start}-{verse_end}"
        elif verse_start:
            # Один стих
            reference = f"{book_name} {chapter_start}:{verse_start}"
        else:
            # Вся глава
            reference = f"{book_name} {chapter_start}"
        
        return reference
    
    elif bookmark_type == "commentaries":
        # Для сохраненных разборов: "Книга Глава:Стих (тип)"
        reference = bookmark.get('reference_text', 'Неизвестно')
        commentary_type = bookmark.get('commentary_type', 'ai')
        type_icon = "🤖" if commentary_type == "ai" else "📝"
        
        return f"{type_icon} {reference}"
    
    return "Неизвестная закладка"


def create_bookmark_action_keyboard(bookmark_index: int, bookmark_type: str, page: int = 0) -> InlineKeyboardMarkup:
    """Создает клавиатуру с действиями для конкретной закладки"""
    buttons = [
        [
            InlineKeyboardButton(
                text="🗑️ Удалить закладку",
                callback_data=f"delete_bookmark_{bookmark_type}_{bookmark_index}"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ К списку закладок",
                callback_data=f"bookmarks_page_{bookmark_type}_{page}"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)