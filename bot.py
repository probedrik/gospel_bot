"""
Главный файл бота для чтения Библии.
"""
import asyncio
import logging
import sys
from datetime import datetime
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums.parse_mode import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext

from config import settings
from handlers import (
    commands, text_messages, callbacks, bookmarks, bookmark_callbacks, reading_plans, admin
)
from middleware.state import StateMiddleware
from middleware.db_middleware import DatabaseMiddleware
from database.db_manager import db_manager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

# Получаем логгер для текущего файла
logger = logging.getLogger(__name__)


async def main() -> None:
    """
    Основная функция запуска бота.
    """
    # Логируем начало работы
    logger.info("Запуск бота: %s", datetime.now())

    # Проверяем и инициализируем БД
    try:
        # Форсируем пересоздание таблиц, если есть проблемы с БД
        db_file = db_manager.db_file
        db_dir = os.path.dirname(db_file)

        # Убедимся, что директория существует
        os.makedirs(db_dir, exist_ok=True)

        # Проверяем права доступа
        try:
            with open(db_file, 'a') as f:
                pass
        except Exception as e:
            logger.error(f"Ошибка доступа к файлу БД: {e}")

        # Явно вызываем метод создания таблиц
        db_manager._create_tables()

        # Тестируем БД путем добавления временного пользователя
        await db_manager.add_user(123456, "test_user", "Test")
        test_user = await db_manager.get_user(123456)

        if test_user:
            logger.info(
                f"Инициализация БД успешна, тестовый пользователь получен: {test_user}")
        else:
            logger.error(
                "Ошибка: тестовый пользователь не найден после добавления")

    except Exception as e:
        logger.error(
            f"Критическая ошибка при инициализации БД: {e}", exc_info=True)
        logger.warning("Бот будет работать без сохранения данных в БД!")

    # Инициализируем хранилище состояний
    storage = MemoryStorage()

    # Инициализируем бота и диспетчер с использованием новой схемы DefaultBotProperties
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=storage)

    # Проверяем работу БД перед использованием
    try:
        # Тестовое соединение с БД
        test_db = await db_manager.get_user(1)
        logger.info(f"Тестовое соединение с БД успешно: {db_manager.db_file}")
    except Exception as e:
        logger.error(f"Ошибка при соединении с БД: {e}", exc_info=True)

    # Сохраняем экземпляр БД в контексте диспетчера
    dp["db"] = db_manager
    logger.info(
        f"Объект БД добавлен в контекст диспетчера: {db_manager.db_file}")

    # Регистрируем middleware
    dp.update.middleware(StateMiddleware())
    dp.update.middleware(DatabaseMiddleware())
    logger.info("Middleware для передачи объекта БД зарегистрирован")

    # Регистрируем роутеры с обработчиками
    dp.include_router(admin.admin_router)  # Административные команды первыми
    dp.include_router(commands.router)
    dp.include_router(text_messages.router)
    dp.include_router(callbacks.router)
    dp.include_router(bookmarks.router)
    dp.include_router(bookmark_callbacks.router)
    dp.include_router(reading_plans.router)

    # Запускаем бота
    try:
        logger.info("Бот запущен")
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error("Ошибка при запуске бота: %s", e, exc_info=True)
    finally:
        logger.info("Бот остановлен")
        # Закрываем соединения с базой данных
        await db_manager.close()
        logger.info("Завершение работы")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен по команде пользователя")
    except Exception as e:
        logger.error("Необработанная ошибка: %s", e, exc_info=True)
