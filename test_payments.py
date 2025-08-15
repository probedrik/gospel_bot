#!/usr/bin/env python3
"""
Тест системы платежей Telegram Stars
"""
import asyncio
import logging
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_payments_system():
    """Тестирует систему платежей"""
    
    try:
        # Инициализируем базу данных
        from database.universal_manager import universal_db_manager as db_manager
        await db_manager.initialize()
        
        # Инициализируем менеджер премиум запросов
        from services.premium_manager import PremiumManager
        premium_manager = PremiumManager()
        
        test_user_id = 123456789
        
        logger.info("🧪 Начинаем тестирование системы платежей...")
        
        # 1. Проверяем начальный баланс
        logger.info("1️⃣ Проверяем начальный баланс премиум запросов...")
        initial_balance = await premium_manager.get_user_premium_requests(test_user_id)
        logger.info(f"   Начальный баланс: {initial_balance} запросов")
        
        # 2. Тестируем покупку премиум запросов через Stars
        logger.info("2️⃣ Тестируем покупку премиум запросов через Stars...")
        purchase_id = await premium_manager.create_star_premium_purchase(
            user_id=test_user_id,
            requests_count=10,
            amount_stars=25,
            telegram_payment_charge_id="test_charge_123"
        )
        
        if purchase_id:
            logger.info(f"   ✅ Покупка создана с ID: {purchase_id}")
            
            # Проверяем новый баланс
            new_balance = await premium_manager.get_user_premium_requests(test_user_id)
            logger.info(f"   Новый баланс: {new_balance} запросов")
            
            if new_balance == initial_balance + 10:
                logger.info("   ✅ Баланс обновлен корректно!")
            else:
                logger.error(f"   ❌ Ошибка баланса: ожидалось {initial_balance + 10}, получено {new_balance}")
        else:
            logger.error("   ❌ Не удалось создать покупку")
            new_balance = initial_balance  # Устанавливаем значение для дальнейшего использования
        
        # 3. Тестируем пожертвование через Stars
        logger.info("3️⃣ Тестируем пожертвование через Stars...")
        donation_id = await premium_manager.create_star_donation(
            user_id=test_user_id,
            amount_stars=50,
            telegram_payment_charge_id="test_donation_456",
            message="Тестовое пожертвование"
        )
        
        if donation_id:
            logger.info(f"   ✅ Пожертвование создано с ID: {donation_id}")
        else:
            logger.error("   ❌ Не удалось создать пожертвование")
        
        # 4. Проверяем статистику пользователя
        logger.info("4️⃣ Проверяем статистику пользователя...")
        stats = await premium_manager.get_user_premium_stats(test_user_id)
        logger.info(f"   Статистика: {stats}")
        
        # 5. Тестируем использование премиум запроса
        logger.info("5️⃣ Тестируем использование премиум запроса...")
        success = await premium_manager.use_premium_request(test_user_id)
        
        if success:
            logger.info("   ✅ Премиум запрос использован успешно")
            
            # Проверяем баланс после использования
            final_balance = await premium_manager.get_user_premium_requests(test_user_id)
            logger.info(f"   Финальный баланс: {final_balance} запросов")
            
            if final_balance == new_balance - 1:
                logger.info("   ✅ Баланс после использования корректен!")
            else:
                logger.error(f"   ❌ Ошибка баланса после использования: ожидалось {new_balance - 1}, получено {final_balance}")
        else:
            logger.error("   ❌ Не удалось использовать премиум запрос")
        
        logger.info("🎉 Тестирование завершено!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Закрываем соединения
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(test_payments_system())