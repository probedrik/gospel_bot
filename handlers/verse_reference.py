import re
from aiogram.fsm.context import FSMContext
from middleware.state import get_current_translation, set_chosen_book, set_current_chapter
from utils.bible_data import bible_data
from utils.api_client import bible_api
import logging

logger = logging.getLogger(__name__)


async def get_verse_by_reference(state: FSMContext, reference: str) -> tuple:
    """
    Обработка ссылки на стих или главу в формате "Книга Глава:Стих" или "Книга Глава"
    Возвращает текст и имеет ли стих/глава продолжение
    """
    translation = await get_current_translation(state)

    try:
        # Распарсить ссылку
        book_name, chapter, verse = parse_reference(reference)
        if not book_name:
            return "Неверный формат ссылки. Используйте формат 'Книга Глава:Стих' или 'Книга Глава'", False

        # Получить ID книги
        book_id = bible_data.get_book_id(book_name)
        if not book_id:
            return f"Книга '{book_name}' не найдена.", False

        # Проверка допустимости главы
        # ПРИМЕЧАНИЕ: 2 Петра имеет ID 47 (не 61)
        max_chapter = bible_data.max_chapters.get(book_id, 0)

        logger.info(
            f"Запрос на стих: {book_name} (ID: {book_id}) глава {chapter}, макс. глав: {max_chapter}")

        # Проверка допустимости главы только для обычных ссылок
        if isinstance(chapter, int) and (chapter < 1 or chapter > max_chapter):
            return f"Книга '{book_name}' содержит {max_chapter} глав. Укажите главу от 1 до {max_chapter}.", False

        # Получение текста: стих, диапазон или вся глава
        if chapter == "chapter_range":
            # Диапазон глав (например, Быт 1-3)
            start_chapter, end_chapter = verse
            result = await get_chapter_range(book_id, start_chapter, end_chapter, translation)
            await set_chosen_book(state, book_id)
            await set_current_chapter(state, start_chapter)
            has_continuation = True

            # Возвращаем также информацию о book_id и chapter для совместимости
            return result, {"book_id": book_id, "chapter": start_chapter, "is_range": True}

        elif chapter == "cross_chapter_range":
            # Диапазон стихов через главы (например, Быт 1:1-2:25)
            start_chapter, start_verse, end_chapter, end_verse = verse
            result = await get_cross_chapter_range(book_id, start_chapter, start_verse, end_chapter, end_verse, translation)
            await set_chosen_book(state, book_id)
            await set_current_chapter(state, start_chapter)
            has_continuation = True

            # Возвращаем также информацию о book_id и chapter для совместимости
            return result, {"book_id": book_id, "chapter": start_chapter, "is_range": True}

        elif verse:
            await set_chosen_book(state, book_id)
            await set_current_chapter(state, chapter)
            if isinstance(verse, tuple):
                result = await bible_api.get_verses(book_id, chapter, verse, translation)
            elif isinstance(verse, int):
                result = await bible_api.get_verses(book_id, chapter, verse, translation)
            else:
                result = await bible_api.get_formatted_chapter(book_id, chapter, translation)
            has_continuation = True
        else:
            await set_chosen_book(state, book_id)
            await set_current_chapter(state, chapter)
            result = await bible_api.get_formatted_chapter(book_id, chapter, translation)
            has_previous = chapter > 1
            has_next = chapter < max_chapter
            has_continuation = has_previous or has_next

        if result.startswith("Ошибка:"):
            return result, False

        return result, has_continuation
    except Exception as e:
        logger.error(
            f"Ошибка при обработке ссылки на стих: {e}", exc_info=True)
        return "Произошла ошибка при обработке ссылки. Пожалуйста, проверьте формат и попробуйте снова.", False


def parse_reference(reference: str):
    """
    Парсит ссылку на стих или диапазон стихов/глав.
    Поддерживает форматы:
      - 'Ин 3:16' (один стих)
      - 'Ин 3:16-18' (диапазон стихов в одной главе)
      - 'Ин 3' (вся глава)
      - 'Быт 1-3' (диапазон глав с 1 по 3)
      - 'Быт 1:1-2:25' (диапазон стихов через главы)
      - 'от иоанна 3:16', 'иоанн 3:16' и т.д.
    Возвращает (нормализованное_название_книги, номер_главы, номер_стиха или специальный формат для диапазонов)
    """
    # Сначала проверяем диапазон глав: Быт 1-3
    chapter_range_match = re.match(
        r'^([а-яА-ЯёЁ0-9\s]+)\s+(\d+)-(\d+)$', reference.strip(), re.IGNORECASE)
    if chapter_range_match:
        book_raw = chapter_range_match.group(1).strip()
        start_chapter = int(chapter_range_match.group(2))
        end_chapter = int(chapter_range_match.group(3))
        book = bible_data.normalize_book_name(book_raw)
        return book, "chapter_range", (start_chapter, end_chapter)

    # Проверяем диапазон стихов через главы: Быт 1:1-2:25
    cross_chapter_match = re.match(
        r'^([а-яА-ЯёЁ0-9\s]+)\s+(\d+):(\d+)-(\d+):(\d+)$', reference.strip(), re.IGNORECASE)
    if cross_chapter_match:
        book_raw = cross_chapter_match.group(1).strip()
        start_chapter = int(cross_chapter_match.group(2))
        start_verse = int(cross_chapter_match.group(3))
        end_chapter = int(cross_chapter_match.group(4))
        end_verse = int(cross_chapter_match.group(5))
        book = bible_data.normalize_book_name(book_raw)
        return book, "cross_chapter_range", (start_chapter, start_verse, end_chapter, end_verse)

    # Обычные форматы: Ин 3:16-18 или Ин 3:16 или Ин 3
    match = re.match(
        r'^([а-яА-ЯёЁ0-9\s]+)\s+(\d+)(?::(\d+)(?:-(\d+))?)?$', reference.strip(), re.IGNORECASE)
    if not match:
        return None, None, None
    book_raw = match.group(1).strip()
    chapter = int(match.group(2))
    verse = match.group(3)
    verse_end = match.group(4)
    # Нормализация названия книги
    book = bible_data.normalize_book_name(book_raw)
    if verse and verse_end:
        return book, chapter, (int(verse), int(verse_end))
    elif verse:
        return book, chapter, int(verse)
    else:
        return book, chapter, None


async def get_chapter_range(book_id: int, start_chapter: int, end_chapter: int, translation: str) -> str:
    """
    Получает текст диапазона глав (например, Быт 1-3)
    """
    try:
        from utils.bible_data import bible_data
        from utils.api_client import bible_api
        from config.settings import ENABLE_VERSE_NUMBERS

        # Проверяем валидность диапазона
        max_chapter = bible_data.max_chapters.get(book_id, 0)
        if start_chapter < 1 or end_chapter > max_chapter or start_chapter > end_chapter:
            return f"Ошибка: неверный диапазон глав {start_chapter}-{end_chapter}"

        result = ""
        for chapter_num in range(start_chapter, end_chapter + 1):
            # Используем правильный метод в зависимости от настроек номеров стихов
            if ENABLE_VERSE_NUMBERS:
                chapter_text = await bible_api.get_formatted_chapter_with_verses(book_id, chapter_num, translation)
            else:
                chapter_text = await bible_api.get_formatted_chapter(book_id, chapter_num, translation)

            if chapter_text.startswith("Ошибка:"):
                return chapter_text
            result += chapter_text + "\n\n"

        return result.strip()

    except Exception as e:
        logger.error(f"Ошибка при получении диапазона глав: {e}")
        return f"Ошибка при получении диапазона глав: {e}"


async def get_cross_chapter_range(book_id: int, start_chapter: int, start_verse: int, end_chapter: int, end_verse: int, translation: str) -> str:
    """
    Получает текст диапазона стихов через главы (например, Быт 1:1-2:25)
    """
    try:
        from utils.bible_data import bible_data
        from utils.api_client import bible_api

        # Проверяем валидность диапазона
        max_chapter = bible_data.max_chapters.get(book_id, 0)
        if start_chapter < 1 or end_chapter > max_chapter or start_chapter > end_chapter:
            return f"Ошибка: неверный диапазон глав {start_chapter}-{end_chapter}"

        result = ""

        if start_chapter == end_chapter:
            # Диапазон стихов в одной главе - используем существующий API метод
            result = await bible_api.get_verses(book_id, start_chapter, (start_verse, end_verse), translation)
        else:
            # Диапазон через несколько глав - обрабатываем каждую главу отдельно
            for chapter_num in range(start_chapter, end_chapter + 1):
                if chapter_num == start_chapter:
                    # Первая глава: от start_verse до конца главы
                    # Получаем информацию о количестве стихов в главе
                    chapter_data = await bible_api.get_chapter(book_id, chapter_num, translation)
                    if not chapter_data:
                        return f"Ошибка: не удалось получить главу {chapter_num}"

                    # Находим максимальный номер стиха в главе
                    max_verse = 0
                    for key in chapter_data.keys():
                        if key != "info":
                            try:
                                verse_num = int(key)
                                max_verse = max(max_verse, verse_num)
                            except ValueError:
                                continue

                    chapter_text = await bible_api.get_verses(book_id, chapter_num, (start_verse, max_verse), translation)
                elif chapter_num == end_chapter:
                    # Последняя глава: от первого стиха до end_verse
                    chapter_text = await bible_api.get_verses(book_id, chapter_num, (1, end_verse), translation)
                else:
                    # Промежуточные главы: вся глава
                    from config.settings import ENABLE_VERSE_NUMBERS
                    if ENABLE_VERSE_NUMBERS:
                        chapter_text = await bible_api.get_formatted_chapter_with_verses(book_id, chapter_num, translation)
                    else:
                        chapter_text = await bible_api.get_formatted_chapter(book_id, chapter_num, translation)

                if chapter_text.startswith("Ошибка:"):
                    return chapter_text

                result += chapter_text + "\n\n"

        return result.strip()

    except Exception as e:
        logger.error(f"Ошибка при получении диапазона стихов через главы: {e}")
        return f"Ошибка при получении диапазона стихов через главы: {e}"
