"""
Модуль для работы с библейскими темами.
Теперь использует Supabase вместо CSV файла.
"""

import asyncio
import logging
from typing import List, Dict, Optional
from pathlib import Path

# Fallback к CSV если Supabase недоступен
FALLBACK_CSV = Path(__file__).parent.parent / "bible_verses_by_topic_fixed.csv"

logger = logging.getLogger(__name__)

# Кэш тем для ускорения работы
_topics_cache = None
_cache_timestamp = 0


async def load_topics_from_supabase() -> List[Dict]:
    """Загружает темы из Supabase"""
    try:
        from database.universal_manager import universal_db_manager

        # Получаем все темы из Supabase
        topics_data = await universal_db_manager.get_bible_topics(limit=100)

        if not topics_data:
            logger.warning("Нет тем в Supabase, используем fallback к CSV")
            return load_topics_from_csv()

        # Конвертируем в нужный формат
        topics = []
        for topic_data in topics_data:
            topic_name = topic_data.get('topic_name', '')
            verses_str = topic_data.get('verses', '')

            # Разбиваем строку стихов на список
            verses = [v.strip() for v in verses_str.split(';') if v.strip()]

            topics.append({
                "topic": topic_name,
                "verses": verses,
                "id": topic_data.get('id')
            })

        logger.info(f"Загружено {len(topics)} тем из Supabase")
        return topics

    except Exception as e:
        logger.error(f"Ошибка загрузки тем из Supabase: {e}")
        logger.info("Переключаемся на fallback CSV")
        return load_topics_from_csv()


def load_topics_from_csv() -> List[Dict]:
    """Fallback: загружает темы из CSV файла"""
    try:
        import csv

        topics = []
        csv_file = FALLBACK_CSV if FALLBACK_CSV.exists() else Path(
            __file__).parent.parent / "bible_verses_by_topic.csv"

        with open(csv_file, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                topic = row["Тема"].strip()
                verses = [v.strip()
                          for v in row["Стихи"].split(";") if v.strip()]
                topics.append({"topic": topic, "verses": verses})

        logger.info(f"Загружено {len(topics)} тем из CSV (fallback)")
        return topics

    except Exception as e:
        logger.error(f"Ошибка загрузки тем из CSV: {e}")
        return []


def load_topics() -> List[Dict]:
    """Загружает темы (синхронная обёртка для async функции)"""
    global _topics_cache, _cache_timestamp

    import time
    current_time = time.time()

    # Кэш действует 5 минут
    if _topics_cache and (current_time - _cache_timestamp) < 300:
        return _topics_cache

    try:
        # Пытаемся загрузить из Supabase
        loop = asyncio.get_event_loop()
        topics = loop.run_until_complete(load_topics_from_supabase())
    except RuntimeError:
        # Если нет активного event loop, создаем новый
        topics = asyncio.run(load_topics_from_supabase())
    except Exception as e:
        logger.error(f"Ошибка при загрузке тем: {e}")
        # Последний fallback к CSV
        topics = load_topics_from_csv()

    # Обновляем кэш
    _topics_cache = topics
    _cache_timestamp = current_time

    return topics


def get_topics_list() -> List[str]:
    """Возвращает список названий тем"""
    topics = load_topics()
    return [t["topic"] for t in topics]


def get_verses_for_topic(topic_name: str) -> List[str]:
    """Возвращает список стихов для указанной темы"""
    topics = load_topics()
    for topic_data in topics:
        if topic_data["topic"] == topic_name:
            return topic_data["verses"]
    return []


async def search_topics(query: str, limit: int = 20) -> List[Dict]:
    """Поиск тем по запросу (асинхронная функция для продвинутого поиска)"""
    try:
        from database.universal_manager import universal_db_manager

        # Пытаемся использовать полнотекстовый поиск
        topics_data = await universal_db_manager.search_topics_fulltext(query, limit)

        if not topics_data:
            # Fallback к обычному поиску
            topics_data = await universal_db_manager.get_bible_topics(query, limit)

        # Конвертируем в нужный формат
        topics = []
        for topic_data in topics_data:
            topic_name = topic_data.get('topic_name', '')
            verses_str = topic_data.get('verses', '')
            verses = [v.strip() for v in verses_str.split(';') if v.strip()]

            topics.append({
                "topic": topic_name,
                "verses": verses,
                "id": topic_data.get('id')
            })

        return topics

    except Exception as e:
        logger.error(f"Ошибка поиска тем: {e}")
        return []


def clear_cache():
    """Очищает кэш тем (для принудительного обновления)"""
    global _topics_cache, _cache_timestamp
    _topics_cache = None
    _cache_timestamp = 0


# Для обратной совместимости (если где-то используются старые импорты)
def get_topic_verses(topic_name: str) -> List[str]:
    """Алиас для get_verses_for_topic"""
    return get_verses_for_topic(topic_name)
