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
    commands, text_messages, callbacks, bookmarks, bookmark_callbacks, reading_plans, admin, ai_assistant
)
from middleware.state import StateMiddleware
from middleware.db_middleware import DatabaseMiddleware
from database.universal_manager import universal_db_manager as db_manager

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
        # Асинхронная инициализация универсального менеджера БД
        await db_manager.initialize()

        # Логируем тип базы данных
        if db_manager.is_supabase:
            db_type = "Supabase"
        elif db_manager.is_postgres:
            db_type = "PostgreSQL"
        else:
            db_type = "SQLite"
        logger.info(f"🗄️ Используется база данных: {db_type}")

        # Для SQLite проверяем права доступа
        if not db_manager.is_postgres and not db_manager.is_supabase:
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
                f"✅ Инициализация БД успешна, тестовый пользователь получен: {test_user}")
        else:
            logger.error(
                "❌ Ошибка: тестовый пользователь не найден после добавления")

    except Exception as e:
        logger.error(
            f"❌ Критическая ошибка при инициализации БД: {e}", exc_info=True)
        logger.warning("⚠️ Бот будет работать без сохранения данных в БД!")

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
        if db_manager.is_supabase:
            logger.info("Тестовое соединение с Supabase успешно")
        elif db_manager.is_postgres:
            logger.info("Тестовое соединение с PostgreSQL успешно")
        else:
            logger.info(
                f"Тестовое соединение с БД успешно: {db_manager.db_file}")
    except Exception as e:
        logger.error(f"Ошибка при соединении с БД: {e}", exc_info=True)

    # Сохраняем экземпляр БД в контексте диспетчера
    dp["db"] = db_manager
    if db_manager.is_supabase:
        logger.info("Объект Supabase БД добавлен в контекст диспетчера")
    elif db_manager.is_postgres:
        logger.info("Объект PostgreSQL БД добавлен в контекст диспетчера")
    else:
        logger.info(
            f"Объект БД добавлен в контекст диспетчера: {db_manager.db_file}")

    # Регистрируем middleware
    dp.update.middleware(StateMiddleware())
    dp.update.middleware(DatabaseMiddleware())
    logger.info("Middleware для передачи объекта БД зарегистрирован")

    # Регистрируем роутеры с обработчиками
    dp.include_router(admin.admin_router)  # Административные команды первыми
    dp.include_router(commands.router)

    # Новые обработчики закладок (ВАЖНО: регистрируем ДО старых!)
    from handlers import bookmarks_new, bookmark_handlers
    dp.include_router(bookmarks_new.router)
    dp.include_router(bookmark_handlers.router)

    dp.include_router(text_messages.router)
    dp.include_router(callbacks.router)
    dp.include_router(bookmarks.router)  # Старый обработчик закладок
    dp.include_router(bookmark_callbacks.router)
    dp.include_router(reading_plans.router)
    dp.include_router(ai_assistant.router)  # ИИ помощник

    # Календарь
    from handlers import calendar as calendar_handler
    dp.include_router(calendar_handler.router)

    # Платежи через Telegram Stars
    from handlers import payments
    dp.include_router(payments.router)
    
    # Настройки (включают обработчики платежей) - регистрируем в конце
    from handlers import settings as settings_handler
    dp.include_router(settings_handler.router)

    # Запускаем планировщик квот ИИ
    try:
        from services.ai_quota_manager import ai_quota_manager
        await ai_quota_manager.start_quota_reset_scheduler()
        logger.info("✅ Планировщик квот ИИ запущен")
    except Exception as e:
        logger.error("❌ Ошибка запуска планировщика квот: %s",
                     e, exc_info=True)

    # Запускаем бота
    try:
        logger.info("Бот запущен")
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error("Ошибка при запуске бота: %s", e, exc_info=True)
    finally:
        logger.info("Бот остановлен")

        # Останавливаем планировщик квот
        try:
            from services.ai_quota_manager import ai_quota_manager
            await ai_quota_manager.stop_quota_reset_scheduler()
            logger.info("✅ Планировщик квот остановлен")
        except Exception as e:
            logger.error(
                "❌ Ошибка остановки планировщика квот: %s", e, exc_info=True)

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
