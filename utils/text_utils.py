"""
Утилиты для работы с текстом.
"""
from config.settings import MESS_MAX_LENGTH


def split_text(text: str, max_length: int = MESS_MAX_LENGTH) -> list[str]:
    """
    Разбивает длинный текст на части, не превышающие максимальную длину.
    Старается сохранить целостность абзацев.

    Args:
        text: Исходный текст для разбивки
        max_length: Максимальная длина одной части

    Returns:
        Список строк, разбитых по максимальной длине
    """
    if len(text) <= max_length:
        return [text]

    parts = []
    while len(text) > 0:
        # Ищем последний перенос строки в допустимом диапазоне
        split_position = text.rfind('\n', 0, max_length)

        # Если не нашли перенос - ищем последний пробел
        if split_position == -1:
            split_position = text.rfind(' ', 0, max_length)

        # Если совсем не нашли подходящего места - форсированно обрезаем
        if split_position == -1:
            split_position = max_length

        part = text[:split_position].strip()
        if part:
            parts.append(part)
        text = text[split_position:].strip()

    return parts
