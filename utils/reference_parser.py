"""
Парсер библейских ссылок для планов чтения.
"""
import re
import logging
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

# Словарь сокращений книг Библии
BOOK_ABBREVIATIONS = {
    # Ветхий Завет
    'Быт': 'Бытие', 'Исх': 'Исход', 'Лев': 'Левит', 'Чис': 'Числа', 'Втор': 'Второзаконие',
    'Нав': 'Иисус Навин', 'Суд': 'Судьи', 'Руф': 'Руфь',
    'Первая Царств': '1 Царств', '1Цар': '1 Царств', '2Цар': '2 Царств', '3Цар': '3 Царств', '4Цар': '4 Царств',
    'Первая Паралипоменон': '1 Паралипоменон', '1Пар': '1 Паралипоменон', '2Пар': '2 Паралипоменон',
    'Езд': 'Ездра', 'Неем': 'Неемия', 'Есф': 'Есфирь',
    'Иов': 'Иов', 'Пс': 'Псалтирь', 'Прит': 'Притчи', 'Еккл': 'Екклесиаст', 'Песн': 'Песнь Песней',
    'Ис': 'Исаия', 'Иер': 'Иеремия', 'Плач': 'Плач Иеремии', 'Иез': 'Иезекииль', 'Дан': 'Даниил',
    'Ос': 'Осия', 'Иоиль': 'Иоиль', 'Ам': 'Амос', 'Авд': 'Авдий', 'Ион': 'Иона', 'Мих': 'Михей',
    'Наум': 'Наум', 'Авв': 'Аввакум', 'Соф': 'Софония', 'Агг': 'Аггей', 'Зах': 'Захария', 'Мал': 'Малахия',

    # Новый Завет
    'Мф': 'Матфей', 'Мк': 'Марк', 'Лк': 'Лука', 'Ин': 'Иоанн',
    'Деян': 'Деяния', 'Рим': 'Римлянам',
    '1Кор': '1 Коринфянам', '2Кор': '2 Коринфянам',
    'Гал': 'Галатам', 'Еф': 'Ефесянам', 'Флп': 'Филиппийцам', 'Кол': 'Колоссянам',
    '1Фес': '1 Фессалоникийцам', '2Фес': '2 Фессалоникийцам',
    '1Тим': '1 Тимофею', '2Тим': '2 Тимофею', 'Тит': 'Титу', 'Флм': 'Филимону',
    'Евр': 'Евреям', 'Иак': 'Иакова',
    '1Пет': '1 Петра', '2Пет': '2 Петра',
    '1Ин': '1 Иоанна', '2Ин': '2 Иоанна', '3Ин': '3 Иоанна',
    'Иуд': 'Иуды', 'Откр': 'Откровение'
}


def normalize_book_name(book_abbr: str) -> str:
    """Нормализует сокращение книги к полному названию."""
    # Убираем лишние пробелы
    book_abbr = book_abbr.strip()

    # Проверяем прямое соответствие
    if book_abbr in BOOK_ABBREVIATIONS:
        return BOOK_ABBREVIATIONS[book_abbr]

    # Проверяем без учета регистра
    for abbr, full_name in BOOK_ABBREVIATIONS.items():
        if abbr.lower() == book_abbr.lower():
            return full_name

    # Если не найдено, возвращаем как есть
    return book_abbr


def parse_reference(reference: str) -> Optional[Dict]:
    """
    Парсит библейскую ссылку.

    Примеры:
    - "Мф 1" -> {'book': 'Матфей', 'chapter': 1}
    - "Мф 1:1" -> {'book': 'Матфей', 'chapter': 1, 'verse_start': 1, 'verse_end': 1}
    - "Мф 1:1-5" -> {'book': 'Матфей', 'chapter': 1, 'verse_start': 1, 'verse_end': 5}
    - "Лк 5:27-39" -> {'book': 'Лука', 'chapter': 5, 'verse_start': 27, 'verse_end': 39}
    - "Быт 1:1-2:25" -> {'book': 'Бытие', 'chapter': 1, 'verse_start': 1, 'verse_end': 25, 'end_chapter': 2}
    """
    try:
        reference = reference.strip()

        # Сначала пробуем сложный паттерн для межглавных диапазонов: "Быт 1:1-2:25"
        complex_pattern = r'^(.+?)\s+(\d+):(\d+)-(\d+):(\d+)$'
        complex_match = re.match(complex_pattern, reference)

        if complex_match:
            book_abbr = complex_match.group(1).strip()
            chapter = int(complex_match.group(2))
            verse_start = int(complex_match.group(3))
            end_chapter = int(complex_match.group(4))
            verse_end = int(complex_match.group(5))

            book_name = normalize_book_name(book_abbr)

            return {
                'book': book_name,
                'chapter': chapter,
                'verse_start': verse_start,
                'verse_end': verse_end,
                'end_chapter': end_chapter
            }

        # Простой паттерн для обычных ссылок
        simple_pattern = r'^(.+?)\s+(\d+)(?::(\d+)(?:-(\d+))?)?$'
        simple_match = re.match(simple_pattern, reference)

        if not simple_match:
            logger.warning(f"Не удалось распарсить ссылку: {reference}")
            return None

        book_abbr = simple_match.group(1).strip()
        chapter = int(simple_match.group(2))
        verse_start = int(simple_match.group(
            3)) if simple_match.group(3) else None
        verse_end = int(simple_match.group(
            4)) if simple_match.group(4) else verse_start

        # Нормализуем название книги
        book_name = normalize_book_name(book_abbr)

        result = {
            'book': book_name,
            'chapter': chapter
        }

        if verse_start is not None:
            result['verse_start'] = verse_start
            result['verse_end'] = verse_end

        return result

    except Exception as e:
        logger.error(f"Ошибка при парсинге ссылки '{reference}': {e}")
        return None


def parse_multiple_references(references_text: str) -> List[Dict]:
    """
    Парсит несколько ссылок, разделенных точкой с запятой.

    Пример: "Мф 1; Мф 2" -> [{'book': 'Матфей', 'chapter': 1}, {'book': 'Матфей', 'chapter': 2}]
    """
    references = []

    # Разделяем по точке с запятой
    parts = references_text.split(';')

    for part in parts:
        part = part.strip()
        if part:
            parsed = parse_reference(part)
            if parsed:
                references.append(parsed)

    return references


def format_reference(parsed_ref: Dict) -> str:
    """
    Форматирует распарсенную ссылку обратно в строку.
    """
    book = parsed_ref['book']
    chapter = parsed_ref['chapter']

    if 'verse_start' in parsed_ref:
        verse_start = parsed_ref['verse_start']
        verse_end = parsed_ref.get('verse_end', verse_start)

        if verse_start == verse_end:
            return f"{book} {chapter}:{verse_start}"
        else:
            return f"{book} {chapter}:{verse_start}-{verse_end}"
    else:
        return f"{book} {chapter}"


# Тестирование функций
if __name__ == "__main__":
    test_references = [
        "Мф 1",
        "Мф 1:1",
        "Мф 1:1-5",
        "Лк 5:27-39",
        "Первая Царств 1:1-2:25",
        "Быт 1:1-2:25",
        "Пс 1"
    ]

    for ref in test_references:
        parsed = parse_reference(ref)
        print(f"{ref} -> {parsed}")
        if parsed:
            formatted = format_reference(parsed)
            print(f"  Formatted: {formatted}")
