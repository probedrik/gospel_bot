"""
Обработчики настроек бота
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from keyboards.settings import (
    create_settings_keyboard,
    create_admin_settings_keyboard,
    create_ai_limits_keyboard,
    create_button_management_keyboard
)
from keyboards.main import create_translations_keyboard, get_main_keyboard
from database.universal_manager import universal_db_manager as db_manager
from config.settings import ADMIN_USER_ID

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.text == "⚙️ Настройки")
async def show_settings_menu(message: Message, state: FSMContext):
    """Показывает меню настроек"""
    keyboard = create_settings_keyboard(message.from_user.id)
    await message.answer(
        "⚙️ **Настройки**\n\n"
        "Выберите раздел настроек:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "back_to_settings")
async def back_to_settings(callback: CallbackQuery, state: FSMContext):
    """Возврат к настройкам"""
    keyboard = create_settings_keyboard(callback.from_user.id)
    await callback.message.edit_text(
        "⚙️ **Настройки**\n\n"
        "Выберите раздел настроек:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "settings_translation")
async def settings_translation(callback: CallbackQuery, state: FSMContext):
    """Настройки перевода"""
    keyboard = create_translations_keyboard()
    await callback.message.edit_text(
        "🔄 **Смена перевода**\n\n"
        "Выберите перевод Библии:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "settings_ai_limits")
async def settings_ai_limits(callback: CallbackQuery, state: FSMContext):
    """Информация о лимитах ИИ"""
    keyboard = create_ai_limits_keyboard()
    await callback.message.edit_text(
        "🤖 **Лимиты ИИ**\n\n"
        "Информация о лимитах использования ИИ помощника:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "ai_limits_my")
async def show_my_ai_limits(callback: CallbackQuery, state: FSMContext):
    """Показывает лимиты пользователя"""
    user_id = callback.from_user.id
    
    try:
        # Получаем информацию о лимитах из базы данных
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Здесь должна быть логика получения лимитов из БД
        # Пока что показываем заглушку
        daily_limit = 10  # Дневной лимит
        used_today = 3    # Использовано сегодня
        remaining = daily_limit - used_today
        
        message_text = (
            f"📊 **Ваши лимиты ИИ**\n\n"
            f"🗓️ **Сегодня ({today}):**\n"
            f"• Лимит: {daily_limit} запросов\n"
            f"• Использовано: {used_today}\n"
            f"• Осталось: {remaining}\n\n"
            f"ℹ️ Лимиты обновляются каждый день в 00:00 UTC"
        )
        
        keyboard = create_ai_limits_keyboard()
        await callback.message.edit_text(
            message_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Ошибка при получении лимитов ИИ: {e}")
        await callback.answer("Ошибка при получении информации о лимитах")


@router.callback_query(F.data == "ai_limits_info")
async def show_ai_limits_info(callback: CallbackQuery, state: FSMContext):
    """Показывает информацию о том, как работают лимиты"""
    message_text = (
        "ℹ️ **Как работают лимиты ИИ**\n\n"
        "🎯 **Что считается запросом:**\n"
        "• Разбор стиха или главы ИИ\n"
        "• Объяснение библейской темы\n"
        "• Ответы ИИ помощника\n\n"
        "⏰ **Обновление лимитов:**\n"
        "• Лимиты обновляются каждый день\n"
        "• Время обновления: 00:00 UTC\n\n"
        "📈 **Дневной лимит:**\n"
        "• Обычные пользователи: 10 запросов\n"
        "• Администраторы: без ограничений\n\n"
        "💡 **Совет:** Сохраняйте интересные разборы в закладки, "
        "чтобы не тратить лимит на повторные запросы!"
    )
    
    keyboard = create_ai_limits_keyboard()
    await callback.message.edit_text(
        message_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "settings_help")
async def settings_help(callback: CallbackQuery, state: FSMContext):
    """Показывает помощь"""
    help_text = (
        "❓ **Помощь по использованию бота**\n\n"
        "📖 **Чтение Библии:**\n"
        "• Выберите книгу → главу → читайте\n"
        "• Отправьте ссылку: 'Ин 3:16' или 'Быт 1-3'\n"
        "• Поддерживаются диапазоны: 'Мф 5:3-12'\n\n"
        "🤖 **ИИ помощник:**\n"
        "• Нажмите 'Разбор от ИИ' под стихом\n"
        "• Сохраняйте интересные разборы\n"
        "• Следите за лимитами запросов\n\n"
        "📝 **Закладки:**\n"
        "• Сохраняйте любые стихи и главы\n"
        "• Добавляйте заметки к закладкам\n"
        "• Просматривайте сохраненные разборы\n\n"
        "📚 **Планы чтения:**\n"
        "• Выберите план на год или месяц\n"
        "• Отмечайте прочитанное\n"
        "• Следите за прогрессом\n\n"
        "🎯 **Темы:**\n"
        "• Изучайте библейские темы\n"
        "• Находите стихи по темам\n"
        "• Получайте разборы от ИИ\n\n"
        "💬 **Поддержка:** @your_support_username"
    )
    
    keyboard = create_settings_keyboard(callback.from_user.id)
    await callback.message.edit_text(
        help_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()


# Админские функции
@router.callback_query(F.data == "settings_admin")
async def settings_admin(callback: CallbackQuery, state: FSMContext):
    """Админская панель"""
    if callback.from_user.id != ADMIN_USER_ID:
        await callback.answer("У вас нет прав доступа к админ панели")
        return
    
    keyboard = create_admin_settings_keyboard()
    await callback.message.edit_text(
        "👑 **Админ панель**\n\n"
        "Управление настройками бота:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_admin")
async def back_to_admin(callback: CallbackQuery, state: FSMContext):
    """Возврат к админ панели"""
    if callback.from_user.id != ADMIN_USER_ID:
        await callback.answer("У вас нет прав доступа")
        return
    
    keyboard = create_admin_settings_keyboard()
    await callback.message.edit_text(
        "👑 **Админ панель**\n\n"
        "Управление настройками бота:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_buttons")
async def admin_buttons(callback: CallbackQuery, state: FSMContext):
    """Управление кнопками"""
    if callback.from_user.id != ADMIN_USER_ID:
        await callback.answer("У вас нет прав доступа")
        return
    
    keyboard = create_button_management_keyboard()
    await callback.message.edit_text(
        "🎛️ **Управление кнопками**\n\n"
        "Включите или отключите кнопки в главном меню:\n"
        "✅ - кнопка включена\n"
        "❌ - кнопка отключена",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery, state: FSMContext):
    """Статистика бота"""
    if callback.from_user.id != ADMIN_USER_ID:
        await callback.answer("У вас нет прав доступа")
        return
    
    # Здесь должна быть логика получения статистики
    stats_text = (
        "📊 **Статистика бота**\n\n"
        "👥 **Пользователи:**\n"
        "• Всего: 150\n"
        "• Активных сегодня: 25\n"
        "• Новых за неделю: 12\n\n"
        "🤖 **ИИ запросы:**\n"
        "• Сегодня: 45\n"
        "• За неделю: 320\n"
        "• За месяц: 1,250\n\n"
        "📝 **Закладки:**\n"
        "• Всего создано: 890\n"
        "• Активных: 750\n\n"
        "📚 **Планы чтения:**\n"
        "• Активных планов: 35\n"
        "• Завершенных: 8"
    )
    
    keyboard = create_admin_settings_keyboard()
    await callback.message.edit_text(
        stats_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_ai_settings")
async def admin_ai_settings(callback: CallbackQuery, state: FSMContext):
    """Настройки ИИ для админа"""
    if callback.from_user.id != ADMIN_USER_ID:
        await callback.answer("У вас нет прав доступа")
        return
    
    ai_settings_text = (
        "🤖 **Настройки ИИ**\n\n"
        "⚙️ **Текущие настройки:**\n"
        "• Дневной лимит: 10 запросов\n"
        "• Модель: GPT-3.5-turbo\n"
        "• Максимум токенов: 1000\n"
        "• Температура: 0.7\n\n"
        "📊 **Использование:**\n"
        "• Запросов сегодня: 45\n"
        "• Средняя длина ответа: 250 токенов\n"
        "• Успешных запросов: 98%\n\n"
        "💰 **Стоимость:**\n"
        "• Сегодня: $2.15\n"
        "• За месяц: $65.40"
    )
    
    keyboard = create_admin_settings_keyboard()
    await callback.message.edit_text(
        ai_settings_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_main")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    # Удаляем сообщение с inline клавиатурой
    await callback.message.delete()
    
    # Отправляем новое сообщение с обычной клавиатурой
    await callback.message.answer(
        "🏠 Главное меню",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()