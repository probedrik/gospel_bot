"""
Клавиатуры для настроек бота
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config.settings import ADMIN_USER_ID


def create_settings_keyboard(user_id: int = None) -> InlineKeyboardMarkup:
    """Создает клавиатуру настроек"""
    buttons = [
        [
            InlineKeyboardButton(
                text="🔄 Сменить перевод",
                callback_data="settings_translation"
            )
        ],
        [
            InlineKeyboardButton(
                text="🤖 Лимиты ИИ",
                callback_data="settings_ai_limits"
            )
        ],
        [
            InlineKeyboardButton(
                text="❓ Помощь",
                callback_data="settings_help"
            )
        ]
    ]
    
    # Добавляем админские настройки для администратора
    if user_id and user_id == ADMIN_USER_ID:
        buttons.append([
            InlineKeyboardButton(
                text="👑 Админ панель",
                callback_data="settings_admin"
            )
        ])
    
    buttons.append([
        InlineKeyboardButton(
            text="⬅️ Назад в главное меню",
            callback_data="back_to_main"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_admin_settings_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру админских настроек"""
    buttons = [
        [
            InlineKeyboardButton(
                text="🎛️ Управление кнопками",
                callback_data="admin_buttons"
            )
        ],
        [
            InlineKeyboardButton(
                text="📊 Статистика бота",
                callback_data="admin_stats"
            )
        ],
        [
            InlineKeyboardButton(
                text="🤖 Настройки ИИ",
                callback_data="admin_ai_settings"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад к настройкам",
                callback_data="back_to_settings"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_ai_limits_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру информации о лимитах ИИ"""
    buttons = [
        [
            InlineKeyboardButton(
                text="📈 Мой лимит",
                callback_data="ai_limits_my"
            )
        ],
        [
            InlineKeyboardButton(
                text="ℹ️ Как работают лимиты",
                callback_data="ai_limits_info"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад к настройкам",
                callback_data="back_to_settings"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_button_management_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру управления кнопками (для админа)"""
    buttons = [
        [
            InlineKeyboardButton(
                text="📖 Выбрать книгу",
                callback_data="toggle_button_books"
            ),
            InlineKeyboardButton(
                text="✅",  # Статус кнопки
                callback_data="noop"
            )
        ],
        [
            InlineKeyboardButton(
                text="📚 План чтения",
                callback_data="toggle_button_reading"
            ),
            InlineKeyboardButton(
                text="✅",
                callback_data="noop"
            )
        ],
        [
            InlineKeyboardButton(
                text="📝 Мои закладки",
                callback_data="toggle_button_bookmarks"
            ),
            InlineKeyboardButton(
                text="✅",
                callback_data="noop"
            )
        ],
        [
            InlineKeyboardButton(
                text="🎯 Темы",
                callback_data="toggle_button_topics"
            ),
            InlineKeyboardButton(
                text="✅",
                callback_data="noop"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔍 Поиск по слову",
                callback_data="toggle_button_search"
            ),
            InlineKeyboardButton(
                text="❌",  # Отключена по умолчанию
                callback_data="noop"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад к админ панели",
                callback_data="back_to_admin"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)