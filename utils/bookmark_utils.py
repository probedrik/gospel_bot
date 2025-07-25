"""
Утилиты для работы с закладками
"""
from aiogram.types import InlineKeyboardButton
from typing import Optional


def create_bookmark_button(book_id: int, chapter_start: int, chapter_end: Optional[int] = None,
                          verse_start: Optional[int] = None, verse_end: Optional[int] = None,
                          is_bookmarked: bool = False) -> InlineKeyboardButton:
    """
    Создает кнопку для добавления/удаления закладки
    
    Args:
        book_id: ID книги
        chapter_start: Начальная глава
        chapter_end: Конечная глава (для диапазонов)
        verse_start: Начальный стих
        verse_end: Конечный стих
        is_bookmarked: Уже добавлено в закладки или нет
    
    Returns:
        InlineKeyboardButton: Кнопка закладки
    """
    if is_bookmarked:
        text = "🔖 Удалить из закладок"
        action = "remove"
    else:
        text = "📌 Сохранить в закладки"
        action = "add"
    
    # Формируем callback_data
    callback_parts = [f"bookmark_{action}", str(book_id), str(chapter_start)]
    
    if chapter_end and chapter_end != chapter_start:
        callback_parts.append(str(chapter_end))
    else:
        callback_parts.append("0")  # 0 означает отсутствие конечной главы
    
    if verse_start:
        callback_parts.append(str(verse_start))
    else:
        callback_parts.append("0")
    
    if verse_end and verse_end != verse_start:
        callback_parts.append(str(verse_end))
    else:
        callback_parts.append("0")
    
    callback_data = "_".join(callback_parts)
    
    return InlineKeyboardButton(text=text, callback_data=callback_data)


def parse_bookmark_callback(callback_data: str) -> dict:
    """
    Парсит callback_data кнопки закладки
    
    Args:
        callback_data: Строка callback_data
    
    Returns:
        dict: Распарсенные данные
    """
    parts = callback_data.split("_")
    
    if len(parts) < 6:
        return None
    
    try:
        action = parts[1]  # add или remove
        book_id = int(parts[2])
        chapter_start = int(parts[3])
        chapter_end = int(parts[4]) if parts[4] != "0" else None
        verse_start = int(parts[5]) if parts[5] != "0" else None
        verse_end = int(parts[6]) if len(parts) > 6 and parts[6] != "0" else None
        
        return {
            'action': action,
            'book_id': book_id,
            'chapter_start': chapter_start,
            'chapter_end': chapter_end,
            'verse_start': verse_start,
            'verse_end': verse_end
        }
    except (ValueError, IndexError):
        return None


def format_bookmark_reference(book_name: str, chapter_start: int, chapter_end: Optional[int] = None,
                             verse_start: Optional[int] = None, verse_end: Optional[int] = None) -> str:
    """
    Форматирует ссылку для отображения в закладке
    
    Args:
        book_name: Название книги
        chapter_start: Начальная глава
        chapter_end: Конечная глава
        verse_start: Начальный стих
        verse_end: Конечный стих
    
    Returns:
        str: Отформатированная ссылка
    """
    if chapter_end and chapter_end != chapter_start:
        # Диапазон глав
        return f"{book_name} {chapter_start}-{chapter_end}"
    elif verse_start and verse_end and verse_start != verse_end:
        # Диапазон стихов
        return f"{book_name} {chapter_start}:{verse_start}-{verse_end}"
    elif verse_start:
        # Один стих
        return f"{book_name} {chapter_start}:{verse_start}"
    else:
        # Вся глава
        return f"{book_name} {chapter_start}"