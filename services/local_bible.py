"""
Сервис для работы с локальными JSON файлами Библии.
"""
import json
import logging
import os
from typing import Dict, Any, Optional, List
import re

from config.settings import LOCAL_FILES_PATH
from utils.bible_data import bible_data

logger = logging.getLogger(__name__)


class LocalBibleService:
    """Класс для работы с локальными JSON файлами Библии."""

    def __init__(self):
        self._cache = {}  # Кэш загруженных переводов
        self._loaded_translations = set()  # Множество загруженных переводов

    def _load_translation(self, translation: str) -> Dict[str, Any]:
        """
        Загружает перевод из JSON файла в память.

        Args:
            translation: Код перевода (rst, rbo)

        Returns:
            Словарь с данными перевода
        """
        if translation in self._cache:
            return self._cache[translation]

        file_path = os.path.join(LOCAL_FILES_PATH, f"{translation}.json")

        if not os.path.exists(file_path):
            logger.error(f"Файл перевода не найден: {file_path}")
            raise FileNotFoundError(f"Файл перевода {translation} не найден")

        try:
            logger.info(f"Загружаю перевод {translation} из {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self._cache[translation] = data
            self._loaded_translations.add(translation)
            logger.info(f"Перевод {translation} успешно загружен")
            return data

        except Exception as e:
            logger.error(f"Ошибка при загрузке перевода {translation}: {e}")
            raise

    def _get_book_name_from_id(self, book_id: int) -> str:
        """
        Получает название книги для поиска в JSON по ID книги.

        Args:
            book_id: ID книги (1-66)

        Returns:
            Название книги для поиска в JSON
        """
        # Маппинг ID книг на названия в JSON файлах (точные названия из файлов)
        book_names_map = {
            1: "Бытие", 2: "Исход", 3: "Левит", 4: "Числа", 5: "Второзаконие",
            6: "Иисус Навин", 7: "Судьи", 8: "Руфь", 9: "1 Царств", 10: "2 Царств",
            11: "3 Царств", 12: "4 Царств", 13: "1 Паралипоменон", 14: "2 Паралипоменон",
            15: "Ездра", 16: "Неемия", 17: "Есфирь", 18: "Иов", 19: "Псалтирь",
            20: "Притчи", 21: "Екклесиаст", 22: "Песня Песней", 23: "Исаия", 24: "Иеремия",
            25: "Плач Иеремии", 26: "Иезекииль", 27: "Даниил", 28: "Осия", 29: "Иоиль",
            30: "Амос", 31: "Авдий", 32: "Иона", 33: "Михей", 34: "Наум", 35: "Аввакум",
            36: "Софоний", 37: "Аггей", 38: "Захария", 39: "Малахия", 40: "Матфей",
            41: "Марк", 42: "Лука", 43: "Иоанн", 44: "Деяния", 45: "Иаков",
            46: "1 Петра", 47: "2 Петра", 48: "1 Иоанна", 49: "2 Иоанна",
            50: "3 Иоанна", 51: "Иуда", 52: "Римлянам", 53: "1 Коринфянам",
            54: "2 Коринфянам", 55: "Галатам", 56: "Ефесянам", 57: "Филиппийцам",
            58: "Колоссянам", 59: "1 Фессалоникийцам", 60: "2 Фессалоникийцам",
            61: "1 Тимофею", 62: "2 Тимофею", 63: "Титу", 64: "Филимону",
            65: "Евреям", 66: "Откровение"
        }

        return book_names_map.get(book_id, f"Книга {book_id}")

    def _find_book_in_data(self, data: Dict[str, Any], book_id: int) -> Optional[str]:
        """
        Находит ключ книги в данных JSON по ID книги.

        Args:
            data: Данные перевода
            book_id: ID книги

        Returns:
            Ключ книги в JSON или None
        """
        expected_name = self._get_book_name_from_id(book_id)

        # Сначала пробуем точное совпадение
        if expected_name in data:
            return expected_name

        # Если не найдено, ищем по частичному совпадению
        for key in data.keys():
            if expected_name.lower() in key.lower() or key.lower() in expected_name.lower():
                return key

        # Если все еще не найдено, логируем доступные ключи для отладки
        logger.warning(
            f"Книга с ID {book_id} ({expected_name}) не найдена в данных")
        # Показываем первые 10
        logger.debug(f"Доступные книги: {list(data.keys())[:10]}...")

        return None

    async def get_chapter(self, book: int, chapter: int, translation: str = "rst") -> Dict[str, Any]:
        """
        Получает текст главы из локального JSON файла.

        Args:
            book: Номер книги (1-66)
            chapter: Номер главы
            translation: Код перевода (rst, rbo)

        Returns:
            Словарь с текстом главы в формате, совместимом с API
        """
        try:
            book = int(book)
            chapter = int(chapter)
        except Exception as e:
            logger.error(f"Некорректные типы для book или chapter: {e}")
            raise ValueError("book и chapter должны быть целыми числами")

        try:
            # Загружаем данные перевода
            data = self._load_translation(translation)

            # Находим книгу в данных
            book_key = self._find_book_in_data(data, book)
            if not book_key:
                raise ValueError(
                    f"Книга с ID {book} не найдена в переводе {translation}")

            book_data = data[book_key]

            # Проверяем наличие главы
            chapter_str = str(chapter)
            if chapter_str not in book_data:
                raise ValueError(
                    f"Глава {chapter} не найдена в книге {book_key}")

            chapter_data = book_data[chapter_str]

            # Формируем ответ в формате, совместимом с API
            result = {
                "info": {
                    "book": bible_data.get_book_name(book),
                    "chapter": chapter,
                    "translation": translation
                }
            }

            # Добавляем стихи
            for verse_num, verse_text in chapter_data.items():
                result[verse_num] = verse_text

            return result

        except Exception as e:
            logger.error(
                f"Ошибка при получении главы {book}:{chapter} из локального файла: {e}")
            raise

    async def get_verses(self, book: int, chapter: int, verse_range, translation: str = "rst") -> str:
        """
        Получает текст одного стиха или диапазона стихов из главы.

        Args:
            book: Номер книги
            chapter: Номер главы
            verse_range: int (один стих) или (start, end) для диапазона
            translation: Код перевода

        Returns:
            Отформатированный текст стихов
        """
        try:
            chapter_data = await self.get_chapter(book, chapter, translation)

            # Получаем стихи (исключаем 'info')
            verses = []
            verse_numbers = []

            for key, value in chapter_data.items():
                if key != "info":
                    try:
                        verse_num = int(key)
                        verses.append((verse_num, value))
                        verse_numbers.append(verse_num)
                    except ValueError:
                        continue

            # Сортируем по номеру стиха
            verses.sort(key=lambda x: x[0])
            verse_texts = [v[1] for v in verses]

            if isinstance(verse_range, tuple):
                start, end = verse_range
                # Находим индексы стихов в отсортированном списке
                start_idx = None
                end_idx = None

                for i, (verse_num, _) in enumerate(verses):
                    if verse_num == start:
                        start_idx = i
                    if verse_num == end:
                        end_idx = i
                        break

                if start_idx is None or end_idx is None:
                    raise ValueError(f"Стихи {start}-{end} не найдены")

                selected = verse_texts[start_idx:end_idx + 1]
                verses_text = ' '.join(selected)
                ref = f"{chapter_data['info']['book']} {chapter}:{start}-{end}"
            else:
                # Один стих
                verse_idx = None
                for i, (verse_num, _) in enumerate(verses):
                    if verse_num == verse_range:
                        verse_idx = i
                        break

                if verse_idx is None:
                    raise ValueError(f"Стих {verse_range} не найден")

                selected = [verse_texts[verse_idx]]
                verses_text = ' '.join(selected)
                ref = f"{chapter_data['info']['book']} {chapter}:{verse_range}"

            testament = "Ветхий завет" if book < 40 else "Новый завет"
            return f"{testament}. {ref}:\n{verses_text}"

        except Exception as e:
            logger.error(f"Ошибка при получении стихов: {e}")
            return f"Ошибка: {e}"

    async def get_formatted_chapter(self, book: int, chapter: int, translation: str = "rst") -> str:
        """
        Получает отформатированный текст главы.

        Args:
            book: Номер книги (1-66)
            chapter: Номер главы
            translation: Код перевода (rst, rbo)

        Returns:
            Отформатированный текст главы
        """
        try:
            chapter_data = await self.get_chapter(book, chapter, translation)

            # Получаем стихи (исключаем 'info')
            verses = []
            for key, value in chapter_data.items():
                if key != "info":
                    verses.append(value)

            testament = "Ветхий завет" if book < 40 else "Новый завет"
            book_name = chapter_data['info']['book']

            return f"{testament}. {book_name} {chapter}:\n{' '.join(verses)}"

        except Exception as e:
            logger.error(f"Ошибка при получении отформатированной главы: {e}")
            return f"Ошибка: {e}"

    async def search_bible_text(self, search_query: str, translation: str = "rst") -> List[Dict[str, Any]]:
        """
        Поиск слова или фразы в тексте Библии в локальных файлах.

        Args:
            search_query: Поисковый запрос
            translation: Код перевода (rst, rbo)

        Returns:
            Список найденных результатов в формате API
        """
        if len(search_query) < 3:
            logger.warning("Слишком короткий поисковый запрос")
            return []

        try:
            # Загружаем данные перевода
            data = self._load_translation(translation)

            results = []
            search_lower = search_query.lower()

            # Проходим по всем книгам
            for book_name, book_data in data.items():
                # Определяем ID книги
                book_id = None
                for bid, bname in bible_data.book_dict.items():
                    if bname.lower() in book_name.lower() or book_name.lower() in bname.lower():
                        book_id = bid
                        break

                if not book_id:
                    continue

                # Проходим по главам
                for chapter_str, chapter_data in book_data.items():
                    try:
                        chapter_num = int(chapter_str)
                    except ValueError:
                        continue

                    # Проходим по стихам
                    for verse_str, verse_text in chapter_data.items():
                        try:
                            verse_num = int(verse_str)
                        except ValueError:
                            continue

                        # Проверяем наличие поискового запроса в тексте стиха
                        if search_lower in verse_text.lower():
                            results.append({
                                "book": book_id,
                                "chapter": chapter_num,
                                "verse": verse_num,
                                "text": verse_text,
                                "book_name": bible_data.get_book_name(book_id),
                                "reference": f"{bible_data.get_book_name(book_id)} {chapter_num}:{verse_num}"
                            })

            logger.info(
                f"Найдено {len(results)} результатов для запроса '{search_query}'")
            return results

        except Exception as e:
            logger.error(f"Ошибка при поиске в локальных файлах: {e}")
            return []

    async def get_verse_by_reference(self, reference: str, translation: str = "rst") -> str:
        """
        Получает текст по библейской ссылке из локальных файлов.

        Args:
            reference: Библейская ссылка
            translation: Код перевода

        Returns:
            Отформатированный текст
        """
        try:
            # Парсим ссылку
            parsed = bible_data.parse_reference(reference)
            if not parsed:
                return f"Не удалось распознать ссылку: {reference}"

            book_id, chapter, start_verse, end_verse = parsed

            if start_verse and end_verse:
                # Диапазон стихов
                return await self.get_verses(book_id, chapter, (start_verse, end_verse), translation)
            elif start_verse:
                # Один стих
                return await self.get_verses(book_id, chapter, start_verse, translation)
            else:
                # Вся глава
                return await self.get_formatted_chapter(book_id, chapter, translation)

        except Exception as e:
            logger.error(
                f"Ошибка при получении текста по ссылке {reference} из локальных файлов: {e}")
            return f"Ошибка при получении текста: {reference}"


# Создаем глобальный экземпляр сервиса
local_bible_service = LocalBibleService()
