"""
Утилиты для работы с текстом.
"""
from config.settings import MESS_MAX_LENGTH


def split_text(text: str, max_length: int = MESS_MAX_LENGTH) -> list[str]:
    """
    Разбивает длинный текст на части, не превышающие максимальную длину.
    Старается сохранить целостность абзацев, избегать очень маленьких кусков в конце
    и корректно обрабатывать HTML теги (особенно blockquote).

    Args:
        text: Исходный текст для разбивки
        max_length: Максимальная длина одной части

    Returns:
        Список строк, разбитых по максимальной длине
    """
    if len(text) <= max_length:
        return [text]

    parts = []
    # Минимальная длина части (чтобы избежать маленьких кусков)
    min_part_length = 200

    iteration_count = 0
    max_iterations = 50  # Защита от бесконечного цикла

    while len(text) > 0 and iteration_count < max_iterations:
        iteration_count += 1

        if len(text) <= max_length:
            # Если остался небольшой кусок, проверяем можно ли его объединить с предыдущей частью
            if parts and len(text) < min_part_length and len(parts[-1]) + len(text) + 10 <= max_length:
                # Объединяем с предыдущей частью
                parts[-1] = parts[-1] + "\n\n" + text
                break
            else:
                # Добавляем как отдельную часть
                parts.append(text.strip())
                break

        # Ищем последний перенос строки в допустимом диапазоне
        split_position = text.rfind('\n', 0, max_length)

        # Если не нашли перенос - ищем последний пробел
        if split_position == -1:
            split_position = text.rfind(' ', 0, max_length)

        # Если совсем не нашли подходящего места - форсированно обрезаем
        if split_position == -1:
            split_position = max_length

        # Проверяем, не разрывается ли HTML тег на месте разделения
        part = text[:split_position].strip()

        # Проверяем баланс HTML тегов в этой части
        if part and _has_unbalanced_html_tags(part):
            # Если HTML теги не сбалансированы, пытаемся найти лучшее место для разделения
            better_split = _find_safe_split_position(
                text, split_position, max_length)
            if better_split != split_position and better_split > 0:
                split_position = better_split

            # ВСЕГДА обновляем part после поиска позиции
            part = text[:split_position].strip()

        # ВСЕГДА проверяем баланс тегов после всех попыток найти лучшую позицию
        if part and _has_unbalanced_html_tags(part):
            # Подсчитываем открытые blockquote теги
            open_blockquotes = part.count(
                '<blockquote>') - part.count('</blockquote>')
            if open_blockquotes > 0:
                # Добавляем закрывающие теги
                part += '</blockquote>' * open_blockquotes

        if part:
            parts.append(part)

        # Убеждаемся, что мы продвигаемся вперед
        remaining_text = text[split_position:].strip()
        if remaining_text == text.strip():
            # Если текст не изменился, принудительно отрезаем хотя бы один символ
            remaining_text = text[1:].strip() if len(text) > 1 else ""

        # Если мы принудительно закрыли blockquote теги в предыдущей части,
        # нужно открыть их в следующей части
        if remaining_text and part and part.endswith('</blockquote>') and remaining_text.count('<blockquote>') < remaining_text.count('</blockquote>'):
            # Подсчитываем сколько blockquote тегов нужно открыть
            missing_opens = remaining_text.count(
                '</blockquote>') - remaining_text.count('<blockquote>')
            if missing_opens > 0:
                remaining_text = '<blockquote>' * missing_opens + remaining_text

        text = remaining_text

    # Если достигли лимита итераций, добавляем оставшийся текст
    if iteration_count >= max_iterations and text:
        parts.append(text.strip())

    return parts


def _has_unbalanced_html_tags(text: str) -> bool:
    """
    Проверяет, есть ли несбалансированные HTML теги в тексте.
    Особое внимание уделяется тегам blockquote, b, i, u, code.
    """
    import re

    # Важные теги которые должны быть сбалансированы
    important_tags = ['blockquote', 'b', 'i', 'u', 'code', 'pre', 'a']

    for tag in important_tags:
        # Считаем открывающие и закрывающие теги
        open_count = len(re.findall(f'<{tag}[^>]*>', text, re.IGNORECASE))
        close_count = len(re.findall(f'</{tag}>', text, re.IGNORECASE))

        if open_count != close_count:
            return True

    return False


def _find_safe_split_position(text: str, current_split: int, max_length: int) -> int:
    """
    Находит безопасную позицию для разделения текста, избегая разрыва HTML тегов.
    """
    import re

    # СПЕЦИАЛЬНЫЙ СЛУЧАЙ: если весь текст обернут в один <blockquote>
    # и нет способа разделить без нарушения баланса, то разделяем внутри blockquote
    # и добавляем закрывающий/открывающий теги

    # Ищем позицию для разделения на границах слов/переносов строк
    best_pos = current_split

    # Сначала ищем назад
    for pos in range(current_split, max(0, current_split - 500), -1):
        if pos == 0 or text[pos] in [' ', '\n', '.', '!', '?']:
            if pos > 100:  # Минимальная длина части
                best_pos = pos
                return best_pos

    # Если не нашли назад, ищем вперед (но не больше max_length)
    for pos in range(current_split, min(len(text), max_length)):
        if text[pos] in [' ', '\n', '.', '!', '?']:
            best_pos = pos
            return best_pos

    # В крайнем случае возвращаем оригинальную позицию
    return current_split


def format_chapter_with_verses(chapter_data: dict, format_mode: str = "HTML") -> str:
    """
    Форматирует главу с номерами стихов (каждый стих с новой строки).

    Args:
        chapter_data: Словарь с данными главы из JSON файла
        format_mode: Режим форматирования (HTML, Markdown, MarkdownV2)

    Returns:
        Отформатированный текст с номерами стихов
    """
    if not chapter_data or 'verses' not in chapter_data:
        return "Ошибка: некорректные данные главы"

    verses = chapter_data['verses']
    book_name = chapter_data.get('book', 'Неизвестная книга')
    chapter_num = chapter_data.get('chapter', 1)

    # Получаем функции форматирования
    format_functions = get_verse_format_functions(chapter_num)

    # Форматируем заголовок и номера стихов в зависимости от режима
    if format_mode.upper() == "HTML":
        title = f"<b>{book_name}, глава {chapter_num}</b>"
        verse_format = format_functions["HTML"]
    elif format_mode.upper() == "MARKDOWN":
        title = f"**{book_name}, глава {chapter_num}**"
        verse_format = format_functions["MARKDOWN"]
    elif format_mode.upper() == "MARKDOWNV2":
        # Экранируем спецсимволы для MarkdownV2
        def escape_md(s):
            s = s.replace('\\', '\\\\')
            chars = r'_ * [ ] ( ) ~ ` > # + - = | { } . !'
            for c in chars.split():
                s = s.replace(c, f'\\{c}')
            return s

        escaped_book = escape_md(book_name)
        title = f"*{escaped_book}, глава {chapter_num}*"
        verse_format = format_functions["MARKDOWNV2"]
    else:
        # Обычный текст без форматирования
        title = f"{book_name}, глава {chapter_num}"
        verse_format = format_functions["PLAIN"]

    # Формируем результат
    result = f"{title}\n\n"

    # Добавляем стихи с номерами
    for verse_num, verse_text in verses.items():
        result += f"{verse_format(verse_num, verse_text)}\n\n"

    return result.strip()


def get_verses_parse_mode() -> str:
    """
    Определяет режим парсинга для сообщений с номерами стихов.

    Returns:
        Режим парсинга для aiogram (HTML, Markdown, MarkdownV2 или None)
    """
    from config.settings import ENABLE_VERSE_NUMBERS, BIBLE_MARKDOWN_ENABLED, BIBLE_MARKDOWN_MODE, BIBLE_QUOTE_ENABLED

    if not ENABLE_VERSE_NUMBERS:
        return None

    # Если включен режим цитат, принудительно используем HTML
    if BIBLE_QUOTE_ENABLED:
        return "HTML"

    if BIBLE_MARKDOWN_ENABLED:
        return BIBLE_MARKDOWN_MODE
    else:
        return "HTML"  # По умолчанию используем HTML если markdown отключен


def get_commentary_parse_mode() -> str:
    """
    Определяет режим парсинга для толкований и ИИ-ответов.

    Returns:
        Режим парсинга для aiogram (HTML, Markdown, MarkdownV2 или None)
    """
    from config.settings import COMMENTARY_MARKDOWN_ENABLED, COMMENTARY_MARKDOWN_MODE

    if COMMENTARY_MARKDOWN_ENABLED:
        return COMMENTARY_MARKDOWN_MODE
    else:
        return "HTML"  # По умолчанию используем HTML


def format_as_quote(text: str) -> str:
    """
    Форматирует текст как цитату, используя HTML-тег <blockquote> для визуального отображения.

    Args:
        text: Исходный текст

    Returns:
        Текст, отформатированный как цитата
    """
    if not text:
        return text

    # Используем HTML-тег blockquote для создания настоящей визуальной цитаты
    import html
    import re

    # СНАЧАЛА очищаем от HTML тегов
    cleaned_text = re.sub(r'<[^>]*>', '', text)  # Удаляем все HTML теги

    # ЗАТЕМ очищаем от markdown символов
    # **жирный** → жирный
    cleaned_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned_text)
    cleaned_text = re.sub(r'\*([^*]+)\*', r'\1',
                          cleaned_text)  # *курсив* → курсив
    cleaned_text = re.sub(r'`([^`]+)`', r'\1', cleaned_text)  # `код` → код

    cleaned_text = cleaned_text.strip()
    escaped_text = html.escape(cleaned_text)
    return f"<blockquote>{escaped_text}</blockquote>"


def get_verse_format_functions(chapter_num=None):
    """
    Возвращает функции форматирования номеров стихов для разных режимов.
    Использует настройки BIBLE_VERSE_NUMBER_SPACING, BIBLE_INCLUDE_CHAPTER_NUMBER и BIBLE_VERSE_NUMBER_STYLE.

    Args:
        chapter_num: Номер главы (для формата "глава:стих")

    Returns:
        Словарь с функциями форматирования для каждого режима
    """
    from config.settings import BIBLE_VERSE_NUMBER_SPACING, BIBLE_INCLUDE_CHAPTER_NUMBER, BIBLE_VERSE_NUMBER_STYLE

    # Создаем строку с нужным количеством пробелов
    spacing = " " * BIBLE_VERSE_NUMBER_SPACING

    def format_verse_number(verse_num):
        """Форматирует номер стиха в зависимости от настроек"""
        if BIBLE_INCLUDE_CHAPTER_NUMBER and chapter_num is not None:
            return f"{chapter_num}:{verse_num}"
        else:
            return str(verse_num)

    def escape_md(s):
        """Экранирует спецсимволы для MarkdownV2"""
        s = s.replace('\\', '\\\\')
        chars = r'_ * [ ] ( ) ~ ` > # + - = | { } . !'
        for c in chars.split():
            s = s.replace(c, f'\\{c}')
        return s

    # Функции форматирования для разных стилей
    def format_for_html(num, text):
        verse_num = format_verse_number(num)
        if BIBLE_VERSE_NUMBER_STYLE == "bold":
            return f"<b>{verse_num}</b>{spacing}{text}"
        elif BIBLE_VERSE_NUMBER_STYLE == "code":
            return f"<code>{verse_num}</code>{spacing}{text}"
        elif BIBLE_VERSE_NUMBER_STYLE == "italic":
            return f"<i>{verse_num}</i>{spacing}{text}"
        else:  # По умолчанию bold
            return f"<b>{verse_num}</b>{spacing}{text}"

    def format_for_markdown(num, text):
        verse_num = format_verse_number(num)
        if BIBLE_VERSE_NUMBER_STYLE == "bold":
            return f"**{verse_num}**{spacing}{text}"
        elif BIBLE_VERSE_NUMBER_STYLE == "code":
            return f"`{verse_num}`{spacing}{text}"
        elif BIBLE_VERSE_NUMBER_STYLE == "italic":
            return f"_{verse_num}_{spacing}{text}"
        else:  # По умолчанию bold
            return f"**{verse_num}**{spacing}{text}"

    def format_for_markdownv2(num, text):
        verse_num = format_verse_number(num)
        if BIBLE_VERSE_NUMBER_STYLE == "bold":
            return f"*{verse_num}*{spacing}{escape_md(text)}"
        elif BIBLE_VERSE_NUMBER_STYLE == "code":
            return f"`{verse_num}`{spacing}{escape_md(text)}"
        elif BIBLE_VERSE_NUMBER_STYLE == "italic":
            return f"__{verse_num}__{spacing}{escape_md(text)}"
        else:  # По умолчанию bold
            return f"*{verse_num}*{spacing}{escape_md(text)}"

    def format_for_plain(num, text):
        verse_num = format_verse_number(num)
        return f"{verse_num}{spacing}{text}"

    return {
        "HTML": format_for_html,
        "MARKDOWN": format_for_markdown,
        "MARKDOWNV2": format_for_markdownv2,
        "PLAIN": format_for_plain
    }
