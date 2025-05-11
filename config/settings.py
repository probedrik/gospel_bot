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
