"""
Клиент для работы с API Библии.
"""
import logging
import aiohttp
import time
from typing import Dict, Any, Optional

from config.settings import API_URL, API_TIMEOUT, CACHE_TTL, USE_LOCAL_FILES
from config.ai_settings import ENABLE_GPT_EXPLAIN, OPENROUTER_API_KEY, OPENROUTER_MODEL, LLM_ROLE
# Добавляем флаг для логирования OpenRouter API
try:
    from config.ai_settings import LOG_OPENROUTER_RESPONSE
except ImportError:
    LOG_OPENROUTER_RESPONSE = False

# Инициализация логгера
logger = logging.getLogger(__name__)


class BibleAPIClient:
    """Класс для работы с API Библии с поддержкой кэширования и локальных файлов."""

    def __init__(self):
        self._session = None
        # Простой кэш в памяти: ключ -> (значение, время_истечения)
        self._cache = {}
        # Импортируем локальный сервис только при необходимости
        self._local_service = None

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

    def _get_local_service(self):
        """Получает экземпляр локального сервиса (ленивая инициализация)."""
        if self._local_service is None:
            from services.local_bible import local_bible_service
            self._local_service = local_bible_service
        return self._local_service

    async def get_chapter(
        self, book: int, chapter: int, translation: str = "rst"
    ) -> Dict[str, Any]:
        """
        Получает текст главы из API или локальных файлов.

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

        # Используем локальные файлы, если включено в настройках
        if USE_LOCAL_FILES:
            logger.debug(
                f"Используем локальные файлы для получения главы {book}:{chapter}")
            local_service = self._get_local_service()
            return await local_service.get_chapter(book, chapter, translation)

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

        # Используем локальные файлы, если включено в настройках
        if USE_LOCAL_FILES:
            logger.debug(
                f"Используем локальные файлы для получения отформатированной главы {book}:{chapter}")
            local_service = self._get_local_service()
            return await local_service.get_formatted_chapter(book, chapter, translation)

        try:
            data = await self.get_chapter(book, chapter, translation)
            # Проверка наличия ключа 'info' и нужных данных
            if not data or 'info' not in data or 'book' not in data['info']:
                logger.error(
                    f"Некорректный ответ от API (нет 'info' или 'book'): {data}")
                return "Ошибка: не удалось получить текст главы. Попробуйте позже."
            verses = [v for k, v in data.items() if k != "info"]
            testament = "Ветхий завет" if book < 40 else "Новый завет"
            return f"{testament}. {data['info']['book']} {chapter}:\n{' '.join(verses)}"
        except Exception as e:
            logger.error(f"Ошибка при получении текста главы: {e}")
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
        Поиск слова или фразы в тексте Библии через API или локальные файлы.

        Args:
            search_query: Поисковый запрос
            translation: Код перевода (rst, rbo)

        Returns:
            Список найденных результатов
        """
        if len(search_query) < 3:
            logger.warning("Слишком короткий поисковый запрос")
            return []

        # Используем локальные файлы, если включено в настройках
        if USE_LOCAL_FILES:
            logger.debug(
                f"Используем локальные файлы для поиска '{search_query}'")
            local_service = self._get_local_service()
            return await local_service.search_bible_text(search_query, translation)

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
        Получает текст одного стиха или диапазона стихов из главы.
        verse_range: int (один стих) или (start, end) для диапазона
        """
        # Приведение типов для book и chapter
        try:
            book = int(book)
            chapter = int(chapter)
        except Exception as e:
            logger.error(f"Некорректные типы для book или chapter: {e}")
            return f"Ошибка: некорректные параметры главы (book/chapter)"

        # Используем локальные файлы, если включено в настройках
        if USE_LOCAL_FILES:
            logger.debug(
                f"Используем локальные файлы для получения стихов {book}:{chapter}")
            local_service = self._get_local_service()
            return await local_service.get_verses(book, chapter, verse_range, translation)

        try:
            data = await self.get_chapter(book, chapter, translation)
            verses = [v for k, v in data.items() if k != "info"]
            if isinstance(verse_range, tuple):
                start, end = verse_range
                selected = verses[start-1:end]
                verses_text = ' '.join(selected)
                ref = f"{data['info']['book']} {chapter}:{start}-{end}"
            else:
                selected = verses[verse_range-1:verse_range]
                verses_text = ' '.join(selected)
                ref = f"{data['info']['book']} {chapter}:{verse_range}"
            testament = "Ветхий завет" if book < 40 else "Новый завет"
            return f"{testament}. {ref}:\n{verses_text}"
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

    async def get_verse_by_reference(self, reference: str, translation: str = "rst") -> str:
        """
        Получает текст по библейской ссылке (например, "Мф 5:3-12" или "Ин 3:16")

        Args:
            reference: Библейская ссылка
            translation: Код перевода (rst, rbo)

        Returns:
            Отформатированный текст
        """
        # Используем локальные файлы, если включено в настройках
        if USE_LOCAL_FILES:
            logger.debug(
                f"Используем локальные файлы для получения ссылки '{reference}'")
            local_service = self._get_local_service()
            return await local_service.get_verse_by_reference(reference, translation)

        try:
            from utils.bible_data import bible_data

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
                f"Ошибка при получении текста по ссылке {reference}: {e}")
            return f"Ошибка при получении текста: {reference}"


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
        "max_tokens": 2048,
        "temperature": 0.7
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
                return "Извините, не удалось получить объяснение от ИИ. Попробуйте позже."


# Создаем глобальный экземпляр клиента для использования в других модулях
bible_api = BibleAPIClient()
