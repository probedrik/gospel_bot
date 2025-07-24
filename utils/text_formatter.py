"""
Утилиты для форматирования текста толкований
"""
import re
from typing import Optional


def format_commentary_text(text: str) -> str:
    """
    Форматирует текст толкования для корректного отображения в Telegram

    Заменяет markdown-разметку на HTML-теги, поддерживаемые Telegram
    """
    if not text:
        return ""

    # Убираем лишние пробелы и переносы строк
    text = text.strip()

    # Заменяем двойные звездочки на жирный текст
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)

    # Заменяем одинарные звездочки на курсив
    text = re.sub(r'\*([^*]+?)\*', r'<i>\1</i>', text)

    # Заменяем подчеркивания на подчеркнутый текст
    text = re.sub(r'__(.*?)__', r'<u>\1</u>', text)
    text = re.sub(r'_([^_]+?)_', r'<u>\1</u>', text)

    # Заменяем обратные кавычки на моноширинный текст
    text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)

    # Экранируем специальные HTML символы (кроме наших тегов)
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;').replace('>', '&gt;')

    # Восстанавливаем наши HTML теги
    text = text.replace('&lt;b&gt;', '<b>').replace('&lt;/b&gt;', '</b>')
    text = text.replace('&lt;i&gt;', '<i>').replace('&lt;/i&gt;', '</i>')
    text = text.replace('&lt;u&gt;', '<u>').replace('&lt;/u&gt;', '</u>')
    text = text.replace('&lt;code&gt;', '<code>').replace(
        '&lt;/code&gt;', '</code>')

    # Ограничиваем длину сообщения (максимум 4096 символов для Telegram)
    if len(text) > 4000:
        text = text[:3997] + "..."

    return text


def create_commentary_summary(text: str, max_length: int = 200) -> str:
    """
    Создает краткое резюме толкования для отображения в списках
    """
    if not text:
        return ""

    # Убираем HTML теги для резюме
    clean_text = re.sub(r'<[^>]+>', '', text)

    # Убираем лишние пробелы
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()

    if len(clean_text) <= max_length:
        return clean_text

    # Обрезаем по словам
    words = clean_text.split()
    summary = ""
    for word in words:
        if len(summary + word + " ") > max_length - 3:
            break
        summary += word + " "

    return summary.strip() + "..." if summary else clean_text[:max_length-3] + "..."


def get_reference_key(book_id: int, chapter: int, verse_start: Optional[int] = None,
                      verse_end: Optional[int] = None) -> str:
    """
    Создает уникальный ключ для ссылки на стих/главу
    """
    if verse_start is None:
        return f"{book_id}:{chapter}"
    elif verse_end is None or verse_start == verse_end:
        return f"{book_id}:{chapter}:{verse_start}"
    else:
        return f"{book_id}:{chapter}:{verse_start}-{verse_end}"


def format_reference_display(book_name: str, chapter: int, verse_start: Optional[int] = None,
                             verse_end: Optional[int] = None) -> str:
    """
    Создает отформатированную строку ссылки для отображения
    """
    if verse_start is None:
        return f"{book_name} {chapter}"
    elif verse_end is None or verse_start == verse_end:
        return f"{book_name} {chapter}:{verse_start}"
    else:
        return f"{book_name} {chapter}:{verse_start}-{verse_end}"
