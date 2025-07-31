"""
Менеджер квот ИИ с ежедневным обновлением
"""
import asyncio
import logging
from datetime import datetime, timedelta, date
from typing import Optional
from database.universal_manager import universal_db_manager as db_manager
from config.settings import ADMIN_USER_ID

logger = logging.getLogger(__name__)

# Настройки квот
ADMIN_DAILY_LIMIT = 1000  # Лимит для администраторов (практически без ограничений)
QUOTA_RESET_HOUR = 0  # Час сброса квот (00:00 UTC)


class AIQuotaManager:
    """Менеджер квот ИИ"""
    
    def __init__(self):
        self.last_reset_date = None
        self.reset_task = None
    
    async def start_quota_reset_scheduler(self):
        """Запускает планировщик сброса квот"""
        logger.info("🔄 Запуск планировщика сброса квот ИИ")
        self.reset_task = asyncio.create_task(self._quota_reset_loop())
    
    async def stop_quota_reset_scheduler(self):
        """Останавливает планировщик сброса квот"""
        if self.reset_task:
            self.reset_task.cancel()
            try:
                await self.reset_task
            except asyncio.CancelledError:
                pass
            logger.info("⏹️ Планировщик сброса квот остановлен")
    
    async def _quota_reset_loop(self):
        """Основной цикл сброса квот"""
        while True:
            try:
                # Вычисляем время до следующего сброса
                now = datetime.utcnow()
                next_reset = self._get_next_reset_time(now)
                sleep_seconds = (next_reset - now).total_seconds()
                
                logger.info(f"⏰ Следующий сброс квот: {next_reset.strftime('%Y-%m-%d %H:%M:%S')} UTC")
                logger.info(f"⏳ Ожидание {sleep_seconds:.0f} секунд до сброса")
                
                # Ждем до времени сброса
                await asyncio.sleep(sleep_seconds)
                
                # Выполняем сброс квот
                await self._reset_daily_quotas()
                
            except asyncio.CancelledError:
                logger.info("🛑 Планировщик квот отменен")
                break
            except Exception as e:
                logger.error(f"❌ Ошибка в планировщике квот: {e}")
                # Ждем 1 час перед повторной попыткой
                await asyncio.sleep(3600)
    
    def _get_next_reset_time(self, current_time: datetime) -> datetime:
        """Вычисляет время следующего сброса квот"""
        # Следующий сброс в QUOTA_RESET_HOUR:00:00
        next_reset = current_time.replace(
            hour=QUOTA_RESET_HOUR, 
            minute=0, 
            second=0, 
            microsecond=0
        )
        
        # Если время уже прошло сегодня, переносим на завтра
        if next_reset <= current_time:
            next_reset += timedelta(days=1)
        
        return next_reset
    
    async def _reset_daily_quotas(self):
        """Сбрасывает дневные квоты (очищает старые записи)"""
        try:
            today = datetime.utcnow().strftime('%Y-%m-%d')
            yesterday = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')
            
            logger.info(f"🔄 Сброс квот ИИ на {today}")
            
            # Здесь можно добавить логику очистки старых записей
            # Пока что просто логируем событие
            logger.info(f"✅ Квоты сброшены на {today}")
            
            self.last_reset_date = today
            
        except Exception as e:
            logger.error(f"❌ Ошибка при сбросе квот: {e}")
    
    async def get_user_quota_info(self, user_id: int) -> dict:
        """Получает информацию о квоте пользователя (включая премиум запросы)"""
        try:
            today_date = datetime.utcnow().date()
            today_str = today_date.strftime('%Y-%m-%d')
            
            # Получаем текущее использование
            used_today = await db_manager.get_ai_usage(user_id, today_date)
            
            # Определяем лимит пользователя
            if user_id == ADMIN_USER_ID:
                daily_limit = ADMIN_DAILY_LIMIT
            else:
                # Получаем динамический лимит из настроек
                from services.ai_settings_manager import ai_settings_manager
                daily_limit = await ai_settings_manager.get_daily_limit()
            
            # Вычисляем оставшиеся обычные запросы
            remaining = max(0, daily_limit - used_today)
            
            # Получаем информацию о премиум запросах
            from services.premium_manager import premium_manager
            premium_requests = await premium_manager.get_user_premium_requests(user_id)
            
            # Время до следующего сброса
            now = datetime.utcnow()
            next_reset = self._get_next_reset_time(now)
            hours_until_reset = int((next_reset - now).total_seconds() / 3600)
            
            # Общее количество доступных запросов
            total_available = remaining + premium_requests
            
            return {
                'user_id': user_id,
                'date': today_str,
                'daily_limit': daily_limit,
                'used_today': used_today,
                'remaining': remaining,
                'premium_requests': premium_requests,
                'total_available': total_available,
                'is_admin': user_id == ADMIN_USER_ID,
                'next_reset': next_reset,
                'hours_until_reset': hours_until_reset,
                'can_use_ai': remaining > 0 or premium_requests > 0 or user_id == ADMIN_USER_ID
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения квоты для пользователя {user_id}: {e}")
            # Используем значение по умолчанию из ai_settings.py при ошибке
            from config.ai_settings import AI_DAILY_LIMIT
            return {
                'user_id': user_id,
                'date': datetime.utcnow().strftime('%Y-%m-%d'),
                'daily_limit': AI_DAILY_LIMIT,
                'used_today': 0,
                'remaining': AI_DAILY_LIMIT,
                'premium_requests': 0,
                'total_available': AI_DAILY_LIMIT,
                'is_admin': False,
                'next_reset': self._get_next_reset_time(datetime.utcnow()),
                'hours_until_reset': 24,
                'can_use_ai': True,
                'error': str(e)
            }
    
    async def check_and_increment_usage(self, user_id: int) -> tuple[bool, str]:
        """Проверяет квоту и увеличивает использование (включая премиум запросы)
        
        Логика: Если у пользователя есть премиум запросы, он всегда использует премиум ИИ
        
        Returns:
            tuple[bool, str]: (можно_использовать, тип_ии)
            тип_ии: 'regular' для обычного ИИ, 'premium' для премиум ИИ
        """
        try:
            # Получаем информацию о квоте
            quota_info = await self.get_user_quota_info(user_id)
            
            # Проверяем, есть ли у пользователя премиум запросы или бесплатный премиум доступ
            from services.premium_manager import premium_manager
            from services.ai_settings_manager import ai_settings_manager
            
            premium_available = await premium_manager.get_user_premium_requests(user_id)
            free_premium_users = await ai_settings_manager.get_free_premium_users()
            is_free_premium_user = user_id in free_premium_users
            
            # Проверяем админский режим
            is_admin_premium_mode = False
            if user_id == ADMIN_USER_ID:
                is_admin_premium_mode = await ai_settings_manager.get_admin_premium_mode()
            
            # Если есть премиум запросы, бесплатный премиум доступ или админ в премиум режиме - используем премиум ИИ
            if premium_available > 0 or is_free_premium_user or is_admin_premium_mode:
                # Сначала пытаемся использовать обычные лимиты, но с премиум ИИ
                if quota_info['can_use_ai']:
                    await db_manager.increment_ai_usage(user_id)
                    user_type = "админ" if user_id == ADMIN_USER_ID else ("бесплатный премиум" if is_free_premium_user else "премиум")
                    logger.info(f"✅ {user_type.capitalize()} пользователь использовал дневной лимит с премиум ИИ {user_id}. "
                               f"Использовано: {quota_info['used_today'] + 1}/{quota_info['daily_limit']}")
                    return True, 'premium'
                else:
                    # Если дневные лимиты исчерпаны
                    if premium_available > 0:
                        # Используем премиум запросы (только для платных пользователей)
                        success = await premium_manager.use_premium_request(user_id)
                        if success:
                            logger.info(f"✅ Использован премиум запрос для пользователя {user_id}. "
                                       f"Осталось премиум: {premium_available - 1}")
                            return True, 'premium'
                    elif is_free_premium_user or is_admin_premium_mode:
                        # Бесплатные премиум пользователи и админ в премиум режиме не могут использовать ИИ после исчерпания дневных лимитов
                        logger.warning(f"⚠️ Бесплатный премиум пользователь {user_id} исчерпал дневные лимиты")
                        return False, 'none'
            
            # Если нет премиум запросов - используем обычную логику
            elif quota_info['can_use_ai']:
                await db_manager.increment_ai_usage(user_id)
                logger.info(f"✅ Использован обычный ИИ запрос для пользователя {user_id}. "
                           f"Использовано: {quota_info['used_today'] + 1}/{quota_info['daily_limit']}")
                return True, 'regular'
            
            logger.warning(f"⚠️ Пользователь {user_id} исчерпал все лимиты ИИ")
            return False, 'none'
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки квоты для пользователя {user_id}: {e}")
            return False, 'none'
    
    async def get_quota_stats(self) -> dict:
        """Получает общую статистику по квотам"""
        try:
            today = datetime.utcnow().strftime('%Y-%m-%d')
            
            # Здесь можно добавить логику получения общей статистики
            # Пока что возвращаем базовую информацию
            
            return {
                'date': today,
                'default_limit': DEFAULT_DAILY_LIMIT,
                'admin_limit': ADMIN_DAILY_LIMIT,
                'reset_hour': QUOTA_RESET_HOUR,
                'last_reset': self.last_reset_date,
                'scheduler_running': self.reset_task is not None and not self.reset_task.done()
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики квот: {e}")
            return {
                'error': str(e)
            }


# Глобальный экземпляр менеджера квот
ai_quota_manager = AIQuotaManager()