"""
Клавиатуры для настроек бота
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config.settings import ADMIN_USER_ID
from config.ai_settings import PREMIUM_AI_PACKAGE_PRICE, PREMIUM_AI_PACKAGE_REQUESTS, PREMIUM_REQUESTS_50, PREMIUM_PRICE_50
from services.ai_settings_manager import ai_settings_manager


async def create_settings_keyboard(user_id: int = None) -> InlineKeyboardMarkup:
    """Создает клавиатуру настроек"""
    buttons = [
        [
            InlineKeyboardButton(
                text="🧠 Премиум ИИ",
                callback_data="premium_ai_info"
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
                text="🔄 Сменить перевод",
                callback_data="settings_translation"
            )
        ],
        [
            InlineKeyboardButton(
                text="📖 Справка",
                callback_data="settings_help"
            )
        ]
    ]

    # Кнопка настроек календаря убрана для всех пользователей

    buttons.append([
        InlineKeyboardButton(
            text="🪙 Помочь проекту",
            callback_data="settings_donation"
        )
    ])

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
                text="⚙️ Лимиты и цены ИИ",
                callback_data="admin_ai_limits"
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


def create_premium_ai_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру премиум доступа к ИИ"""
    # Используем значения по умолчанию из ai_settings.py для кнопки
    # Реальные значения будут подставляться в тексте через динамические функции
    buttons = [
        [
            InlineKeyboardButton(
                text=f"⭐ Купить +{PREMIUM_REQUESTS_50} запросов ({PREMIUM_PRICE_50}₽)",
                callback_data="buy_premium_ai_50"
            )
        ],
        [
            InlineKeyboardButton(
                text="🌟 Купить за Telegram Stars",
                callback_data="buy_premium_stars"
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


def create_donation_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру пожертвований"""
    buttons = [
        [
            InlineKeyboardButton(
                text="⭐ Telegram Stars",
                callback_data="donate_stars_menu"
            )
        ],
        [
            InlineKeyboardButton(
                text="🪙 50₽",
                callback_data="donate_50"
            ),
            InlineKeyboardButton(
                text="🪙 100₽",
                callback_data="donate_100"
            )
        ],
        [
            InlineKeyboardButton(
                text="🪙 500₽",
                callback_data="donate_500"
            ),
            InlineKeyboardButton(
                text="🪙 1000₽",
                callback_data="donate_1000"
            )
        ],
        [
            InlineKeyboardButton(
                text="ℹ️ О пожертвованиях",
                callback_data="donation_info"
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


def create_admin_ai_limits_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру управления лимитами и ценами ИИ"""
    buttons = [
        [
            InlineKeyboardButton(
                text="📊 Изменить дневной лимит",
                callback_data="admin_change_daily_limit"
            )
        ],
        [
            InlineKeyboardButton(
                text="💰 Изменить цену пакета",
                callback_data="admin_change_package_price"
            )
        ],
        [
            InlineKeyboardButton(
                text="📦 Изменить размер пакета",
                callback_data="admin_change_package_size"
            )
        ],
        [
            InlineKeyboardButton(
                text="🤖 Режим ИИ для админа",
                callback_data="admin_toggle_ai_mode"
            )
        ],
        [
            InlineKeyboardButton(
                text="👥 Бесплатный премиум доступ",
                callback_data="admin_free_premium_users"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔄 Сбросить к умолчаниям",
                callback_data="admin_reset_ai_settings"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад к /admin панели",
                callback_data="admin_panel_refresh"
            )
        ]
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_free_premium_users_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру управления бесплатными премиум пользователями"""
    buttons = [
        [
            InlineKeyboardButton(
                text="➕ Добавить пользователя",
                callback_data="admin_add_free_premium_user"
            )
        ],
        [
            InlineKeyboardButton(
                text="➖ Удалить пользователя",
                callback_data="admin_remove_free_premium_user"
            )
        ],
        [
            InlineKeyboardButton(
                text="📋 Показать список",
                callback_data="admin_show_free_premium_users"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад к настройкам ИИ",
                callback_data="admin_ai_limits"
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
                text="📅 Православный календарь",
                callback_data="toggle_button_calendar"
            ),
            InlineKeyboardButton(
                text="✅",  # Включена по умолчанию
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


def create_stars_donation_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для пожертвований Telegram Stars"""
    buttons = [
        [
            InlineKeyboardButton(
                text="⭐ 1 Star",
                callback_data="donate_stars_1"
            ),
            InlineKeyboardButton(
                text="⭐ 10 Stars",
                callback_data="donate_stars_10"
            )
        ],
        [
            InlineKeyboardButton(
                text="⭐ 25 Stars",
                callback_data="donate_stars_25"
            ),
            InlineKeyboardButton(
                text="⭐ 50 Stars",
                callback_data="donate_stars_50"
            )
        ],
        [
            InlineKeyboardButton(
                text="⭐ 100 Stars",
                callback_data="donate_stars_100"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад к пожертвованиям",
                callback_data="settings_donation"
            )
        ]
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_premium_stars_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для покупки премиума за Stars"""
    buttons = [
        [
            InlineKeyboardButton(
                text="⭐ 10 запросов за 25 Stars",
                callback_data="buy_premium_stars_10"
            )
        ],
        [
            InlineKeyboardButton(
                text="⭐ 25 запросов за 50 Stars",
                callback_data="buy_premium_stars_25"
            )
        ],
        [
            InlineKeyboardButton(
                text="⭐ 50 запросов за 100 Stars",
                callback_data="buy_premium_stars_50"
            )
        ],
        [
            InlineKeyboardButton(
                text="💎 100 запросов за 180 Stars",
                callback_data="buy_premium_stars_100"
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
