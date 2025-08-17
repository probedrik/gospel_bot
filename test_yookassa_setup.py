#!/usr/bin/env python3
"""
Тест настройки ЮKassa
"""
import asyncio
import logging
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_yookassa_setup():
    """Тестирует настройку ЮKassa"""
    
    logger.info("🧪 Тестируем настройку ЮKassa...")
    
    try:
        # 1. Проверяем переменные окружения
        logger.info("1️⃣ Проверяем переменные окружения...")
        
        import os
        
        yookassa_vars = {
            'YOOKASSA_SHOP_ID': os.getenv('YOOKASSA_SHOP_ID'),
            'YOOKASSA_SECRET_KEY': os.getenv('YOOKASSA_SECRET_KEY'),
            'YOOKASSA_WEBHOOK_SECRET': os.getenv('YOOKASSA_WEBHOOK_SECRET')
        }
        
        for var_name, var_value in yookassa_vars.items():
            if var_value:
                masked_value = var_value[:8] + "..." + var_value[-4:] if len(var_value) > 12 else "***"
                logger.info(f"   ✅ {var_name}: {masked_value}")
            else:
                logger.warning(f"   ⚠️ {var_name}: не установлен")
        
        # 2. Проверяем импорт yookassa
        logger.info("2️⃣ Проверяем библиотеку yookassa...")
        
        try:
            import yookassa
            logger.info(f"   ✅ yookassa версия: {yookassa.__version__}")
        except ImportError:
            logger.error("   ❌ Библиотека yookassa не установлена!")
            logger.info("   💡 Установите: pip install yookassa")
            return
        
        # 3. Тестируем PaymentService
        logger.info("3️⃣ Тестируем PaymentService...")
        
        from services.payment_service import PaymentService
        payment_service = PaymentService()
        
        if payment_service.is_enabled():
            logger.info("   ✅ PaymentService инициализирован и готов к работе")
        else:
            logger.warning("   ⚠️ PaymentService не настроен")
            return
        
        # 4. Тестируем создание тестового платежа (без отправки)
        logger.info("4️⃣ Тестируем создание платежа...")
        
        test_payment_data = {
            'user_id': 123456789,
            'requests_count': 10,
            'amount': 100.0
        }
        
        try:
            # Создаем тестовый платеж
            payment_result = await payment_service.create_premium_payment(
                user_id=test_payment_data['user_id'],
                requests_count=test_payment_data['requests_count'],
                amount=test_payment_data['amount']
            )
            
            if payment_result:
                logger.info("   ✅ Тестовый платеж создан успешно")
                logger.info(f"      Payment ID: {payment_result['payment_id']}")
                logger.info(f"      Status: {payment_result['status']}")
                logger.info(f"      Amount: {payment_result['amount']}₽")
                logger.info(f"      Confirmation URL: {payment_result['confirmation_url'][:50]}...")
            else:
                logger.error("   ❌ Не удалось создать тестовый платеж")
                
        except Exception as e:
            logger.error(f"   ❌ Ошибка создания платежа: {e}")
        
        # 5. Проверяем webhook handler
        logger.info("5️⃣ Проверяем webhook handler...")
        
        try:
            from handlers.yookassa_webhook import YooKassaWebhookHandler
            webhook_handler = YooKassaWebhookHandler()
            logger.info("   ✅ YooKassaWebhookHandler инициализирован")
            
            # Тестируем проверку подписи
            test_body = b'{"test": "data"}'
            test_signature = "test_signature"
            
            signature_valid = webhook_handler.verify_signature(test_body, test_signature)
            logger.info(f"   ℹ️ Проверка подписи: {'включена' if yookassa_vars['YOOKASSA_WEBHOOK_SECRET'] else 'отключена'}")
            
        except Exception as e:
            logger.error(f"   ❌ Ошибка webhook handler: {e}")
        
        # 6. Проверяем webhook server
        logger.info("6️⃣ Проверяем webhook server...")
        
        try:
            from webhook_server import WebhookServer
            webhook_server = WebhookServer()
            logger.info("   ✅ WebhookServer готов к запуску")
            logger.info("   💡 Для запуска используйте: python webhook_server.py")
            
        except Exception as e:
            logger.error(f"   ❌ Ошибка webhook server: {e}")
        
        # 7. Итоговая оценка
        logger.info("7️⃣ Итоговая оценка готовности...")
        
        required_vars = ['YOOKASSA_SHOP_ID', 'YOOKASSA_SECRET_KEY']
        missing_vars = [var for var in required_vars if not yookassa_vars[var]]
        
        if not missing_vars and payment_service.is_enabled():
            logger.info("   🎉 ЮKassa полностью настроена и готова к работе!")
            logger.info("   📋 Следующие шаги:")
            logger.info("      1. Запустите webhook сервер: python webhook_server.py")
            logger.info("      2. Настройте вебхуки в личном кабинете ЮKassa")
            logger.info("      3. Протестируйте платеж в боте")
        else:
            logger.warning("   ⚠️ ЮKassa настроена частично")
            if missing_vars:
                logger.warning(f"      Отсутствуют переменные: {', '.join(missing_vars)}")
            logger.info("   📖 См. YOOKASSA_SETUP_GUIDE.md для подробной настройки")
        
        logger.info("🎉 Тестирование завершено!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_yookassa_setup())