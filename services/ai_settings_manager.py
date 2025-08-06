"""
Менеджер динамических настроек ИИ
"""
import logging
from typing import Optional, Dict, Any, Union
from database.universal_manager import universal_db_manager

logger = logging.getLogger(__name__)


class AISettingsManager:
    """Менеджер динамических настроек ИИ"""

    def __init__(self):
        self.db = universal_db_manager
        self._cache = {}  # Кэш настроек
        self._cache_ttl = 300  # TTL кэша в секундах (5 минут)
        self._cache_timestamps = {}  # Временные метки для TTL

    async def get_setting(self, key: str, default_value: Any = None) -> Any:
        """Получить значение настройки с кэшированием"""
        try:
            import time
            current_time = time.time()

            # Проверяем кэш с TTL
            if key in self._cache and key in self._cache_timestamps:
                if current_time - self._cache_timestamps[key] < self._cache_ttl:
                    return self._cache[key]
                else:
                    # Кэш устарел, удаляем
                    del self._cache[key]
                    del self._cache_timestamps[key]

            # Получаем из базы данных
            query = "SELECT setting_value, setting_type FROM ai_settings WHERE setting_key = ?"
            result = await self.db.fetch_one(query, (key,))

            if result:
                value = self._convert_value(
                    result['setting_value'], result['setting_type'])
                self._cache[key] = value
                self._cache_timestamps[key] = current_time
                return value
            else:
                # Если настройка не найдена, возвращаем значение по умолчанию
                return default_value

        except Exception as e:
            logger.error(f"Ошибка получения настройки {key}: {e}")
            return default_value

    async def set_setting(self, key: str, value: Any, setting_type: str = None, description: str = None) -> bool:
        """Установить значение настройки"""
        try:
            # Определяем тип автоматически, если не указан
            if setting_type is None:
                setting_type = self._get_type_name(value)

            # Конвертируем значение в строку для хранения
            str_value = str(value)

            # Проверяем, существует ли настройка
            existing = await self.db.fetch_one("SELECT setting_key FROM ai_settings WHERE setting_key = ?", (key,))

            if existing:
                # Обновляем существующую настройку
                query = """
                    UPDATE ai_settings 
                    SET setting_value = ?, setting_type = ?, description = COALESCE(?, description), updated_at = datetime('now')
                    WHERE setting_key = ?
                """
                await self.db.execute(query, (str_value, setting_type, description, key))
            else:
                # Вставляем новую настройку
                query = """
                    INSERT INTO ai_settings (setting_key, setting_value, setting_type, description)
                    VALUES (?, ?, ?, ?)
                """
                await self.db.execute(query, (key, str_value, setting_type, description))

            # Обновляем кэш
            import time
            self._cache[key] = value
            self._cache_timestamps[key] = time.time()

            logger.info(f"Настройка {key} обновлена: {value}")
            return True

        except Exception as e:
            logger.error(f"Ошибка установки настройки {key}: {e}")
            return False

    async def get_all_settings(self) -> Dict[str, Any]:
        """Получить все настройки"""
        try:
            query = "SELECT setting_key, setting_value, setting_type, description FROM ai_settings ORDER BY setting_key"
            results = await self.db.fetch_all(query)

            settings = {}
            for row in results:
                key = row['setting_key']
                value = self._convert_value(
                    row['setting_value'], row['setting_type'])
                settings[key] = {
                    'value': value,
                    'type': row['setting_type'],
                    'description': row['description']
                }
                # Обновляем кэш
                self._cache[key] = value

            return settings

        except Exception as e:
            logger.error(f"Ошибка получения всех настроек: {e}")
            return {}

    async def reset_to_defaults(self) -> bool:
        """Сбросить настройки к значениям по умолчанию"""
        try:
            # Импортируем значения по умолчанию из ai_settings.py
            from config.ai_settings import AI_DAILY_LIMIT, PREMIUM_AI_PACKAGE_PRICE, PREMIUM_AI_PACKAGE_REQUESTS

            defaults = {
                'ai_daily_limit': AI_DAILY_LIMIT,
                'premium_package_price': PREMIUM_AI_PACKAGE_PRICE,
                'premium_package_requests': PREMIUM_AI_PACKAGE_REQUESTS,
                'admin_premium_mode': True,
                'free_premium_users': '[]'
            }

            for key, value in defaults.items():
                await self.set_setting(key, value)

            logger.info("Настройки ИИ сброшены к значениям по умолчанию")
            return True

        except Exception as e:
            logger.error(f"Ошибка сброса настроек: {e}")
            return False

    def clear_cache(self):
        """Очистить кэш настроек"""
        self._cache.clear()
        self._cache_timestamps.clear()
        logger.info("Кэш настроек ИИ очищен")

    def _convert_value(self, str_value: str, setting_type: str) -> Any:
        """Конвертировать строковое значение в нужный тип"""
        try:
            if setting_type == 'integer':
                return int(str_value)
            elif setting_type == 'float':
                return float(str_value)
            elif setting_type == 'boolean':
                return str_value.lower() in ('true', '1', 'yes', 'on')
            else:  # string
                return str_value
        except (ValueError, TypeError):
            logger.warning(
                f"Не удалось конвертировать значение '{str_value}' в тип '{setting_type}'")
            return str_value

    def _get_type_name(self, value: Any) -> str:
        """Определить тип значения"""
        if isinstance(value, bool):
            return 'boolean'
        elif isinstance(value, int):
            return 'integer'
        elif isinstance(value, float):
            return 'float'
        else:
            return 'string'

    # Удобные методы для часто используемых настроек
    async def get_daily_limit(self) -> int:
        """Получить дневной лимит ИИ"""
        from config.ai_settings import AI_DAILY_LIMIT
        return await self.get_setting('ai_daily_limit', AI_DAILY_LIMIT)

    async def get_premium_price(self) -> int:
        """Получить цену премиум пакета"""
        from config.ai_settings import PREMIUM_AI_PACKAGE_PRICE
        return await self.get_setting('premium_package_price', PREMIUM_AI_PACKAGE_PRICE)

    async def get_premium_requests(self) -> int:
        """Получить количество запросов в премиум пакете"""
        from config.ai_settings import PREMIUM_AI_PACKAGE_REQUESTS
        return await self.get_setting('premium_package_requests', PREMIUM_AI_PACKAGE_REQUESTS)

    async def get_admin_premium_mode(self) -> bool:
        """Получить режим премиум ИИ для админа"""
        return await self.get_setting('admin_premium_mode', True)

    async def set_admin_premium_mode(self, enabled: bool) -> bool:
        """Установить режим премиум ИИ для админа"""
        return await self.set_setting('admin_premium_mode', enabled, 'boolean', 'Использует ли админ премиум ИИ по умолчанию')

    async def get_free_premium_users(self) -> set:
        """Получить список пользователей с бесплатным премиум доступом"""
        import json
        try:
            users_json = await self.get_setting('free_premium_users', '[]')
            users_list = json.loads(users_json)
            return set(users_list)
        except (json.JSONDecodeError, TypeError):
            logger.warning(
                "Ошибка парсинга списка бесплатных премиум пользователей")
            return set()

    async def set_free_premium_users(self, users: set) -> bool:
        """Установить список пользователей с бесплатным премиум доступом"""
        import json
        try:
            users_list = list(users)
            users_json = json.dumps(users_list)
            return await self.set_setting('free_premium_users', users_json, 'string', 'JSON список пользователей с бесплатным премиум доступом')
        except (TypeError, ValueError) as e:
            logger.error(f"Ошибка сериализации списка пользователей: {e}")
            return False

    async def add_free_premium_user(self, user_id: int) -> bool:
        """Добавить пользователя в список бесплатного премиум доступа"""
        users = await self.get_free_premium_users()
        users.add(user_id)
        return await self.set_free_premium_users(users)

    async def remove_free_premium_user(self, user_id: int) -> bool:
        """Удалить пользователя из списка бесплатного премиум доступа"""
        users = await self.get_free_premium_users()
        users.discard(user_id)
        return await self.set_free_premium_users(users)

    # === КАЛЕНДАРНЫЕ НАСТРОЙКИ ===

    async def is_calendar_enabled(self) -> bool:
        """Проверить, включена ли функция календаря"""
        return await self.get_setting('calendar_enabled', True)

    async def set_calendar_enabled(self, enabled: bool) -> bool:
        """Включить/выключить функцию календаря"""
        return await self.set_setting('calendar_enabled', str(enabled).lower(), 'boolean', 'Включена ли функция православного календаря')

    async def get_calendar_default_settings(self) -> dict:
        """Получить настройки календаря по умолчанию"""
        # Получаем настройки из БД
        header = await self.get_setting('calendar_default_header', True)
        lives = await self.get_setting('calendar_default_lives', 4)
        tropars = await self.get_setting('calendar_default_tropars', 0)
        scripture = await self.get_setting('calendar_default_scripture', 1)
        date_format = await self.get_setting('calendar_default_date_format', True)

        return {
            'header': header if isinstance(header, bool) else (header == 'true'),
            # 4 = основные святые в одном параграфе
            'lives': int(lives) if isinstance(lives, (int, str)) and str(lives).isdigit() else 4,
            # 0 = тропари отключены, 1 = с заголовком, 2 = без заголовка
            'tropars': int(tropars) if isinstance(tropars, (int, str)) and str(tropars).isdigit() else 0,
            # 0 = чтения отключены, 1 = с заголовком, 2 = без заголовка
            'scripture': int(scripture) if isinstance(scripture, (int, str)) and str(scripture).isdigit() else 1,
            'date_format': date_format if isinstance(date_format, bool) else (date_format == 'true')
        }

    async def set_calendar_default_setting(self, setting_name: str, value) -> bool:
        """Установить настройку календаря по умолчанию"""
        setting_key = f"calendar_default_{setting_name}"
        description = f"Настройка {setting_name} для календаря"

        # Определяем тип и значение в зависимости от переданного параметра
        if isinstance(value, bool):
            setting_type = 'boolean'
            setting_value = str(value).lower()
        elif isinstance(value, int):
            setting_type = 'integer'
            setting_value = str(value)
        else:
            setting_type = 'string'
            setting_value = str(value)

        return await self.set_setting(setting_key, setting_value, setting_type, description)


# Глобальный экземпляр менеджера
ai_settings_manager = AISettingsManager()
