"""
Клиент для работы с API Библии.
"""
import logging
import aiohttp
import time
from typing import Dict, Any, Optional

from config.settings import API_URL, API_TIMEOUT, CACHE_TTL
from config.ai_settings import (
    ENABLE_GPT_EXPLAIN, OPENROUTER_API_KEY, OPENROUTER_MODEL, LLM_ROLE,
    OPENROUTER_PREMIUM_API_KEY, OPENROUTER_PREMIUM_MODEL, LLM_PREMIUM_ROLE,
    AI_REGULAR_MAX_CHARS, AI_PREMIUM_MAX_CHARS,
    DEFAULT_MAX_TOKENS, PREMIUM_MAX_TOKENS_SHORT, PREMIUM_MAX_TOKENS_FULL
)
# Добавляем флаг для логирования OpenRouter API
try:
    from config.ai_settings import LOG_OPENROUTER_RESPONSE
except ImportError:
    LOG_OPENROUTER_RESPONSE = False

# Инициализация логгера
logger = logging.getLogger(__name__)


class BibleAPIClient:
    """Класс для работы с API Библии с поддержкой кэширования."""

    def __init__(self):
        self._session = None
        # Простой кэш в памяти: ключ -> (значение, время_истечения)
        self._cache = {}

    async def get_session(self) -> aiohttp.ClientSession:
        """Возвращает существующую сессию или создает новую."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self) -> None:
        """Закрывает сессию, если она открыта."""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.info("HTTP сессия закрыта")

    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Получает данные из кэша, если они есть и не устарели."""
        if key in self._cache:
            value, expiration_time = self._cache[key]
            if time.time() < expiration_time:
                logger.debug(f"Данные получены из кэша: {key}")
                return value
            # Если данные устарели, удаляем их из кэша
            del self._cache[key]
        return None

    def _set_to_cache(self, key: str, value: Any, ttl: int = CACHE_TTL) -> None:
        """Сохраняет данные в кэш с указанным временем жизни."""
        expiration_time = time.time() + ttl
        self._cache[key] = (value, expiration_time)
        logger.debug(f"Данные сохранены в кэш: {key}")

    async def get_chapter(
        self, book: int, chapter: int, translation: str = "rst"
    ) -> Dict[str, Any]:
        """
        Получает текст главы из API.

        Args:
            book: Номер книги (1-66)
            chapter: Номер главы
            translation: Код перевода (rst, rbo)

        Returns:
            Словарь с текстом главы и информацией о ней
        """
        # Приведение типов для book и chapter
        try:
            book = int(book)
            chapter = int(chapter)
        except Exception as e:
            logger.error(f"Некорректные типы для book или chapter: {e}")
            raise ValueError("book и chapter должны быть целыми числами")

        cache_key = f"chapter_{book}_{chapter}_{translation}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data

        url = f"{API_URL}/bible?translation={translation}&book={book}&chapter={chapter}"
        try:
            session = await self.get_session()
            async with session.get(url, timeout=API_TIMEOUT) as response:
                response.raise_for_status()
                data = await response.json()

                # Сохраняем в кэш
                self._set_to_cache(cache_key, data)
                return data
        except aiohttp.ClientError as e:
            logger.error(f"Ошибка при запросе к API (chapter): {e}")
            raise

    async def get_formatted_chapter(
        self, book: int, chapter: int, translation: str = "rst"
    ) -> str:
        """
        Получает отформатированный текст главы.

        Args:
            book: Номер книги (1-66)
            chapter: Номер главы
            translation: Код перевода (rst, rbo)

        Returns:
            Отформатированный текст главы
        """
        # Приведение типов для book и chapter
        try:
            book = int(book)
            chapter = int(chapter)
        except Exception as e:
            logger.error(f"Некорректные типы для book или chapter: {e}")
            return f"Ошибка: некорректные параметры главы (book/chapter)"
        try:
            from config.settings import ENABLE_VERSE_NUMBERS

            data = await self.get_chapter(book, chapter, translation)
            # Проверка наличия ключа 'info' и нужных данных
            if not data or 'info' not in data or 'book' not in data['info']:
                logger.error(
                    f"Некорректный ответ от API (нет 'info' или 'book'): {data}")
                return "Ошибка: не удалось получить текст главы. Попробуйте позже."

            verses = [v for k, v in data.items() if k != "info"]
            testament = "Ветхий завет" if book < 40 else "Новый завет"

            if ENABLE_VERSE_NUMBERS:
                # Формат с номерами стихов
                return await self.get_formatted_chapter_with_verses(book, chapter, translation)
            else:
                # Обычный формат
                from config.settings import BIBLE_QUOTE_ENABLED
                from utils.text_utils import format_as_quote

                result = f"{testament}. {data['info']['book']} {chapter}:\n{' '.join(verses)}"

                # Применяем форматирование цитаты если включено
                if BIBLE_QUOTE_ENABLED:
                    result = format_as_quote(result)

                return result
        except Exception as e:
            logger.error(f"Ошибка при получении текста главы: {e}")
            return f"Ошибка: {e}"

    async def get_formatted_chapter_with_verses(
        self, book: int, chapter: int, translation: str = "rst"
    ) -> str:
        """
        Получает отформатированный текст главы с номерами стихов.

        Args:
            book: Номер книги (1-66)
            chapter: Номер главы
            translation: Код перевода (rst, rbo)

        Returns:
            Отформатированный текст главы с номерами стихов в текущем формате
        """
        try:
            from config.settings import BIBLE_MARKDOWN_ENABLED, BIBLE_MARKDOWN_MODE

            data = await self.get_chapter(book, chapter, translation)

            # Проверка наличия ключа 'info' и нужных данных
            if not data or 'info' not in data or 'book' not in data['info']:
                logger.error(
                    f"Некорректный ответ от API (нет 'info' или 'book'): {data}")
                return "Ошибка: не удалось получить текст главы. Попробуйте позже."

            # Получаем стихи с номерами (исключаем 'info')
            verses = []
            for key, value in data.items():
                if key != "info":
                    try:
                        verse_num = int(key)
                        verses.append((verse_num, value))
                    except ValueError:
                        continue

            # Сортируем по номеру стиха
            verses.sort(key=lambda x: x[0])

            testament = "Ветхий завет" if book < 40 else "Новый завет"
            book_name = data['info']['book']

            # Определяем формат, используя ту же логику что и get_verses_parse_mode()
            from utils.text_utils import get_verses_parse_mode
            parse_mode = get_verses_parse_mode()
            format_mode = parse_mode if parse_mode else "HTML"

            # Получаем функции форматирования
            from utils.text_utils import get_verse_format_functions
            format_functions = get_verse_format_functions(chapter)

            # Форматируем заголовок и стихи в зависимости от режима
            if format_mode.upper() == "HTML":
                title = f"<b>{testament}. {book_name} {chapter}:</b>"
                verse_format = format_functions["HTML"]
            elif format_mode.upper() == "MARKDOWN":
                title = f"**{testament}. {book_name} {chapter}:**"
                verse_format = format_functions["MARKDOWN"]
            elif format_mode.upper() == "MARKDOWNV2":
                # Экранируем спецсимволы для MarkdownV2
                def escape_md(s):
                    s = s.replace('\\', '\\\\')
                    chars = r'_ * [ ] ( ) ~ ` > # + - = | { } . !'
                    for c in chars.split():
                        s = s.replace(c, f'\\{c}')
                    return s

                escaped_testament = escape_md(testament)
                escaped_book = escape_md(book_name)
                title = f"*{escaped_testament}\\. {escaped_book} {chapter}:*"
                verse_format = format_functions["MARKDOWNV2"]
            else:
                # Обычный текст
                title = f"{testament}. {book_name} {chapter}:"
                verse_format = format_functions["PLAIN"]

            # Формируем результат
            result = f"{title}\n\n"

            for verse_num, verse_text in verses:
                result += f"{verse_format(verse_num, verse_text)}\n\n"

            result = result.strip()

            # Применяем форматирование цитаты если включено
            from config.settings import BIBLE_QUOTE_ENABLED
            from utils.text_utils import format_as_quote

            if BIBLE_QUOTE_ENABLED:
                result = format_as_quote(result)

            return result

        except Exception as e:
            logger.error(
                f"Ошибка при получении отформатированной главы с номерами стихов: {e}")
            return f"Ошибка: {e}"

    async def get_random_verse(self, translation: str = "rbo") -> str:
        """
        Получает случайный стих из API.

        Args:
            translation: Код перевода (rst, rbo)

        Returns:
            Текст случайного стиха
        """
        try:
            session = await self.get_session()
            async with session.get(
                f"{API_URL}/random?translation={translation}",
                timeout=API_TIMEOUT
            ) as response:
                data = await response.json()
            return f"{data['info']} - {data['verse']}"
        except Exception as e:
            logger.error(f"Ошибка при получении случайного стиха: {e}")
            return "Не удалось получить стих"

    async def search_bible_text(self, search_query: str, translation: str = "rst") -> list:
        """
        Поиск слова или фразы в тексте Библии через API.

        Args:
            search_query: Поисковый запрос
            translation: Код перевода (rst, rbo)

        Returns:
            Список найденных результатов
        """
        if len(search_query) < 3:
            logger.warning("Слишком короткий поисковый запрос")
            return []

        cache_key = f"search_{translation}_{search_query}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data

        try:
            url = f"{API_URL}/search?translation={translation}&search={search_query}"
            session = await self.get_session()
            async with session.get(url, timeout=API_TIMEOUT) as response:
                response.raise_for_status()
                data = await response.json()

                # Сохраняем в кэш
                self._set_to_cache(cache_key, data)
                return data
        except Exception as e:
            logger.error(f"Ошибка при поиске текста: {e}")
            return []

    async def get_verses(self, book: int, chapter: int, verse_range, translation: str = "rst") -> str:
        """
        Получает отформатированный текст одного стиха или диапазона стихов из главы.
        verse_range: int (один стих) или (start, end) для диапазона
        """
        # Приведение типов для book и chapter
        try:
            book = int(book)
            chapter = int(chapter)
        except Exception as e:
            logger.error(f"Некорректные типы для book или chapter: {e}")
            return f"Ошибка: некорректные параметры главы (book/chapter)"

        try:
            from config.settings import ENABLE_VERSE_NUMBERS, BIBLE_MARKDOWN_ENABLED, BIBLE_MARKDOWN_MODE, BIBLE_QUOTE_ENABLED
            from utils.text_utils import format_as_quote

            data = await self.get_chapter(book, chapter, translation)

            # Получаем все стихи как пары (номер, текст)
            all_verses = []
            for key, value in data.items():
                if key != "info":
                    try:
                        verse_num = int(key)
                        all_verses.append((verse_num, value))
                    except ValueError:
                        continue

            # Сортируем по номеру стиха
            all_verses.sort(key=lambda x: x[0])

            testament = "Ветхий завет" if book < 40 else "Новый завет"
            book_name = data['info']['book']

            # Определяем какие стихи нужны
            if isinstance(verse_range, tuple):
                start, end = verse_range
                selected_verses = [(num, text)
                                   for num, text in all_verses if start <= num <= end]
                ref_text = f"{start}-{end}"
            else:
                selected_verses = [(num, text)
                                   for num, text in all_verses if num == verse_range]
                ref_text = str(verse_range)

            if not selected_verses:
                return f"Ошибка: стихи не найдены"

            # Форматируем в зависимости от настроек
            if ENABLE_VERSE_NUMBERS:
                # Определяем формат, используя ту же логику что и get_verses_parse_mode()
                from utils.text_utils import get_verses_parse_mode
                parse_mode = get_verses_parse_mode()
                format_mode = parse_mode if parse_mode else "HTML"

                # Получаем функции форматирования
                from utils.text_utils import get_verse_format_functions
                format_functions = get_verse_format_functions(chapter)

                # Форматируем заголовок и стихи в зависимости от режима
                if format_mode.upper() == "HTML":
                    title = f"<b>{testament}. {book_name} {chapter}:{ref_text}</b>"
                    verse_format = format_functions["HTML"]
                elif format_mode.upper() == "MARKDOWN":
                    title = f"**{testament}. {book_name} {chapter}:{ref_text}**"
                    verse_format = format_functions["MARKDOWN"]
                elif format_mode.upper() == "MARKDOWNV2":
                    # Экранируем спецсимволы для MarkdownV2
                    def escape_md(s):
                        s = s.replace('\\', '\\\\')
                        chars = r'_ * [ ] ( ) ~ ` > # + - = | { } . !'
                        for c in chars.split():
                            s = s.replace(c, f'\\{c}')
                        return s

                    escaped_testament = escape_md(testament)
                    escaped_book = escape_md(book_name)
                    escaped_ref = escape_md(ref_text)
                    title = f"*{escaped_testament}\\. {escaped_book} {chapter}:{escaped_ref}*"
                    verse_format = format_functions["MARKDOWNV2"]
                else:
                    # Обычный текст
                    title = f"{testament}. {book_name} {chapter}:{ref_text}"
                    verse_format = format_functions["PLAIN"]

                # Формируем результат с номерами стихов
                result = f"{title}\n\n"
                for verse_num, verse_text in selected_verses:
                    result += f"{verse_format(verse_num, verse_text)}\n\n"
                result = result.strip()
            else:
                # Простой формат без номеров стихов
                verses_text = ' '.join([text for num, text in selected_verses])
                result = f"{testament}. {book_name} {chapter}:{ref_text}\n{verses_text}"

            # Применяем форматирование цитаты если включено
            if BIBLE_QUOTE_ENABLED:
                result = format_as_quote(result)

            return result

        except Exception as e:
            logger.error(f"Ошибка при получении диапазона стихов: {e}")
            return f"Ошибка: {e}"

    async def get_formatted_verses(self, book: int, chapter: int, start_verse: int, end_verse: int, translation: str = "rst") -> str:
        """
        Получает отформатированный текст диапазона стихов главы.

        Args:
            book: Номер книги (1-66)
            chapter: Номер главы
            start_verse: Начальный стих
            end_verse: Конечный стих
            translation: Код перевода (rst, rbo)

        Returns:
            Отформатированный текст стихов
        """
        try:
            data = await self.get_chapter(book, chapter, translation)
            verses = data.get("verses", [])
            selected = [v for v in verses if start_verse <=
                        v["number"] <= end_verse]
            if not selected:
                return f"Стихи {start_verse}-{end_verse} не найдены в {book} {chapter}"
            return "\n".join([f"<b>{chapter}:{v['number']}</b> {v['text']}" for v in selected])
        except Exception as e:
            return f"Ошибка при получении стихов: {e}"


# Кэш для ответов ИИ: ключ -> ответ
_gpt_explain_cache = {}


async def ask_gpt_explain(text: str) -> str:
    """
    Отправляет запрос к OpenRouter (OpenAI совместимый API) для объяснения стиха или главы.
    Кэширует ответы для одинаковых запросов.
    """
    cache_key = text.strip().lower()
    if cache_key in _gpt_explain_cache:
        return _gpt_explain_cache[cache_key]

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": LLM_ROLE},
            {"role": "user", "content": text}
        ],
        "max_tokens": DEFAULT_MAX_TOKENS,
        "temperature": 0.7
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            data = await resp.json()
            if 'LOG_OPENROUTER_RESPONSE' in globals() and LOG_OPENROUTER_RESPONSE:
                logger.error(f"OpenRouter API raw response: {data}")
            try:
                result = data["choices"][0]["message"]["content"].strip()

                # Ограничиваем длину ответа для обычного ИИ
                if len(result) > AI_REGULAR_MAX_CHARS:
                    result = result[:AI_REGULAR_MAX_CHARS-3] + "..."

                _gpt_explain_cache[cache_key] = result
                return result
            except Exception:
                return "Извините, не удалось получить объяснение от ИИ. Попробуйте позже."


async def ask_gpt_explain_premium(text: str, max_tokens: int = PREMIUM_MAX_TOKENS_FULL) -> str:
    """
    Отправляет запрос к премиум OpenRouter API для более подробного объяснения стиха или главы.
    Использует более продвинутую модель и расширенную роль.

    Args:
        text: Текст для объяснения
        max_tokens: Максимальное количество токенов в ответе
    """
    cache_key = f"premium_{max_tokens}_{text.strip().lower()}"  # Учитываем max_tokens в кэше
    if cache_key in _gpt_explain_cache:
        return _gpt_explain_cache[cache_key]

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_PREMIUM_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": OPENROUTER_PREMIUM_MODEL,
        "messages": [
            {"role": "system", "content": LLM_PREMIUM_ROLE},
            {"role": "user", "content": text}
        ],
        "max_tokens": max_tokens,
        "temperature": 0.6   # Немного меньше температура для более точных ответов
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                data = await resp.json()
                if LOG_OPENROUTER_RESPONSE:
                    logger.info(f"Premium OpenRouter API response: {data}")

                result = data["choices"][0]["message"]["content"].strip()

                # Ограничиваем длину ответа для премиум ИИ
                if len(result) > AI_PREMIUM_MAX_CHARS:
                    result = result[:AI_PREMIUM_MAX_CHARS-3] + "..."

                _gpt_explain_cache[cache_key] = result
                return result

    except Exception as e:
        logger.error(f"Ошибка премиум ИИ запроса: {e}")
        return "Извините, не удалось получить объяснение от премиум ИИ помощника. Попробуйте позже."


async def ask_gpt_bible_verses(problem_text: str) -> str:
    """
    Отправляет запрос к OpenRouter для подбора библейских стихов по проблеме пользователя.
    """
    cache_key = f"verses_{problem_text.strip().lower()}"
    if cache_key in _gpt_explain_cache:
        return _gpt_explain_cache[cache_key]

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    system_prompt = (
        "Вы — православный богослов и библейский консультант. "
        "Ваша задача — подобрать 3-5 наиболее подходящих библейских отрывков, "
        "которые помогают в переживании и преодолении описанной проблемы или ситуации. "
        "Отвечайте ТОЛЬКО списком ссылок на стихи в формате 'Книга глава:стих-стих', "
        "разделенных точкой с запятой. "
        "Используйте русские сокращения книг: Быт, Исх, Лев, Чис, Втор, Нав, Суд, Руф, "
        "1Цар, 2Цар, 3Цар, 4Цар, 1Пар, 2Пар, Езд, Неем, Есф, Иов, Пс, Прит, Еккл, Песн, "
        "Ис, Иер, Плач, Иез, Дан, Ос, Иоил, Ам, Авд, Ион, Мих, Наум, Авв, Соф, Агг, Зах, Мал, "
        "Мф, Мк, Лк, Ин, Деян, Рим, 1Кор, 2Кор, Гал, Еф, Флп, Кол, 1Фес, 2Фес, 1Тим, 2Тим, "
        "Тит, Флм, Евр, Иак, 1Пет, 2Пет, 1Ин, 2Ин, 3Ин, Иуд, Откр. "
        "Пример ответа: 'Мф 6:25-34; Флп 4:6-7; 1Пет 5:7; Пс 22:1-6; Ис 41:10'"
    )

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Проблема: {problem_text}"}
        ],
        "max_tokens": 200,
        "temperature": 0.3
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            data = await resp.json()
            if 'LOG_OPENROUTER_RESPONSE' in globals() and LOG_OPENROUTER_RESPONSE:
                logger.error(f"OpenRouter API raw response: {data}")
            try:
                result = data["choices"][0]["message"]["content"].strip()
                _gpt_explain_cache[cache_key] = result
                return result
            except Exception:
                return "Извините, не удалось получить рекомендации от ИИ. Попробуйте позже."


# Создаем глобальный экземпляр клиента для использования в других модулях
bible_api = BibleAPIClient()
