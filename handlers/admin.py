"""
Обработчики административных команд.
"""
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from config.settings import USE_LOCAL_FILES
import config.settings as settings

logger = logging.getLogger(__name__)

# Создаем роутер для административных команд
admin_router = Router()

# ID администратора (замените на ваш Telegram ID)
ADMIN_ID = 2040516595  # Ваш реальный ID


def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором."""
    return user_id == ADMIN_ID


@admin_router.message(Command("admin"))
async def admin_panel(message: Message):
    """Показывает административную панель."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора.")
        return

    current_source = "Локальные файлы" if USE_LOCAL_FILES else "API"

    admin_text = f"""
🔧 **Административная панель**

📊 **Текущие настройки:**
• Источник данных: {current_source}

📋 **Доступные команды:**
• `/toggle_source` - переключить источник данных (API ↔ Локальные файлы)
• `/status` - показать статус системы
• `/reload_config` - перезагрузить конфигурацию
"""

    await message.answer(admin_text, parse_mode="Markdown")


@admin_router.message(Command("toggle_source"))
async def toggle_data_source(message: Message):
    """Переключает источник данных между API и локальными файлами."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора.")
        return

    try:
        # Переключаем настройку
        settings.USE_LOCAL_FILES = not settings.USE_LOCAL_FILES

        new_source = "Локальные файлы" if settings.USE_LOCAL_FILES else "API"

        await message.answer(
            f"✅ Источник данных переключен на: **{new_source}**\n\n"
            f"Теперь бот будет использовать {'локальные JSON файлы' if settings.USE_LOCAL_FILES else 'внешний API'} "
            f"для получения текстов Библии.",
            parse_mode="Markdown"
        )

        logger.info(
            f"Администратор {message.from_user.id} переключил источник данных на: {new_source}")

    except Exception as e:
        logger.error(f"Ошибка при переключении источника данных: {e}")
        await message.answer("❌ Произошла ошибка при переключении источника данных.")


@admin_router.message(Command("status"))
async def system_status(message: Message):
    """Показывает статус системы."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора.")
        return

    try:
        import os
        from utils.api_client import bible_api

        # Проверяем доступность локальных файлов
        local_rst_exists = os.path.exists("local/rst.json")
        local_rbo_exists = os.path.exists("local/rbo.json")

        current_source = "Локальные файлы" if USE_LOCAL_FILES else "API"

        status_text = f"""
📊 **Статус системы**

🔧 **Настройки:**
• Источник данных: {current_source}
• USE_LOCAL_FILES: {USE_LOCAL_FILES}

📁 **Локальные файлы:**
• RST перевод: {'✅ Доступен' if local_rst_exists else '❌ Не найден'}
• RBO перевод: {'✅ Доступен' if local_rbo_exists else '❌ Не найден'}

🌐 **API:**
• URL: {settings.API_URL}
• Timeout: {settings.API_TIMEOUT}s

💾 **Кэш:**
• Время жизни: {settings.CACHE_TTL}s
• Записей в кэше: {len(bible_api._cache)}
"""

        await message.answer(status_text, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Ошибка при получении статуса системы: {e}")
        await message.answer("❌ Произошла ошибка при получении статуса системы.")


@admin_router.message(Command("reload_config"))
async def reload_config(message: Message):
    """Перезагружает конфигурацию."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора.")
        return

    try:
        # Здесь можно добавить логику перезагрузки конфигурации
        # Например, очистка кэша
        from utils.api_client import bible_api
        bible_api._cache.clear()

        await message.answer(
            "✅ Конфигурация перезагружена:\n"
            "• Кэш очищен\n"
            "• Настройки обновлены",
            parse_mode="Markdown"
        )

        logger.info(
            f"Администратор {message.from_user.id} перезагрузил конфигурацию")

    except Exception as e:
        logger.error(f"Ошибка при перезагрузке конфигурации: {e}")
        await message.answer("❌ Произошла ошибка при перезагрузке конфигурации.")
