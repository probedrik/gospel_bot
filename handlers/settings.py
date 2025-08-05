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
    create_button_management_keyboard,
    create_premium_ai_keyboard,
    create_donation_keyboard,
    create_admin_ai_limits_keyboard,
    create_free_premium_users_keyboard
)
from keyboards.main import create_translations_keyboard, get_main_keyboard
from database.universal_manager import universal_db_manager as db_manager
from config.settings import ADMIN_USER_ID
from config.ai_settings import PREMIUM_AI_PACKAGE_PRICE, PREMIUM_AI_PACKAGE_REQUESTS, AI_DAILY_LIMIT

logger = logging.getLogger(__name__)
router = Router()


# Диагностический обработчик убран


async def get_premium_info_text() -> str:
    """Возвращает актуальный текст информации о премиум доступе"""
    from services.ai_settings_manager import ai_settings_manager

    daily_limit = await ai_settings_manager.get_daily_limit()
    premium_price = await ai_settings_manager.get_premium_price()
    premium_requests = await ai_settings_manager.get_premium_requests()

    return (
        "⭐ **Премиум доступ к ИИ**\n\n"
        "🎯 **Что это такое?**\n"
        "Доступ к продвинутому ИИ помощнику с расширенными возможностями анализа Священного Писания.\n\n"
        "🧠 **Премиум ИИ помощник:**\n"
        "• Более мощная модель ИИ (Claude 3.5 Sonnet)\n"
        "• Глубокий богословский анализ\n"
        "• Знание древних языков (греческий, еврейский)\n"
        "• Ссылки на святоотеческие толкования\n"
        "• Подробные ответы (до 4000 символов)\n"
        "• Исторический и культурный контекст\n\n"
        "💎 **Преимущества:**\n"
        f"• +{premium_requests} премиум запросов за {premium_price}₽\n"
        "• Запросы не сгорают (несгораемые)\n"
        "• Можно использовать в любое время\n"
        "• Накапливаются с обычными лимитами\n"
        "• **Премиум пользователи всегда используют продвинутый ИИ!**\n\n"
        "🔄 **Как работает:**\n"
        f"1. Если у вас есть премиум запросы - всегда используется премиум ИИ\n"
        f"2. Сначала тратятся дневные лимиты ({daily_limit} запросов с премиум ИИ)\n"
        "3. Затем используются купленные премиум запросы\n"
        "4. Премиум запросы никогда не сгорают\n\n"
        "💳 **Оплата:** ЮKassa (карта, СБП, кошельки)"
    )


async def get_premium_detailed_info_text() -> str:
    """Возвращает подробную информацию о премиум доступе"""
    from services.ai_settings_manager import ai_settings_manager

    daily_limit = await ai_settings_manager.get_daily_limit()
    premium_price = await ai_settings_manager.get_premium_price()
    premium_requests = await ai_settings_manager.get_premium_requests()
    total_requests = daily_limit + premium_requests

    return (
        "ℹ️ **Как работает премиум доступ**\n\n"
        "🧠 **Два уровня ИИ помощника:**\n"
        "• **Обычный ИИ:** Краткие ответы (до 2000 символов), базовая модель\n"
        "• **Премиум ИИ:** Подробный анализ (до 4000 символов), продвинутая модель\n\n"
        "🎯 **Принцип работы:**\n"
        f"• **Премиум пользователи всегда используют премиум ИИ!**\n"
        f"• Сначала тратятся дневные лимиты ({daily_limit} запросов с премиум ИИ)\n"
        "• Затем используются купленные премиум запросы\n"
        "• Премиум запросы никогда не сгорают\n\n"
        "📈 **Пример использования:**\n"
        f"• Дневной лимит: {daily_limit} запросов (премиум ИИ)\n"
        f"• Премиум запросы: {premium_requests} (премиум ИИ)\n"
        f"• Всего доступно: {total_requests} запросов в день\n"
        f"• На следующий день: {daily_limit} + {premium_requests} (если не потратили)\n\n"
        "⭐ **Преимущества премиум ИИ:**\n"
        "• Более глубокий богословский анализ\n"
        "• Знание древних языков и контекста\n"
        "• Ссылки на святоотеческие толкования\n"
        "• Подробные исторические справки\n\n"
        f"💰 **Стоимость:** {premium_price}₽ за {premium_requests} премиум запросов\n"
        "🔒 **Безопасность:** Оплата через ЮKassa"
    )


@router.message(F.text == "⚙️ Настройки")
async def show_settings_menu(message: Message, state: FSMContext):
    """Показывает меню настроек"""
    keyboard = await create_settings_keyboard(message.from_user.id)
    await message.answer(
        "⚙️ **Настройки**\n\n"
        "Выберите раздел настроек:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "back_to_settings")
async def back_to_settings(callback: CallbackQuery, state: FSMContext):
    """Возврат к настройкам"""
    keyboard = await create_settings_keyboard(callback.from_user.id)
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
        # Получаем информацию о квотах из менеджера
        from services.ai_quota_manager import ai_quota_manager
        quota_info = await ai_quota_manager.get_user_quota_info(user_id)

        # Форматируем сообщение
        status_icon = "👑" if quota_info['is_admin'] else "👤"
        user_type = "Администратор" if quota_info['is_admin'] else "Пользователь"

        premium_text = ""
        if quota_info.get('premium_requests', 0) > 0:
            premium_text = f"\n⭐ **Премиум запросы:** {quota_info['premium_requests']}"

        total_available = quota_info.get(
            'total_available', quota_info['remaining'])

        message_text = (
            f"📊 **Ваши лимиты ИИ**\n\n"
            f"{status_icon} **Тип:** {user_type}\n"
            f"🗓️ **Сегодня ({quota_info['date']}):**\n"
            f"• Дневной лимит: {quota_info['daily_limit']} запросов\n"
            f"• Использовано: {quota_info['used_today']}\n"
            f"• Осталось: {quota_info['remaining']}{premium_text}\n"
            f"• **Всего доступно: {total_available}**\n\n"
            f"⏰ **Обновление:** через {quota_info['hours_until_reset']} ч.\n"
            f"🔄 Дневные лимиты сбрасываются в 00:00 UTC\n"
            f"⭐ Премиум запросы не сгорают"
        )

        # Добавляем предупреждение если лимит исчерпан
        if not quota_info['can_use_ai'] and not quota_info['is_admin']:
            message_text += f"\n\n⚠️ **Лимит исчерпан!** Новые запросы будут доступны через {quota_info['hours_until_reset']} ч."

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
    from services.ai_quota_manager import ai_quota_manager, DEFAULT_DAILY_LIMIT, ADMIN_DAILY_LIMIT, QUOTA_RESET_HOUR

    # Получаем статистику квот
    stats = await ai_quota_manager.get_quota_stats()

    message_text = (
        "ℹ️ **Как работают лимиты ИИ**\n\n"
        "🎯 **Что считается запросом:**\n"
        "• Разбор стиха или главы ИИ\n"
        "• Объяснение библейской темы\n"
        "• Ответы ИИ помощника\n\n"
        "⏰ **Автоматическое обновление:**\n"
        f"• Лимиты сбрасываются в {QUOTA_RESET_HOUR:02d}:00 UTC\n"
        "• Система работает автоматически\n"
        f"• Планировщик: {'🟢 активен' if stats.get('scheduler_running') else '🔴 неактивен'}\n\n"
        "📈 **Дневные лимиты:**\n"
        f"• Обычные пользователи: {DEFAULT_DAILY_LIMIT} запроса\n"
        f"• Администраторы: {ADMIN_DAILY_LIMIT} запросов\n\n"
        "💡 **Советы:**\n"
        "• Сохраняйте разборы в закладки\n"
        "• Используйте поиск по темам\n"
        "• Планируйте запросы заранее"
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

    keyboard = await create_settings_keyboard(callback.from_user.id)
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


# Премиум доступ к ИИ
@router.callback_query(F.data == "ai_premium_access")
async def ai_premium_access(callback: CallbackQuery, state: FSMContext):
    """Показывает информацию о премиум доступе к ИИ"""
    keyboard = create_premium_ai_keyboard()
    premium_text = await get_premium_info_text()

    await callback.message.edit_text(
        premium_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "buy_premium_ai_50")
async def buy_premium_ai_50(callback: CallbackQuery, state: FSMContext):
    """Покупка 50 премиум запросов"""
    # TODO: Интеграция с ЮKassa
    await callback.answer(
        "💳 Оплата временно недоступна. Функция в разработке.",
        show_alert=True
    )


@router.callback_query(F.data == "my_premium_requests")
async def my_premium_requests(callback: CallbackQuery, state: FSMContext):
    """Показывает количество премиум запросов пользователя"""
    user_id = callback.from_user.id

    # Получаем статистику премиум запросов
    from services.premium_manager import premium_manager
    stats = await premium_manager.get_user_premium_stats(user_id)

    # Форматируем дату первой покупки
    first_purchase = ""
    if stats['created_at']:
        first_purchase = f"\n📅 **Первая покупка:** {stats['created_at'].strftime('%d.%m.%Y')}"

    text = (
        f"📊 **Ваши премиум запросы**\n\n"
        f"⭐ **Доступно:** {stats['available']} запросов\n"
        f"📈 **Всего куплено:** {stats['total_purchased']}\n"
        f"📉 **Всего использовано:** {stats['total_used']}{first_purchase}\n\n"
        f"ℹ️ **Как работает:**\n"
        f"• Не сгорают со временем\n"
        f"• Используются после дневных лимитов\n"
        f"• Накапливаются при покупке\n\n"
        f"💡 **Сов��т:** Покупайте премиум запросы заранее, чтобы всегда иметь доступ к ИИ помощнику!"
    )

    keyboard = create_premium_ai_keyboard()
    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "premium_ai_info")
async def premium_ai_info(callback: CallbackQuery, state: FSMContext):
    """Подробная информация о премиум доступе"""
    info_text = await get_premium_detailed_info_text()

    keyboard = create_premium_ai_keyboard()
    await callback.message.edit_text(
        info_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()


# Пожертвования
@router.callback_query(F.data == "settings_donation")
async def settings_donation(callback: CallbackQuery, state: FSMContext):
    """Показывает меню пожертвований"""
    keyboard = create_donation_keyboard()

    donation_text = (
        "🪙 **Пожертвование на развитие**\n\n"
        "💝 **Поддержите проект!**\n"
        "Ваши пожертвования помогают развивать бота и добавлять новые функции.\n\n"
        "🎯 **На что идут средства:**\n"
        "• Оплата серверов и хостинга\n"
        "• Доступ к API библейских текстов\n"
        "• Улучшение ИИ помощника\n"
        "• Добавление новых переводов\n"
        "• Техническая поддержка\n\n"
        "🙏 **Любая сумма важна!**\n"
        "Даже небольшое пожертвование помогает проекту развиваться.\n\n"
        "💳 **Способы оплаты:** ЮKassa (карта, СБП, кошельки)"
    )

    await callback.message.edit_text(
        donation_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("donate_") & ~F.data.in_(["donate_stars_menu"]))
async def process_donation(callback: CallbackQuery, state: FSMContext):
    """Обработка рублевых пожертвований (исключая Stars)"""
    amount = callback.data.split("_")[1]

    if amount == "custom":
        # TODO: Запросить ввод суммы
        await callback.answer(
            "💰 Ввод произвольной суммы временно недоступен. Выберите готовую сумму.",
            show_alert=True
        )
        return

    # TODO: Интеграция с ЮKassa
    await callback.answer(
        f"💳 Пожертвование {amount}₽ временно недоступно. Функция в разработке.",
        show_alert=True
    )


@router.callback_query(F.data == "donate_stars_menu")
async def show_stars_donation_menu(callback: CallbackQuery, state: FSMContext):
    """Показывает меню пожертвований Telegram Stars"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(
        f"🌟 УСПЕШНО: Открыто меню Stars пожертвований для пользователя {callback.from_user.id}")

    from keyboards.settings import create_stars_donation_keyboard

    stars_text = (
        "⭐ **Пожертвование через Telegram Stars**\n\n"
        "🌟 **Преимущества Telegram Stars:**\n"
        "• Быстрая и безопасная оплата прямо в Telegram\n"
        "• Не нужны банковские карты\n"
        "• Мгновенное поступление средств\n"
        "• Полная анонимность\n\n"
        "💫 **Что такое Stars?**\n"
        "Telegram Stars - это внутренняя валюта Telegram для поддержки проектов и каналов.\n\n"
        "🎯 **Выберите сумму для пожертвования:**"
    )

    keyboard = create_stars_donation_keyboard()

    await callback.message.edit_text(
        stars_text,
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data == "donation_info")
async def donation_info(callback: CallbackQuery, state: FSMContext):
    """Информация о пожертвованиях"""
    info_text = (
        "ℹ️ **О пожертвованиях**\n\n"
        "🎯 **Цель проекта:**\n"
        "Создать лучшего библейского помощника с ИИ поддержкой для изучения Священного Писания.\n\n"
        "💰 **Способы оплаты:**\n"
        "• 🌟 **Telegram Stars** - быстро и удобно\n"
        "• 💳 **ЮKassa** - карты, СБП, кошельки\n\n"
        "💰 **Прозрачность:**\n"
        "• Все средства идут на развитие проекта\n"
        "• Никакой личной выгоды разработчика\n"
        "• Отчеты о тратах по запросу\n\n"
        "🔒 **Безопасность:**\n"
        "• Оплата через официальные системы\n"
        "• Все транзакции защищены\n"
        "• Полная анонимность при оплате Stars\n\n"
        "🙏 **Благодарность:**\n"
        "Каждое пожертвование - это инвестиция в духовное развитие сообщества.\n\n"
        "📧 **Связь:** Вопросы о пожертвованиях можно задать через /feedback"
    )

    keyboard = create_donation_keyboard()
    await callback.message.edit_text(
        info_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()


# Обработчики Stars перенесены в handlers/payments.py


@router.callback_query(F.data == "buy_premium_stars")
async def show_premium_stars_menu(callback: CallbackQuery, state: FSMContext):
    """Показывает меню покупки премиума за Stars"""
    from keyboards.settings import create_premium_stars_keyboard

    premium_stars_text = (
        "🌟 **Премиум запросы за Telegram Stars**\n\n"
        "⭐ **Пакеты премиум запросов:**\n"
        "• 10 запросов = 25 Stars (2.5 Stars за запрос)\n"
        "• 25 запросов = 50 Stars (2.0 Stars за запрос)\n"
        "• 50 запросов = 100 Stars (2.0 Stars за запрос)\n"
        "• 100 запросов = 180 Stars (1.8 Stars за запрос) 💎\n\n"
        "🎯 **Преимущества больших пакетов:**\n"
        "• Больше выгода за запрос\n"
        "• Удобнее для активных пользователей\n"
        "• Запросы не сгорают\n\n"
        "💫 **Выберите пакет:**"
    )

    keyboard = create_premium_stars_keyboard()

    await callback.message.edit_text(
        premium_stars_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()


# Обработчик premium_stars_ перенесен в handlers/payments.py


# Админ панель управления настройками ИИ
@router.callback_query(F.data == "admin_ai_limits")
async def admin_ai_limits(callback: CallbackQuery, state: FSMContext):
    """Админ панель управления лимитами и ценами ИИ"""
    if callback.from_user.id != ADMIN_USER_ID:
        await callback.answer("У вас нет прав доступа")
        return

    from services.ai_settings_manager import ai_settings_manager

    # Получаем текущие настройки
    daily_limit = await ai_settings_manager.get_daily_limit()
    premium_price = await ai_settings_manager.get_premium_price()
    premium_requests = await ai_settings_manager.get_premium_requests()
    admin_premium_mode = await ai_settings_manager.get_admin_premium_mode()
    free_premium_users = await ai_settings_manager.get_free_premium_users()

    admin_mode_text = "Премиум ИИ" if admin_premium_mode else "Обычный ИИ"
    free_users_count = len(free_premium_users)

    text = (
        "⚙️ **Управление лимитами и ценами ИИ**\n\n"
        "📊 **Текущие настройки:**\n"
        f"• Дневной лимит: {daily_limit} запросов\n"
        f"• Цена премиум пакета: {premium_price}₽\n"
        f"• Запросов в пакете: {premium_requests}\n"
        f"• Режим ИИ для админа: {admin_mode_text}\n"
        f"• Бесплатный премиум доступ: {free_users_count} пользователей\n\n"
        "💡 **Примечание:**\n"
        "Изменения применяются мгновенно для всех пользователей.\n"
        "Премиум пользователи всегда используют продвинутый ИИ."
    )

    keyboard = create_admin_ai_limits_keyboard()
    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_change_daily_limit")
async def admin_change_daily_limit(callback: CallbackQuery, state: FSMContext):
    """Изменение дневного лимита ИИ"""
    if callback.from_user.id != ADMIN_USER_ID:
        await callback.answer("У вас нет прав доступа")
        return

    await state.set_state("waiting_daily_limit")
    await callback.message.edit_text(
        "📊 **Изменение дневного лимита ИИ**\n\n"
        "Введите новое значение дневного лимита для обычных пользователей:\n"
        "(например: 3, 5, 10)\n\n"
        "❌ Отправьте /cancel для отмены",
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_change_package_price")
async def admin_change_package_price(callback: CallbackQuery, state: FSMContext):
    """Изменение цены премиум пакета"""
    if callback.from_user.id != ADMIN_USER_ID:
        await callback.answer("У вас нет прав доступа")
        return

    await state.set_state("waiting_package_price")
    await callback.message.edit_text(
        "💰 **Изменение цены премиум пакета**\n\n"
        "Введите новую цену премиум пакета в рублях:\n"
        "(например: 50, 100, 150)\n\n"
        "❌ Отправьте /cancel для отмены",
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_change_package_size")
async def admin_change_package_size(callback: CallbackQuery, state: FSMContext):
    """Изменение размера премиум пакета"""
    if callback.from_user.id != ADMIN_USER_ID:
        await callback.answer("У вас нет прав доступа")
        return

    await state.set_state("waiting_package_size")
    await callback.message.edit_text(
        "📦 **Изменение размера премиум пакета**\n\n"
        "Введите новое количество запросов в премиум пакете:\n"
        "(например: 25, 50, 100)\n\n"
        "❌ Отправьте /cancel для отмены",
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_reset_ai_settings")
async def admin_reset_ai_settings(callback: CallbackQuery, state: FSMContext):
    """Сброс настроек ИИ к умолчаниям"""
    if callback.from_user.id != ADMIN_USER_ID:
        await callback.answer("У вас нет прав доступа")
        return

    from services.ai_settings_manager import ai_settings_manager

    success = await ai_settings_manager.reset_to_defaults()

    if success:
        await callback.answer("✅ Настройки сброшены к умолчаниям", show_alert=True)
        # Возвращаемся к панели управления
        await admin_ai_limits(callback, state)
    else:
        await callback.answer("❌ Ошибка сброса настроек", show_alert=True)


# Обработчики ввода новых значений
@router.message(lambda message: message.text and not message.text.startswith('/'))
async def process_admin_input(message: Message, state: FSMContext):
    """Обработка ввода админских настроек"""
    if message.from_user.id != ADMIN_USER_ID:
        return

    current_state = await state.get_state()

    if current_state == "waiting_daily_limit":
        try:
            new_limit = int(message.text.strip())
            if new_limit < 1 or new_limit > 100:
                await message.answer("❌ Лимит должен быть от 1 до 100")
                return

            from services.ai_settings_manager import ai_settings_manager
            success = await ai_settings_manager.set_setting('ai_daily_limit', new_limit)

            if success:
                await message.answer(f"✅ Дневной лимит изменен на {new_limit} запросов")
            else:
                await message.answer("❌ Ошибка изменения лимита")

            await state.clear()

        except ValueError:
            await message.answer("❌ Введите корректное число")

    elif current_state == "waiting_package_price":
        try:
            new_price = int(message.text.strip())
            if new_price < 10 or new_price > 10000:
                await message.answer("❌ Цена должна быть от 10 до 10000 рублей")
                return

            from services.ai_settings_manager import ai_settings_manager
            success = await ai_settings_manager.set_setting('premium_package_price', new_price)

            if success:
                await message.answer(f"✅ Цена премиум пакета изменена на {new_price}₽")
            else:
                await message.answer("❌ Ошибка изменения цены")

            await state.clear()

        except ValueError:
            await message.answer("❌ Введите корректное число")

    elif current_state == "waiting_package_size":
        try:
            new_size = int(message.text.strip())
            if new_size < 1 or new_size > 1000:
                await message.answer("❌ Размер пакета должен быть от 1 до 1000 запросов")
                return

            from services.ai_settings_manager import ai_settings_manager
            success = await ai_settings_manager.set_setting('premium_package_requests', new_size)

            if success:
                await message.answer(f"✅ Размер премиум пакета изменен на {new_size} запросов")
            else:
                await message.answer("❌ Ошибка изменения размера пакета")

            await state.clear()

        except ValueError:
            await message.answer("❌ Введите корректное число")


@router.callback_query(F.data == "admin_toggle_ai_mode")
async def admin_toggle_ai_mode(callback: CallbackQuery, state: FSMContext):
    """Переключение режима ИИ для админа"""
    if callback.from_user.id != ADMIN_USER_ID:
        await callback.answer("У вас нет прав доступа")
        return

    from services.ai_settings_manager import ai_settings_manager

    current_mode = await ai_settings_manager.get_admin_premium_mode()
    new_mode = not current_mode

    success = await ai_settings_manager.set_admin_premium_mode(new_mode)

    if success:
        mode_text = "премиум ИИ" if new_mode else "обычный ИИ"
        await callback.answer(f"✅ Режим админа изменен на {mode_text}", show_alert=True)
        # Возвращаемся к панели управления
        await admin_ai_limits(callback, state)
    else:
        await callback.answer("❌ Ошибка изменения режима", show_alert=True)


@router.callback_query(F.data == "toggle_button_calendar")
async def toggle_calendar_button(callback: CallbackQuery, state: FSMContext):
    """Переключение кнопки календаря в главном меню"""
    if callback.from_user.id != ADMIN_USER_ID:
        await callback.answer("У вас нет прав доступа")
        return

    from services.ai_settings_manager import ai_settings_manager

    # Получаем текущее состояние
    current_enabled = await ai_settings_manager.is_calendar_enabled()
    new_enabled = not current_enabled

    # Переключаем
    success = await ai_settings_manager.set_calendar_enabled(new_enabled)

    if success:
        status = "включена" if new_enabled else "отключена"
        await callback.answer(f"✅ Кнопка календаря {status}")
    else:
        await callback.answer("❌ Ошибка при изменении настройки")

    # Возвращаемся к панели управления кнопками
    await admin_buttons(callback, state)


@router.callback_query(F.data == "admin_free_premium_users")
async def admin_free_premium_users(callback: CallbackQuery, state: FSMContext):
    """Управление бесплатными премиум пользователями"""
    if callback.from_user.id != ADMIN_USER_ID:
        await callback.answer("У вас нет прав доступа")
        return

    from services.ai_settings_manager import ai_settings_manager

    free_users = await ai_settings_manager.get_free_premium_users()
    users_count = len(free_users)

    text = (
        "👥 **Бесплатный премиум доступ**\n\n"
        f"📊 **Текущее состояние:**\n"
        f"• Пользователей с доступом: {users_count}\n\n"
        "ℹ️ **Что это дает:**\n"
        "• Доступ к премиум ИИ в рамках дневных лимитов\n"
        "• Не тратятся премиум запросы\n"
        "• После исчерпания дневных лимитов - доступ заканчивается\n\n"
        "⚙️ **Управление:**\n"
        "Добавляйте пользователей по их Telegram ID"
    )

    keyboard = create_free_premium_users_keyboard()
    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_add_free_premium_user")
async def admin_add_free_premium_user(callback: CallbackQuery, state: FSMContext):
    """Добавление пользователя в бесплатный премиум"""
    if callback.from_user.id != ADMIN_USER_ID:
        await callback.answer("У вас нет прав доступа")
        return

    await state.set_state("waiting_add_free_premium_user")
    await callback.message.edit_text(
        "➕ **Добавление пользователя в бесплатный премиум**\n\n"
        "Введите Telegram ID пользователя:\n"
        "(например: 123456789)\n\n"
        "💡 **Как узнать ID:**\n"
        "• Попросите пользователя написать боту /start\n"
        "• ID отобразится в логах бота\n"
        "• Или используйте @userinfobot\n\n"
        "❌ Отправьте /cancel для отмены",
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_remove_free_premium_user")
async def admin_remove_free_premium_user(callback: CallbackQuery, state: FSMContext):
    """Удаление пользователя из бесплатного премиум"""
    if callback.from_user.id != ADMIN_USER_ID:
        await callback.answer("У вас нет прав доступа")
        return

    await state.set_state("waiting_remove_free_premium_user")
    await callback.message.edit_text(
        "➖ **Удаление пользователя из бесплатного премиум**\n\n"
        "Введите Telegram ID пользователя для удаления:\n"
        "(например: 123456789)\n\n"
        "❌ Отправьте /cancel для отмены",
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_show_free_premium_users")
async def admin_show_free_premium_users(callback: CallbackQuery, state: FSMContext):
    """Показать список бесплатных премиум пользователей"""
    if callback.from_user.id != ADMIN_USER_ID:
        await callback.answer("У вас нет прав доступа")
        return

    from services.ai_settings_manager import ai_settings_manager

    free_users = await ai_settings_manager.get_free_premium_users()

    if free_users:
        users_list = "\n".join(
            [f"• {user_id}" for user_id in sorted(free_users)])
        text = (
            "📋 **Список пользователей с бесплатным премиум доступом**\n\n"
            f"👥 **Всего пользователей:** {len(free_users)}\n\n"
            f"**ID пользователей:**\n{users_list}"
        )
    else:
        text = (
            "📋 **Список пользователей с бесплатным премиум доступом**\n\n"
            "👥 **Список пуст**\n\n"
            "Пока никому не предоставлен бесплатный доступ к премиум ИИ."
        )

    keyboard = create_free_premium_users_keyboard()
    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()


# Обновляем обработчик ввода админских настроек
@router.message(lambda message: message.text and not message.text.startswith('/'))
async def process_admin_input(message: Message, state: FSMContext):
    """Обработка ввода админских настроек"""
    if message.from_user.id != ADMIN_USER_ID:
        return

    current_state = await state.get_state()

    if current_state == "waiting_daily_limit":
        try:
            new_limit = int(message.text.strip())
            if new_limit < 1 or new_limit > 100:
                await message.answer("❌ Лимит должен быть от 1 до 100")
                return

            from services.ai_settings_manager import ai_settings_manager
            success = await ai_settings_manager.set_setting('ai_daily_limit', new_limit)

            if success:
                await message.answer(f"✅ Дневной лимит изменен на {new_limit} запросов")
            else:
                await message.answer("❌ Ошибка изменения лимита")

            await state.clear()

        except ValueError:
            await message.answer("❌ Введите корректное число")

    elif current_state == "waiting_package_price":
        try:
            new_price = int(message.text.strip())
            if new_price < 10 or new_price > 10000:
                await message.answer("❌ Цена должна быть от 10 до 10000 рублей")
                return

            from services.ai_settings_manager import ai_settings_manager
            success = await ai_settings_manager.set_setting('premium_package_price', new_price)

            if success:
                await message.answer(f"✅ Цена премиум пакета изменена на {new_price}₽")
            else:
                await message.answer("❌ Ошибка изменения цены")

            await state.clear()

        except ValueError:
            await message.answer("❌ Введите корректное число")

    elif current_state == "waiting_package_size":
        try:
            new_size = int(message.text.strip())
            if new_size < 1 or new_size > 1000:
                await message.answer("❌ Размер пакета должен быть от 1 до 1000 запросов")
                return

            from services.ai_settings_manager import ai_settings_manager
            success = await ai_settings_manager.set_setting('premium_package_requests', new_size)

            if success:
                await message.answer(f"✅ Размер премиум пакета изменен на {new_size} запросов")
            else:
                await message.answer("❌ Ошибка изменения размера пакета")

            await state.clear()

        except ValueError:
            await message.answer("❌ Введите корректное число")

    elif current_state == "waiting_add_free_premium_user":
        try:
            user_id = int(message.text.strip())
            if user_id <= 0:
                await message.answer("❌ ID пользователя должен быть положительным числом")
                return

            from services.ai_settings_manager import ai_settings_manager
            success = await ai_settings_manager.add_free_premium_user(user_id)

            if success:
                await message.answer(f"✅ Пользователь {user_id} добавлен в бесплатный премиум доступ")
            else:
                await message.answer("❌ Ошибка добавления пользователя")

            await state.clear()

        except ValueError:
            await message.answer("❌ Введите корректный ID пользователя (число)")

    elif current_state == "waiting_remove_free_premium_user":
        try:
            user_id = int(message.text.strip())

            from services.ai_settings_manager import ai_settings_manager
            free_users = await ai_settings_manager.get_free_premium_users()

            if user_id not in free_users:
                await message.answer(f"❌ Пользователь {user_id} не найден в списке бесплатного премиум доступа")
                return

            success = await ai_settings_manager.remove_free_premium_user(user_id)

            if success:
                await message.answer(f"✅ Пользователь {user_id} удален из бесплатного премиум доступа")
            else:
                await message.answer("❌ Ошибка удаления пользователя")

            await state.clear()

        except ValueError:
            await message.answer("❌ Введите корректный ID пользователя (число)")


@router.message(F.text == "/cancel")
async def cancel_admin_input(message: Message, state: FSMContext):
    """Отмена ввода админских настроек"""
    if message.from_user.id != ADMIN_USER_ID:
        return

    await state.clear()
    await message.answer("❌ Ввод отменен")


@router.callback_query(F.data == "back_to_main")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    # Удаляем сообщение с inline клавиатурой
    await callback.message.delete()

    # Отправляем новое сообщение с обычной клавиатурой
    await callback.message.answer(
        "🏠 Главное меню",
        reply_markup=await get_main_keyboard()
    )
    await callback.answer()
