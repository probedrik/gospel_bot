"""
Конфигурационные параметры бота.
"""
import os
import logging
from dotenv import load_dotenv

# Настройка логирования для конфигурации
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загружаем переменные окружения из .env файла
env_loaded = load_dotenv()
if env_loaded:
    logger.info("✅ .env файл найден и загружен")
else:
    logger.warning(
        "⚠️ .env файл не найден, используются системные переменные окружения")

# Основные настройки бота
# Проверяем, что именно находится в переменных окружения
env_bot_token = os.environ.get("BOT_TOKEN")
if env_bot_token:
    env_masked = env_bot_token[:8] + "..." + \
        env_bot_token[-6:] if len(env_bot_token) > 10 else "***скрыт***"
    logger.info(f"🔍 В системных переменных найден BOT_TOKEN: {env_masked}")

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("❌ Токен бота не найден в переменных окружения!")
    raise ValueError("Не задан токен бота в переменных окружения")

# Логируем информацию о токене (маскированную для безопасности)
if len(BOT_TOKEN) > 10:
    masked_token = BOT_TOKEN[:8] + "..." + BOT_TOKEN[-6:]
else:
    masked_token = "***скрыт***"

logger.info(f"🔑 Токен бота загружен: {masked_token}")
logger.info(
    f"📍 Источник токена: {'файл .env' if env_loaded else 'системные переменные окружения'}")

# Проверяем правильность формата .env файла
if env_loaded:
    try:
        with open('.env', 'r', encoding='utf-8') as f:
            env_content = f.read()
        if 'BOT_TOKEN =' in env_content:
            logger.warning(
                "⚠️ ВНИМАНИЕ: В .env файле используется неправильный формат с пробелами!")
            logger.warning(
                "⚠️ Измените 'BOT_TOKEN = \"токен\"' на 'BOT_TOKEN=токен' (без пробелов и кавычек)")
        elif 'BOT_TOKEN=' in env_content:
            logger.info("✅ Формат .env файла корректный")
    except Exception as e:
        logger.warning(f"⚠️ Не удалось проверить формат .env файла: {e}")

# Пути к данным
DATA_PATH = "./data"
EXCEL_FILES = {
    "books": "./file.xlsx",
    "reading_plan": "./plan.xlsx"
}

# Настройки API
API_URL = "https://justbible.ru/api"
API_TIMEOUT = 10  # секунды

# Настройки источника данных Библии
# True - использовать локальные JSON файлы, False - использовать API
USE_LOCAL_FILES = True
LOCAL_FILES_PATH = "./local"  # путь к папке с локальными JSON файлами

# Параметры сообщений Telegram
MESS_MAX_LENGTH = 4096  # максимальная длина сообщения

# Доступные переводы Библии
AVAILABLE_TRANSLATIONS = {
    "rst": "Синодальный перевод",
    "rbo": "Современный перевод РБО"
}

# Интервалы для кэширования
CACHE_TTL = 3600  # время жизни кэша в секундах

# Настройки функций
ENABLE_WORD_SEARCH = False  # Включить/отключить функцию поиска по слову
ENABLE_VERSE_NUMBERS = True  # Включить/отключить вывод с номерами стихов
# Включить/отключить толкования Лопухина глобально
ENABLE_LOPUKHIN_COMMENTARY = False

# Константы для логирования
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Глобальный параметр по умолчанию для удаления связанных сообщений
ENABLE_DELETE_RELATED_MESSAGES_DEFAULT = False

# --- НАСТРОЙКИ ФОРМАТИРОВАНИЯ ---

# Форматирование текста Библии с номерами стихов
BIBLE_MARKDOWN_ENABLED = False  # Использовать Markdown для текста Библии
BIBLE_MARKDOWN_MODE = "HTML"  # HTML, Markdown, MarkdownV2
# Выводить библейский текст как цитату (blockquote)
BIBLE_QUOTE_ENABLED = False
# Количество пробелов после номера стиха (1, 2, 3 и т.д.)
BIBLE_VERSE_NUMBER_SPACING = 2
# Включать номер главы перед номером стиха (2:12 вместо 12)
BIBLE_INCLUDE_CHAPTER_NUMBER = True
# Стиль форматирования номеров стихов: bold, code, italic
BIBLE_VERSE_NUMBER_STYLE = "code"

# Форматирование толкований и ИИ-ответов
COMMENTARY_MARKDOWN_ENABLED = True  # Включить форматирование для толкований и ИИ
COMMENTARY_MARKDOWN_MODE = "HTML"  # Режим: HTML, Markdown, MarkdownV2

# Остальные настройки форматирования (для обратной совместимости)
MARKDOWN_ENABLED = True  # Включить форматирование MarkdownV2 для толкований и ИИ
MARKDOWN_MODE = "MarkdownV2"  # Режим: Markdown, MarkdownV2, HTML
MARKDOWN_BOLD_TITLE = True  # Делать заголовки жирными
MARKDOWN_QUOTE = True  # Выводить текст как цитату (blockquote)
MARKDOWN_ESCAPE = True  # Экранировать спецсимволы для MarkdownV2
