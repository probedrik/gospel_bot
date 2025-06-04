"""
Конфигурационные параметры бота.
"""
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Основные настройки бота
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Не задан токен бота в переменных окружения")

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

# Константы для логирования
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Глобальный параметр по умолчанию для удаления связанных сообщений
ENABLE_DELETE_RELATED_MESSAGES_DEFAULT = False

# --- НАСТРОЙКИ ФОРМАТИРОВАНИЯ ---
MARKDOWN_ENABLED = True  # Включить форматирование MarkdownV2 для толкований и ИИ
MARKDOWN_MODE = "MarkdownV2"  # Режим: Markdown, MarkdownV2, HTML
MARKDOWN_BOLD_TITLE = True  # Делать заголовки жирными
MARKDOWN_QUOTE = True  # Выводить текст как цитату (>)
MARKDOWN_ESCAPE = True  # Экранировать спецсимволы для MarkdownV2
