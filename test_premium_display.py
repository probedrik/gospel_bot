#!/usr/bin/env python3
"""
Тест отображения премиум запросов в меню
"""
import asyncio
import logging
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_premium_display():
    """Тестирует отображение премиум запросов"""
    
    try:
        # Инициализируем базу данных
        from database.universal_manager import universal_db_manager as db_manager
        await db_manager.initialize()
        
        # Инициализируем менеджер премиум запросов
        from services.premium_manager import PremiumManager
        premium_manager = PremiumManager()
        
        test_user_id = 2040516595  # Ваш реальный ID
        
        logger.info("🧪 Проверяем отображение премиум запросов...")
        
        # 1. Получаем текущий баланс
        balance = await premium_manager.get_user_premium_requests(test_user_id)
        logger.info(f"💎 Текущий баланс: {balance} премиум запросов")
        
        # 2. Получаем статистику
        stats = await premium_manager.get_user_premium_stats(test_user_id)
        logger.info(f"📊 Статистика:")
        logger.info(f"   - Доступно: {stats['available']}")
        logger.info(f"   - Всего куплено: {stats['total_purchased']}")
        logger.info(f"   - Всего использовано: {stats['total_used']}")
        logger.info(f"   - Дата создания: {stats['created_at']}")
        
        # 3. Тестируем функцию из handlers/payments.py
        from handlers.payments import get_user_premium_balance
        balance_from_handler = await get_user_premium_balance(test_user_id)
        logger.info(f"💰 Баланс через handler: {balance_from_handler}")
        
        if balance == balance_from_handler:
            logger.info("✅ Баланс отображается корректно!")
        else:
            logger.error(f"❌ Несоответствие баланса: {balance} != {balance_from_handler}")
        
        # 4. Проверяем, что баланс больше 0
        if balance > 0:
            logger.info(f"✅ У пользователя есть премиум запросы: {balance}")
            logger.info("💡 В меню должна отображаться информация о премиум запросах")
        else:
            logger.info("ℹ️ У пользователя нет премиум запросов")
            logger.info("💡 В меню должно предлагаться купить премиум запросы")
        
        logger.info("🎉 Тест завершен!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Закрываем соединения
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(test_premium_display())