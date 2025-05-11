"""
Клиент для работы с API Библии.
"""
import logging
import aiohttp
import time
from typing import Dict, Any, Optional

from config.settings import API_URL, API_TIMEOUT, CACHE_TTL

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
        try:
            data = await self.get_chapter(book, chapter, translation)

            # Формируем текст главы
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


# Создаем глобальный экземпляр клиента для использования в других модулях
bible_api = BibleAPIClient()
