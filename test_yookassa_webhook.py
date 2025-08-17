#!/usr/bin/env python3
"""
Тест обработки вебхуков ЮKassa
"""
import asyncio
import json
import logging
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_webhook_processing():
    """Тестирует обработку вебхуков ЮKassa"""
    
    logger.info("🧪 Тестируем обработку вебхуков ЮKassa...")
    
    try:
        # Инициализируем базу данных
        from database.universal_manager import universal_db_manager as db_manager
        await db_manager.initialize()
        
        # Инициализируем webhook handler
        from handlers.yookassa_webhook import YooKassaWebhookHandler
        webhook_handler = YooKassaWebhookHandler()
        
        # 1. Тестируем обработку успешного платежа за премиум запросы
        logger.info("1️⃣ Тестируем платеж за премиум запросы...")
        
        premium_payment_data = {
            "id": "test-premium-payment-123",
            "status": "succeeded",
            "amount": {
                "value": "100.00",
                "currency": "RUB"
            },
            "metadata": {
                "user_id": "123456789",
                "type": "premium_requests",
                "requests_count": "30"
            },
            "created_at": "2025-08-17T15:00:00.000Z"
        }
        
        await webhook_handler.handle_payment_succeeded(premium_payment_data)
        logger.info("   ✅ Платеж за премиум запросы обработан")
        
        # 2. Тестируем обработку пожертвования
        logger.info("2️⃣ Тестируем пожертвование...")
        
        donation_payment_data = {
            "id": "test-donation-payment-456",
            "status": "succeeded",
            "amount": {
                "value": "500.00",
                "currency": "RUB"
            },
            "metadata": {
                "user_id": "123456789",
                "type": "donation",
                "message": "Поддержка проекта"
            },
            "created_at": "2025-08-17T15:05:00.000Z"
        }
        
        await webhook_handler.handle_payment_succeeded(donation_payment_data)
        logger.info("   ✅ Пожертвование обработано")
        
        # 3. Проверяем записи в базе данных
        logger.info("3️⃣ Проверяем записи в базе данных...")
        
        if db_manager.is_supabase:
            # Проверяем premium_purchases
            premium_result = db_manager.manager.client.table('premium_purchases').select('*').eq('payment_id', 'test-premium-payment-123').execute()
            
            if premium_result.data:
                purchase = premium_result.data[0]
                logger.info(f"   ✅ Найдена запись о покупке премиум запросов:")
                logger.info(f"      ID: {purchase['id']}")
                logger.info(f"      User ID: {purchase['user_id']}")
                logger.info(f"      Requests: {purchase['requests_count']}")
                logger.info(f"      Amount: {purchase['amount_rub']}₽")
                logger.info(f"      Status: {purchase['payment_status']}")
            else:
                logger.warning("   ⚠️ Запись о покупке премиум запросов не найдена")
            
            # Проверяем donations
            donation_result = db_manager.manager.client.table('donations').select('*').eq('payment_id', 'test-donation-payment-456').execute()
            
            if donation_result.data:
                donation = donation_result.data[0]
                logger.info(f"   ✅ Найдена запись о пожертвовании:")
                logger.info(f"      ID: {donation['id']}")
                logger.info(f"      User ID: {donation['user_id']}")
                logger.info(f"      Amount: {donation['amount_rub']}₽")
                logger.info(f"      Message: {donation['message']}")
                logger.info(f"      Status: {donation['payment_status']}")
            else:
                logger.warning("   ⚠️ Запись о пожертвовании не найдена")
            
            # Проверяем баланс премиум запросов
            from services.premium_manager import PremiumManager
            premium_manager = PremiumManager()
            balance = await premium_manager.get_user_premium_requests(123456789)
            logger.info(f"   💎 Баланс премиум запросов пользователя 123456789: {balance}")
        
        # 4. Тестируем полный webhook запрос
        logger.info("4️⃣ Тестируем полный webhook запрос...")
        
        webhook_payload = {
            "event": "payment.succeeded",
            "object": premium_payment_data
        }
        
        # Симулируем aiohttp Request
        class MockRequest:
            def __init__(self, data):
                self.data = json.dumps(data).encode('utf-8')
                self.headers = {'X-Yookassa-Signature': 'test-signature'}
            
            async def read(self):
                return self.data
        
        mock_request = MockRequest(webhook_payload)
        response = await webhook_handler.handle_webhook(mock_request)
        
        logger.info(f"   📨 Webhook response status: {response.status}")
        if response.status == 200:
            logger.info("   ✅ Webhook обработан успешно")
        else:
            logger.warning(f"   ⚠️ Webhook вернул статус {response.status}")
        
        logger.info("🎉 Тестирование завершено!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Закрываем соединения
        try:
            await db_manager.close()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(test_webhook_processing())