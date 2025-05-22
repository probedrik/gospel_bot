"""
Middleware для передачи объекта базы данных в обработчики
"""
import logging
import os
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from database.db_manager import db_manager

# Инициализация логгера
logger = logging.getLogger(__name__)


class DatabaseMiddleware(BaseMiddleware):
    """Middleware для автоматической передачи объекта базы данных в обработчики"""

    def __init__(self):
        super().__init__()
        # При инициализации проверяем доступность БД
        self._check_db()

    def _check_db(self):
        """Проверяет доступность БД и выводит информацию о ней"""
        try:
            db_file = db_manager.db_file
            db_dir = os.path.dirname(db_file)

            # Проверяем директорию
            dir_exists = os.path.exists(db_dir)
            if not dir_exists:
                logger.warning(f"Директория для БД не существует: {db_dir}")
                try:
                    os.makedirs(db_dir, exist_ok=True)
                    logger.info(f"Создана директория для БД: {db_dir}")
                except Exception as e:
                    logger.error(f"Ошибка при создании директории для БД: {e}")

            # Проверяем файл БД
            file_exists = os.path.exists(db_file)
            size = os.path.getsize(db_file) if file_exists else 0

            # Проверяем доступ к файлу
            access_ok = False
            if file_exists:
                try:
                    with open(db_file, 'a') as f:
                        pass
                    access_ok = True
                except Exception as e:
                    logger.error(f"Нет доступа к файлу БД: {e}")

            # Выводим информацию о БД
            logger.info(
                f"БД {db_file}: {'существует' if file_exists else 'не существует'}, " +
                f"размер: {size} байт, доступ: {'ОК' if access_ok else 'ОШИБКА'}")

            # Принудительно создаем таблицы если БД существует
            if file_exists and access_ok:
                db_manager._create_tables()

        except Exception as e:
            logger.error(f"Ошибка при проверке БД: {e}", exc_info=True)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """
        Этот метод вызывается для каждого обработчика событий.
        Он добавляет объект db_manager в данные, переданные обработчику.

        Args:
            handler: Обработчик события
            event: Объект события Telegram
            data: Словарь с данными обработчика

        Returns:
            Результат выполнения обработчика
        """
        # Проверяем тип события
        event_type = event.__class__.__name__

        # Для Message и CallbackQuery логируем ID пользователя
        user_id = None
        if hasattr(event, 'from_user') and event.from_user:
            user_id = event.from_user.id

        # Убеждаемся, что объект БД доступен и файл существует
        if not hasattr(db_manager, 'db_file'):
            logger.error(
                "Ошибка: объект db_manager не содержит атрибута db_file")
        elif not os.path.exists(db_manager.db_file):
            logger.error(
                f"Ошибка: файл БД не существует: {db_manager.db_file}")
            # Принудительно создаем таблицы
            try:
                db_manager._create_tables()
                logger.info("Принудительно вызвано создание таблиц в БД")
            except Exception as e:
                logger.error(f"Ошибка при принудительном создании таблиц: {e}")

        # Добавляем объект db в данные обработчика
        data["db"] = db_manager

        # Проверяем, что объект действительно передан
        if "db" not in data or data["db"] is None:
            logger.error("Критическая ошибка: объект БД не добавлен в data")
            # Экстренное добавление объекта
            data["db"] = db_manager

        # ГАРАНТИЯРОВАННО добавляем пользователя в БД для любого апдейта с user_id
        if user_id:
            try:
                username = None
                first_name = None
                if hasattr(event, 'from_user'):
                    username = event.from_user.username
                    first_name = event.from_user.first_name
                await db_manager.add_user(user_id, username or "", first_name or "")
            except Exception as e:
                logger.error(
                    f"Ошибка при добавлении пользователя {user_id} в БД: {e}", exc_info=True)
        else:
            logger.debug(
                f"Объект db_manager добавлен в обработчик для события {event_type}")

        # Вызываем следующий обработчик в цепочке
        try:
            return await handler(event, data)
        except Exception as e:
            logger.error(
                f"Ошибка в обработчике после db_middleware: {e}", exc_info=True)
            raise
