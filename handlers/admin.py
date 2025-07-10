"""
Обработчики административных команд.
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
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

    bible_format = "HTML"
    if settings.ENABLE_VERSE_NUMBERS and settings.BIBLE_MARKDOWN_ENABLED:
        bible_format = settings.BIBLE_MARKDOWN_MODE
    elif settings.ENABLE_VERSE_NUMBERS:
        bible_format = "HTML"
    else:
        bible_format = "Н/Д"

    commentary_format = "HTML"
    if settings.COMMENTARY_MARKDOWN_ENABLED:
        commentary_format = settings.COMMENTARY_MARKDOWN_MODE

    admin_text = f"""
🔧 **Административная панель**

📊 **Текущие настройки:**
• Источник данных: {current_source}
• Номера стихов: {"✅ Включены" if settings.ENABLE_VERSE_NUMBERS else "❌ Отключены"}
• Формат стихов: {bible_format}
• Цитата Библии: {"✅ Включена" if settings.BIBLE_QUOTE_ENABLED else "❌ Отключена"}
• Пробелов после номера: {settings.BIBLE_VERSE_NUMBER_SPACING}
• Формат номеров: {"глава:стих" if settings.BIBLE_INCLUDE_CHAPTER_NUMBER else "только стих"}
• Стиль номеров: {settings.BIBLE_VERSE_NUMBER_STYLE}
• Толкования Лопухина: {"✅ Включены" if settings.ENABLE_LOPUKHIN_COMMENTARY else "❌ Отключены"}
• Формат толкований: {commentary_format}

📋 **Доступные команды:**
• `/toggle_source` - переключить источник данных (API ↔ Локальные файлы)
• `/toggle_verses` - переключить номера стихов
• `/toggle_quote` - переключить режим цитат (>)
• `/toggle_chapter_numbers` - переключить формат номеров (12 ↔ 2:12)
• `/toggle_lopukhin` - включить/отключить толкования Лопухина
• `/set_format` - изменить формат стихов (HTML/Markdown/MarkdownV2)
• `/set_commentary_format` - изменить формат толкований
• `/set_spacing` - изменить количество пробелов после номера стиха
• `/settings` - показать все настройки
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


@admin_router.message(Command("toggle_verses"))
async def toggle_verse_numbers(message: Message):
    """Переключает режим отображения номеров стихов."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора.")
        return

    try:
        # Переключаем настройку
        settings.ENABLE_VERSE_NUMBERS = not settings.ENABLE_VERSE_NUMBERS

        status = "включены" if settings.ENABLE_VERSE_NUMBERS else "отключены"
        icon = "✅" if settings.ENABLE_VERSE_NUMBERS else "❌"

        format_example = ""
        if settings.ENABLE_VERSE_NUMBERS:
            format_example = "\n\n📖 **Пример нового формата:**\n<b>1</b> Текст первого стиха\n<b>2</b> Текст второго стиха\n..."
        else:
            format_example = "\n\n📖 **Пример обычного формата:**\nТекст первого стиха Текст второго стиха..."

        await message.answer(
            f"{icon} **Номера стихов {status}**\n\n"
            f"Теперь главы Библии будут отображаться "
            f"{'с номерами стихов (каждый стих с новой строки)' if settings.ENABLE_VERSE_NUMBERS else 'в обычном формате (сплошным текстом)'}."
            f"{format_example}",
            parse_mode="HTML"
        )

        logger.info(
            f"Администратор {message.from_user.id} {'включил' if settings.ENABLE_VERSE_NUMBERS else 'отключил'} номера стихов")

    except Exception as e:
        logger.error(f"Ошибка при переключении номеров стихов: {e}")
        await message.answer("❌ Произошла ошибка при переключении настройки.")


@admin_router.message(Command("toggle_quote"))
async def toggle_quote_mode(message: Message):
    """Переключает режим отображения библейского текста как цитаты."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора.")
        return

    try:
        # Переключаем настройку
        settings.BIBLE_QUOTE_ENABLED = not settings.BIBLE_QUOTE_ENABLED

        status = "включен" if settings.BIBLE_QUOTE_ENABLED else "отключен"
        icon = "✅" if settings.BIBLE_QUOTE_ENABLED else "❌"

        format_example = ""
        if settings.BIBLE_QUOTE_ENABLED:
            format_example = "\n\n📖 **Пример с цитатой:**\n<blockquote>Ветхий завет. Бытие 1:\nВ начале сотворил Бог небо и землю.\nЗемля же была безвидна и пуста...</blockquote>"
        else:
            format_example = "\n\n📖 **Пример обычного формата:**\nВетхий завет. Бытие 1:\nВ начале сотворил Бог небо и землю.\nЗемля же была безвидна и пуста..."

        await message.answer(
            f"{icon} **Режим цитат {status}**\n\n"
            f"Теперь библейский текст будет отображаться "
            f"{'как цитата (с символом > в начале строк)' if settings.BIBLE_QUOTE_ENABLED else 'в обычном формате'}."
            f"{format_example}",
            parse_mode="HTML"
        )

        logger.info(
            f"Администратор {message.from_user.id} {'включил' if settings.BIBLE_QUOTE_ENABLED else 'отключил'} режим цитат")

    except Exception as e:
        logger.error(f"Ошибка при переключении режима цитат: {e}")
        await message.answer("❌ Произошла ошибка при переключении настройки.")


@admin_router.message(Command("settings"))
async def show_settings(message: Message):
    """Показывает все настройки бота."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора.")
        return

    try:
        current_source = "Локальные файлы" if settings.USE_LOCAL_FILES else "API"

        verse_format = "Отключены"
        if settings.ENABLE_VERSE_NUMBERS:
            if settings.BIBLE_MARKDOWN_ENABLED:
                verse_format = settings.BIBLE_MARKDOWN_MODE
            else:
                verse_format = "HTML"

        commentary_format = "HTML"
        if settings.COMMENTARY_MARKDOWN_ENABLED:
            commentary_format = settings.COMMENTARY_MARKDOWN_MODE

        settings_text = f"""
⚙️ **Настройки бота:**

📊 **Основные:**
• Источник данных: {current_source}
• Поиск по слову: {"✅ Включен" if settings.ENABLE_WORD_SEARCH else "❌ Отключен"}
• Номера стихов: {"✅ Включены" if settings.ENABLE_VERSE_NUMBERS else "❌ Отключены"}

📝 **Форматирование текста Библии:**
• Формат стихов: {verse_format}
• Markdown включен: {"✅ Да" if settings.BIBLE_MARKDOWN_ENABLED else "❌ Нет"}
• Режим цитат: {"✅ Включен" if settings.BIBLE_QUOTE_ENABLED else "❌ Отключен"}
• Пробелов после номера: {settings.BIBLE_VERSE_NUMBER_SPACING}
• Формат номеров: {"глава:стих" if settings.BIBLE_INCLUDE_CHAPTER_NUMBER else "только стих"}
• Стиль номеров: {settings.BIBLE_VERSE_NUMBER_STYLE}

💬 **Форматирование толкований и ИИ:**
• Формат: {commentary_format}
• Markdown включен: {"✅ Да" if settings.COMMENTARY_MARKDOWN_ENABLED else "❌ Нет"}
• Жирные заголовки: {"✅ Да" if settings.MARKDOWN_BOLD_TITLE else "❌ Нет"}
• Цитаты: {"✅ Да" if settings.MARKDOWN_QUOTE else "❌ Нет"}

🔧 **Команды управления:**
• `/toggle_source` - переключить источник данных
• `/toggle_verses` - переключить номера стихов
• `/toggle_quote` - переключить режим цитат
• `/toggle_chapter_numbers` - переключить формат номеров стихов
• `/set_verse_style` - изменить стиль номеров стихов
• `/set_format` - изменить формат стихов
• `/set_commentary_format` - изменить формат толкований
• `/set_spacing` - изменить количество пробелов после номера стиха
• `/status` - статус системы
• `/reload_config` - перезагрузить конфигурацию
"""

        await message.answer(settings_text, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Ошибка при показе настроек: {e}")
        await message.answer("❌ Произошла ошибка при получении настроек.")


@admin_router.message(Command("set_format"))
async def set_format_command(message: Message):
    """Устанавливает формат номеров стихов (HTML, Markdown, MarkdownV2)"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора.")
        return

    try:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

        # Отправляем меню выбора формата
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="HTML", callback_data="format_HTML")],
            [InlineKeyboardButton(
                text="Markdown", callback_data="format_Markdown")],
            [InlineKeyboardButton(
                text="MarkdownV2", callback_data="format_MarkdownV2")],
        ])

        current_format = "HTML"
        if settings.BIBLE_MARKDOWN_ENABLED:
            current_format = settings.BIBLE_MARKDOWN_MODE

        await message.answer(
            f"📝 **Выберите формат для номеров стихов:**\n\n"
            f"Текущий формат: **{current_format}**\n\n"
            f"• **HTML** - Стандартный HTML формат (<b>номер</b> текст)\n"
            f"• **Markdown** - Базовый Markdown (**номер** текст)\n"
            f"• **MarkdownV2** - Расширенный Markdown (*номер* текст)",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"Ошибка при выборе формата: {e}")
        await message.answer("❌ Ошибка при изменении формата")


@admin_router.callback_query(F.data.startswith("format_"))
async def format_callback(callback: CallbackQuery):
    """Обработчик выбора формата"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора.")
        return

    try:
        format_name = callback.data.split("_")[1]

        if format_name == "HTML":
            settings.BIBLE_MARKDOWN_ENABLED = False
            settings.BIBLE_MARKDOWN_MODE = "HTML"
        elif format_name == "Markdown":
            settings.BIBLE_MARKDOWN_ENABLED = True
            settings.BIBLE_MARKDOWN_MODE = "Markdown"
        elif format_name == "MarkdownV2":
            settings.BIBLE_MARKDOWN_ENABLED = True
            settings.BIBLE_MARKDOWN_MODE = "MarkdownV2"

        # Определяем пример форматирования
        if format_name == "HTML":
            example = "<b>1</b> В начале сотворил Бог небо и землю.\n<b>2</b> Земля же была безвидна и пуста..."
        elif format_name == "Markdown":
            example = "**1** В начале сотворил Бог небо и землю.\n**2** Земля же была безвидна и пуста..."
        else:  # MarkdownV2
            example = "*1* В начале сотворил Бог небо и землю\\.\n*2* Земля же была безвидна и пуста\\.\\.\\."

        await callback.answer(f"✅ Формат изменен: {format_name}")
        await callback.message.edit_text(
            f"✅ **Формат номеров стихов изменен на: {format_name}**\n\n"
            f"📖 **Пример отображения:**\n{example}\n\n"
            f"🔄 Изменения применятся для всех новых сообщений с номерами стихов.",
            parse_mode="Markdown"
        )

        logger.info(
            f"Администратор {callback.from_user.id} изменил формат стихов на: {format_name}")

    except Exception as e:
        logger.error(f"Ошибка при установке формата: {e}")
        await callback.answer("❌ Ошибка при изменении формата")


@admin_router.message(Command("set_commentary_format"))
async def set_commentary_format_command(message: Message):
    """Устанавливает формат для толкований и ИИ-ответов (HTML, Markdown, MarkdownV2)"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора.")
        return

    try:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

        # Отправляем меню выбора формата
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="HTML", callback_data="commentary_format_HTML")],
            [InlineKeyboardButton(
                text="Markdown", callback_data="commentary_format_Markdown")],
            [InlineKeyboardButton(
                text="MarkdownV2", callback_data="commentary_format_MarkdownV2")],
        ])

        current_format = "HTML"
        if settings.COMMENTARY_MARKDOWN_ENABLED:
            current_format = settings.COMMENTARY_MARKDOWN_MODE

        await message.answer(
            f"💬 **Выберите формат для толкований и ИИ-ответов:**\n\n"
            f"Текущий формат: **{current_format}**\n\n"
            f"• **HTML** - Стандартный HTML формат (<b>заголовок</b>, <i>курсив</i>)\n"
            f"• **Markdown** - Базовый Markdown (**заголовок**, *курсив*)\n"
            f"• **MarkdownV2** - Расширенный Markdown (*заголовок*, _курсив_)",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"Ошибка при выборе формата толкований: {e}")
        await message.answer("❌ Ошибка при изменении формата толкований")


@admin_router.callback_query(F.data.startswith("commentary_format_"))
async def commentary_format_callback(callback: CallbackQuery):
    """Обработчик выбора формата толкований"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора.")
        return

    try:
        format_name = callback.data.split("_")[2]

        if format_name == "HTML":
            settings.COMMENTARY_MARKDOWN_ENABLED = False
            settings.COMMENTARY_MARKDOWN_MODE = "HTML"
        elif format_name == "Markdown":
            settings.COMMENTARY_MARKDOWN_ENABLED = True
            settings.COMMENTARY_MARKDOWN_MODE = "Markdown"
        elif format_name == "MarkdownV2":
            settings.COMMENTARY_MARKDOWN_ENABLED = True
            settings.COMMENTARY_MARKDOWN_MODE = "MarkdownV2"

        # Определяем пример форматирования
        if format_name == "HTML":
            example = "<b>Толкование проф. Лопухина</b>\n\n<i>Текст толкования с важными словами...</i>"
        elif format_name == "Markdown":
            example = "**Толкование проф. Лопухина**\n\n*Текст толкования с важными словами...*"
        else:  # MarkdownV2
            example = "*Толкование проф\\. Лопухина*\n\n_Текст толкования с важными словами\\.\\.\\._"

        await callback.answer(f"✅ Формат толкований изменен: {format_name}")
        await callback.message.edit_text(
            f"✅ **Формат толкований и ИИ-ответов изменен на: {format_name}**\n\n"
            f"💬 **Пример отображения:**\n{example}\n\n"
            f"🔄 Изменения применятся для всех новых толкований и ИИ-ответов.",
            parse_mode="Markdown"
        )

        logger.info(
            f"Администратор {callback.from_user.id} изменил формат толкований на: {format_name}")

    except Exception as e:
        logger.error(f"Ошибка при установке формата толкований: {e}")
        await callback.answer("❌ Ошибка при изменении формата толкований")


@admin_router.message(Command("set_spacing"))
async def set_spacing_command(message: Message):
    """Устанавливает количество пробелов после номера стиха"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора.")
        return

    try:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

        # Отправляем меню выбора количества пробелов
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="1 пробел", callback_data="spacing_1"),
                InlineKeyboardButton(
                    text="2 пробела", callback_data="spacing_2")
            ],
            [
                InlineKeyboardButton(
                    text="3 пробела", callback_data="spacing_3"),
                InlineKeyboardButton(
                    text="4 пробела", callback_data="spacing_4")
            ],
            [
                InlineKeyboardButton(
                    text="5 пробелов", callback_data="spacing_5")
            ]
        ])

        current_spacing = settings.BIBLE_VERSE_NUMBER_SPACING

        await message.answer(
            f"📏 **Выберите количество пробелов после номера стиха:**\n\n"
            f"Текущее количество: **{current_spacing} {'пробел' if current_spacing == 1 else 'пробела' if current_spacing <= 4 else 'пробелов'}**\n\n"
            f"📖 **Пример с {current_spacing} пробелом(ами):**\n"
            f"<b>1</b>{' ' * current_spacing}В начале сотворил Бог небо и землю.\n"
            f"<b>2</b>{' ' * current_spacing}Земля же была безвидна и пуста...",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Ошибка при выборе количества пробелов: {e}")
        await message.answer("❌ Ошибка при изменении количества пробелов")


@admin_router.callback_query(F.data.startswith("spacing_"))
async def spacing_callback(callback: CallbackQuery):
    """Обработчик выбора количества пробелов"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора.")
        return

    try:
        spacing_count = int(callback.data.split("_")[1])
        settings.BIBLE_VERSE_NUMBER_SPACING = spacing_count

        # Создаем пример с новым количеством пробелов
        example_html = f"<b>1</b>{' ' * spacing_count}В начале сотворил Бог небо и землю.\n<b>2</b>{' ' * spacing_count}Земля же была безвидна и пуста..."

        spacing_word = "пробел" if spacing_count == 1 else "пробела" if spacing_count <= 4 else "пробелов"

        await callback.answer(f"✅ Установлено: {spacing_count} {spacing_word}")
        await callback.message.edit_text(
            f"✅ **Количество пробелов изменено на: {spacing_count} {spacing_word}**\n\n"
            f"📖 **Пример нового отображения:**\n{example_html}\n\n"
            f"🔄 Изменения применятся для всех новых сообщений с номерами стихов.",
            parse_mode="HTML"
        )

        logger.info(
            f"Администратор {callback.from_user.id} изменил количество пробелов на: {spacing_count}")

    except Exception as e:
        logger.error(f"Ошибка при установке количества пробелов: {e}")
        await callback.answer("❌ Ошибка при изменении количества пробелов")


@admin_router.message(Command("toggle_chapter_numbers"))
async def toggle_chapter_numbers(message: Message):
    """Переключает формат номеров стихов между 'стих' и 'глава:стих'."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора.")
        return

    try:
        # Переключаем настройку
        settings.BIBLE_INCLUDE_CHAPTER_NUMBER = not settings.BIBLE_INCLUDE_CHAPTER_NUMBER

        new_format = "глава:стих" if settings.BIBLE_INCLUDE_CHAPTER_NUMBER else "только стих"
        icon = "✅" if settings.BIBLE_INCLUDE_CHAPTER_NUMBER else "📖"

        format_example = ""
        if settings.BIBLE_INCLUDE_CHAPTER_NUMBER:
            format_example = "\n\n📖 **Пример с номерами глав:**\n<b>1:1</b> В начале сотворил Бог небо и землю.\n<b>1:2</b> Земля же была безвидна и пуста..."
        else:
            format_example = "\n\n📖 **Пример только номеров стихов:**\n<b>1</b> В начале сотворил Бог небо и землю.\n<b>2</b> Земля же была безвидна и пуста..."

        await message.answer(
            f"{icon} **Формат номеров изменен на: {new_format}**\n\n"
            f"Теперь номера стихов будут отображаться "
            f"{'в формате \"глава:стих\" (например, 1:12)' if settings.BIBLE_INCLUDE_CHAPTER_NUMBER else 'только как номер стиха (например, 12)'}."
            f"{format_example}",
            parse_mode="HTML"
        )

        logger.info(
            f"Администратор {message.from_user.id} изменил формат номеров на: {new_format}")

    except Exception as e:
        logger.error(f"Ошибка при переключении формата номеров: {e}")
        await message.answer("❌ Ошибка при изменении формата номеров")


@admin_router.message(Command("set_verse_style"))
async def set_verse_style(message: Message):
    """Изменить стиль номеров стихов."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора.")
        return

    try:
        # Создаем инлайн кнопки для выбора стиля
        style_buttons = [
            [InlineKeyboardButton(
                text="📝 Жирный (bold)",
                callback_data="setstyle_bold"
            )],
            [InlineKeyboardButton(
                text="💻 Код (code)",
                callback_data="setstyle_code"
            )],
            [InlineKeyboardButton(
                text="✍️ Курсив (italic)",
                callback_data="setstyle_italic"
            )]
        ]

        kb = InlineKeyboardMarkup(inline_keyboard=style_buttons)

        # Показываем примеры
        examples = (
            f"📖 **Примеры стилей:**\n\n"
            f"**Жирный (bold):** <b>12</b> Текст стиха...\n"
            f"**Код (code):** <code>12</code> Текст стиха...\n"
            f"**Курсив (italic):** <i>12</i> Текст стиха...\n\n"
            f"Текущий стиль: **{settings.BIBLE_VERSE_NUMBER_STYLE}**"
        )

        await message.answer(examples, reply_markup=kb, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Ошибка при отображении стилей: {e}")
        await message.answer("❌ Ошибка при отображении стилей")


@admin_router.callback_query(F.data.startswith("setstyle_"))
async def set_verse_style_callback(callback: CallbackQuery):
    """Обработчик выбора стиля номеров стихов."""
    try:
        style = callback.data.split("_")[1]

        # Устанавливаем новый стиль
        settings.BIBLE_VERSE_NUMBER_STYLE = style

        # Описания стилей
        style_names = {
            "bold": "жирный",
            "code": "код",
            "italic": "курсив"
        }

        style_name = style_names.get(style, style)

        await callback.message.edit_text(
            f"✅ Стиль номеров стихов изменен на: **{style_name}**",
            parse_mode="HTML"
        )

        logger.info(
            f"Администратор {callback.from_user.id} изменил стиль номеров на: {style}")

    except Exception as e:
        logger.error(f"Ошибка при установке стиля: {e}")
        await callback.answer("❌ Ошибка при изменении стиля")


@admin_router.message(Command("toggle_lopukhin"))
async def toggle_lopukhin_commentary(message: Message):
    """Переключает режим отображения толкований Лопухина."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора.")
        return

    try:
        # Переключаем настройку
        settings.ENABLE_LOPUKHIN_COMMENTARY = not settings.ENABLE_LOPUKHIN_COMMENTARY

        status = "включены" if settings.ENABLE_LOPUKHIN_COMMENTARY else "отключены"
        icon = "✅" if settings.ENABLE_LOPUKHIN_COMMENTARY else "❌"

        await message.answer(
            f"{icon} **Толкования проф. Лопухина {status}**\n\n"
            f"Кнопки толкований будут "
            f"{'отображаться под главами и стихами' if settings.ENABLE_LOPUKHIN_COMMENTARY else 'скрыты во всем боте'}.",
            parse_mode="Markdown"
        )

        logger.info(
            f"Администратор {message.from_user.id} переключил толкования Лопухина: {status}")

    except Exception as e:
        logger.error(f"Ошибка при переключении толкований Лопухина: {e}")
        await message.answer("❌ Произошла ошибка при переключении толкований.")


@admin_router.message(Command("lopukhin_on"))
async def enable_lopukhin_commentary(message: Message):
    """Включает толкования Лопухина."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора.")
        return

    try:
        settings.ENABLE_LOPUKHIN_COMMENTARY = True
        await message.answer(
            "✅ **Толкования проф. Лопухина включены**\n\n"
            "Кнопки толкований теперь будут отображаться под главами и стихами.",
            parse_mode="Markdown"
        )
        logger.info(
            f"Администратор {message.from_user.id} включил толкования Лопухина")
    except Exception as e:
        logger.error(f"Ошибка при включении толкований Лопухина: {e}")
        await message.answer("❌ Произошла ошибка при включении толкований.")


@admin_router.message(Command("lopukhin_off"))
async def disable_lopukhin_commentary(message: Message):
    """Отключает толкования Лопухина."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора.")
        return

    try:
        settings.ENABLE_LOPUKHIN_COMMENTARY = False
        await message.answer(
            "❌ **Толкования проф. Лопухина отключены**\n\n"
            "Кнопки толкований будут скрыты во всем боте.",
            parse_mode="Markdown"
        )
        logger.info(
            f"Администратор {message.from_user.id} отключил толкования Лопухина")
    except Exception as e:
        logger.error(f"Ошибка при отключении толкований Лопухина: {e}")
        await message.answer("❌ Произошла ошибка при отключении толкований.")
