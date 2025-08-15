"""
Менеджер премиум запросов и пожертвований
"""
import logging
from typing import Optional, Dict, Any, List
from database.universal_manager import universal_db_manager

logger = logging.getLogger(__name__)


class PremiumManager:
    """Менеджер премиум запросов и пожертвований"""

    def __init__(self):
        self.db = universal_db_manager

    async def get_user_premium_requests(self, user_id: int) -> int:
        """Получить количество премиум запросов пользователя"""
        try:
            return await self.db.get_user_premium_requests(user_id)
        except Exception as e:
            logger.error(
                f"Ошибка получения премиум запросов для пользователя {user_id}: {e}")
            return 0

    async def add_premium_requests(self, user_id: int, count: int) -> bool:
        """Добавить премиум запросы пользователю"""
        try:
            return await self.db.add_premium_requests(user_id, count)
        except Exception as e:
            logger.error(f"Ошибка добавления премиум запросов: {e}")
            return False

    async def use_premium_request(self, user_id: int) -> bool:
        """Использовать один премиум запрос"""
        try:
            # Получаем текущее количество
            current = await self.get_user_premium_requests(user_id)

            if current <= 0:
                return False

            # Используем метод universal_db_manager для уменьшения запросов
            if self.db.is_supabase:
                # Для Supabase используем клиент напрямую
                result = self.db.manager.client.table('premium_requests').update({
                    'requests_count': current - 1,
                    'total_used': self.db.manager.client.table('premium_requests').select('total_used').eq('user_id', user_id).execute().data[0]['total_used'] + 1 if self.db.manager.client.table('premium_requests').select('total_used').eq('user_id', user_id).execute().data else 1,
                    'updated_at': 'now()'
                }).eq('user_id', user_id).execute()
                
                if result.data:
                    logger.info(f"Использован премиум запрос пользователем {user_id}")
                    return True
            else:
                # Для других БД используем SQL
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
            if self.db.is_supabase:
                # Для Supabase используем клиент
                result = self.db.manager.client.table('premium_requests').select('*').eq('user_id', user_id).execute()
                
                if result.data:
                    data = result.data[0]
                    return {
                        'available': data.get('requests_count', 0),
                        'total_purchased': data.get('total_purchased', 0),
                        'total_used': data.get('total_used', 0),
                        'created_at': data.get('created_at')
                    }
            else:
                # Для других БД используем SQL
                query = "SELECT * FROM premium_requests WHERE user_id = %s"
                result = await self.db.fetch_one(query, (user_id,))
                
                if result:
                    return {
                        'available': result.get('requests_count', 0),
                        'total_purchased': result.get('total_purchased', 0),
                        'total_used': result.get('total_used', 0),
                        'created_at': result.get('created_at')
                    }

            # Если записи нет, возвращаем нули
            return {
                'available': 0,
                'total_purchased': 0,
                'total_used': 0,
                'created_at': None
            }

        except Exception as e:
            logger.error(f"Ошибка получения статистики премиум запросов: {e}")
            return {
                'available': 0,
                'total_purchased': 0,
                'total_used': 0,
                'created_at': None
            }

    # === МЕТОДЫ ДЛЯ РАБОТЫ С TELEGRAM STARS ===

    async def create_star_donation(self, user_id: int, amount_stars: int, telegram_payment_charge_id: str, message: Optional[str] = None) -> Optional[int]:
        """Создать запись о пожертвовании через Stars"""
        try:
            if self.db.is_supabase:
                # Для Supabase используем клиент
                donation_result = self.db.manager.client.table('donations').insert({
                    'user_id': user_id,
                    'amount_rub': 0,  # Для Stars платежей указываем 0 рублей
                    'amount_stars': amount_stars,
                    'payment_method': 'stars',
                    'telegram_payment_charge_id': telegram_payment_charge_id,
                    'message': message,
                    'payment_status': 'completed',
                    'completed_at': 'now()'
                }).execute()
                
                if donation_result.data:
                    donation_id = donation_result.data[0]['id']
                    
                    # Создаем запись в star_transactions
                    await self._create_star_transaction(user_id, telegram_payment_charge_id, amount_stars, 'donation', donation_id)
                    
                    logger.info(f"Создано пожертвование Stars: пользователь {user_id}, {amount_stars} Stars")
                    return donation_id
            else:
                # Для других БД используем SQL
                query = """
                    INSERT INTO donations (user_id, amount_stars, payment_method, telegram_payment_charge_id, message, payment_status)
                    VALUES (%s, %s, 'stars', %s, %s, 'completed')
                    RETURNING id
                """
                result = await self.db.fetch_one(query, (user_id, amount_stars, telegram_payment_charge_id, message))

                if result:
                    donation_id = result['id']
                    # Создаем запись в star_transactions
                    await self._create_star_transaction(user_id, telegram_payment_charge_id, amount_stars, 'donation', donation_id)
                    logger.info(f"Создано пожертвование Stars: пользователь {user_id}, {amount_stars} Stars")
                    return donation_id
            
            return None

        except Exception as e:
            logger.error(f"Ошибка создания пожертвования Stars: {e}")
            return None

    async def create_star_premium_purchase(self, user_id: int, requests_count: int, amount_stars: int, telegram_payment_charge_id: str) -> Optional[int]:
        """Создать запись о покупке премиум запросов через Stars"""
        try:
            if self.db.is_supabase:
                # Для Supabase используем клиент
                purchase_result = self.db.manager.client.table('premium_purchases').insert({
                    'user_id': user_id,
                    'requests_count': requests_count,
                    'amount_rub': 0,  # Для Stars платежей указываем 0 рублей
                    'amount_stars': amount_stars,
                    'payment_method': 'stars',
                    'telegram_payment_charge_id': telegram_payment_charge_id,
                    'payment_status': 'completed',
                    'completed_at': 'now()'
                }).execute()
                
                if purchase_result.data:
                    purchase_id = purchase_result.data[0]['id']
                    
                    # Добавляем запросы пользователю
                    await self.add_premium_requests(user_id, requests_count)
                    
                    # Создаем запись в star_transactions
                    await self._create_star_transaction(user_id, telegram_payment_charge_id, amount_stars, 'premium_purchase', purchase_id)
                    
                    logger.info(f"Покупка премиум запросов за Stars: пользователь {user_id}, {requests_count} запросов за {amount_stars} Stars")
                    return purchase_id
            else:
                # Для других БД используем SQL
                query = """
                    INSERT INTO premium_purchases (user_id, requests_count, amount_stars, payment_method, telegram_payment_charge_id, payment_status)
                    VALUES (%s, %s, %s, 'stars', %s, 'completed')
                    RETURNING id
                """
                result = await self.db.fetch_one(query, (user_id, requests_count, amount_stars, telegram_payment_charge_id))

                if result:
                    purchase_id = result['id']
                    # Добавляем запросы пользователю
                    await self.add_premium_requests(user_id, requests_count)
                    # Создаем запись в star_transactions
                    await self._create_star_transaction(user_id, telegram_payment_charge_id, amount_stars, 'premium_purchase', purchase_id)
                    logger.info(f"Покупка премиум запросов за Stars: пользователь {user_id}, {requests_count} запросов за {amount_stars} Stars")
                    return purchase_id
            
            return None

        except Exception as e:
            logger.error(f"Ошибка покупки премиум запросов за Stars: {e}")
            return None

    async def _create_star_transaction(self, user_id: int, transaction_id: str, amount_stars: int, transaction_type: str, related_id: int) -> bool:
        """Создать запись о транзакции Stars"""
        try:
            if self.db.is_supabase:
                # Для Supabase используем клиент
                result = self.db.manager.client.table('star_transactions').insert({
                    'user_id': user_id,
                    'transaction_id': transaction_id,
                    'amount_stars': amount_stars,
                    'transaction_type': transaction_type,
                    'related_id': related_id,
                    'status': 'completed',
                    'completed_at': 'now()'
                }).execute()
                
                return bool(result.data)
            else:
                # Для других БД используем SQL
                query = """
                    INSERT INTO star_transactions (user_id, transaction_id, amount_stars, transaction_type, related_id, status)
                    VALUES (%s, %s, %s, %s, %s, 'completed')
                """
                await self.db.execute(query, (user_id, transaction_id, amount_stars, transaction_type, related_id))
                return True

        except Exception as e:
            logger.error(f"Ошибка создания транзакции Stars: {e}")
            return False