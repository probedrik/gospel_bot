"""
Менеджер премиум запросов и пожертвований
"""
import logging
from typing import Optional, Dict, Any
from database.universal_manager import universal_db_manager

logger = logging.getLogger(__name__)


class PremiumManager:
    """Менеджер премиум запросов и пожертвований"""
    
    def __init__(self):
        self.db = universal_db_manager
    
    async def get_user_premium_requests(self, user_id: int) -> int:
        """Получить количество премиум запросов пользователя"""
        try:
            query = "SELECT requests_count FROM premium_requests WHERE user_id = %s"
            result = await self.db.fetch_one(query, (user_id,))
            return result['requests_count'] if result else 0
        except Exception as e:
            logger.error(f"Ошибка получения премиум запросов для пользователя {user_id}: {e}")
            return 0
    
    async def add_premium_requests(self, user_id: int, count: int) -> bool:
        """Добавить премиум запросы пользователю"""
        try:
            # Проверяем, есть ли уже запись
            existing = await self.db.fetch_one(
                "SELECT requests_count, total_purchased FROM premium_requests WHERE user_id = %s",
                (user_id,)
            )
            
            if existing:
                # Обновляем существующую запись
                new_count = existing['requests_count'] + count
                new_total = existing['total_purchased'] + count
                
                query = """
                    UPDATE premium_requests 
                    SET requests_count = %s, total_purchased = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = %s
                """
                await self.db.execute(query, (new_count, new_total, user_id))
            else:
                # Создаем новую запись
                query = """
                    INSERT INTO premium_requests (user_id, requests_count, total_purchased)
                    VALUES (%s, %s, %s)
                """
                await self.db.execute(query, (user_id, count, count))
            
            logger.info(f"Добавлено {count} премиум запросов пользователю {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка добавления премиум запросов пользователю {user_id}: {e}")
            return False
    
    async def use_premium_request(self, user_id: int) -> bool:
        """Использовать один премиум запрос"""
        try:
            # Получаем текущее количество
            current = await self.get_user_premium_requests(user_id)
            
            if current <= 0:
                return False
            
            # Уменьшаем количество и увеличиваем счетчик использованных
            query = """
                UPDATE premium_requests 
                SET requests_count = requests_count - 1, 
                    total_used = total_used + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = %s AND requests_count > 0
            """
            result = await self.db.execute(query, (user_id,))
            
            if result:
                logger.info(f"Использован премиум запрос пользователем {user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Ошибка использования премиум запроса пользователем {user_id}: {e}")
            return False
    
    async def get_user_premium_stats(self, user_id: int) -> Dict[str, Any]:
        """Получить статистику премиум запросов пользователя"""
        try:
            query = """
                SELECT requests_count, total_purchased, total_used, created_at
                FROM premium_requests 
                WHERE user_id = %s
            """
            result = await self.db.fetch_one(query, (user_id,))
            
            if result:
                return {
                    'available': result['requests_count'],
                    'total_purchased': result['total_purchased'],
                    'total_used': result['total_used'],
                    'created_at': result['created_at']
                }
            else:
                return {
                    'available': 0,
                    'total_purchased': 0,
                    'total_used': 0,
                    'created_at': None
                }
                
        except Exception as e:
            logger.error(f"Ошибка получения статистики премиум запросов для пользователя {user_id}: {e}")
            return {
                'available': 0,
                'total_purchased': 0,
                'total_used': 0,
                'created_at': None
            }
    
    async def create_premium_purchase(self, user_id: int, requests_count: int, amount_rub: int, payment_id: str) -> bool:
        """Создать запись о покупке премиум запросов"""
        try:
            query = """
                INSERT INTO premium_purchases (user_id, requests_count, amount_rub, payment_id)
                VALUES (%s, %s, %s, %s)
            """
            await self.db.execute(query, (user_id, requests_count, amount_rub, payment_id))
            logger.info(f"Создана покупка премиум запросов: пользователь {user_id}, {requests_count} запросов, {amount_rub}₽")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка создания покупки премиум запросов: {e}")
            return False
    
    async def complete_premium_purchase(self, payment_id: str) -> bool:
        """Завершить покупку премиум запросов"""
        try:
            # Получаем данные покупки
            purchase = await self.db.fetch_one(
                "SELECT user_id, requests_count FROM premium_purchases WHERE payment_id = %s AND payment_status = 'pending'",
                (payment_id,)
            )
            
            if not purchase:
                logger.warning(f"Покупка с payment_id {payment_id} не найдена или уже завершена")
                return False
            
            # Обновляем статус покупки
            await self.db.execute(
                "UPDATE premium_purchases SET payment_status = 'completed', completed_at = CURRENT_TIMESTAMP WHERE payment_id = %s",
                (payment_id,)
            )
            
            # Добавляем премиум запросы пользователю
            success = await self.add_premium_requests(purchase['user_id'], purchase['requests_count'])
            
            if success:
                logger.info(f"Завершена покупка премиум запросов: payment_id {payment_id}")
                return True
            else:
                # Откатываем статус покупки если не удалось добавить запросы
                await self.db.execute(
                    "UPDATE premium_purchases SET payment_status = 'failed' WHERE payment_id = %s",
                    (payment_id,)
                )
                return False
                
        except Exception as e:
            logger.error(f"Ошибка завершения покупки премиум запросов: {e}")
            return False
    
    async def create_donation(self, user_id: int, amount_rub: int, payment_id: str, message: Optional[str] = None) -> bool:
        """Создать запись о пожертвовании"""
        try:
            query = """
                INSERT INTO donations (user_id, amount_rub, payment_id, message)
                VALUES (%s, %s, %s, %s)
            """
            await self.db.execute(query, (user_id, amount_rub, payment_id, message))
            logger.info(f"Создано пожертвование: пользователь {user_id}, {amount_rub}₽")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка создания пожертвования: {e}")
            return False
    
    async def complete_donation(self, payment_id: str) -> bool:
        """Завершить пожертвование"""
        try:
            result = await self.db.execute(
                "UPDATE donations SET payment_status = 'completed', completed_at = CURRENT_TIMESTAMP WHERE payment_id = %s AND payment_status = 'pending'",
                (payment_id,)
            )
            
            if result:
                logger.info(f"Завершено пожертвование: payment_id {payment_id}")
                return True
            else:
                logger.warning(f"Пожертвование с payment_id {payment_id} не найдено или уже завершено")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка завершения пожертвования: {e}")
            return False


# Глобальный экземпляр менеджера
premium_manager = PremiumManager()