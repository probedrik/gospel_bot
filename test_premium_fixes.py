#!/usr/bin/env python3
"""
Тест исправлений для премиум запросов
"""
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_premium_fixes():
    """Тестирует исправления для премиум запросов"""
    
    try:
        logger.info("🧪 Тестируем исправления премиум запросов...")
        
        # 1. Тест импорта PremiumManager
        logger.info("1️⃣ Тестируем импорт PremiumManager...")
        try:
            from services.premium_manager import PremiumManager
            premium_manager = PremiumManager()
            logger.info("   ✅ PremiumManager импортируется корректно")
        except Exception as e:
            logger.error(f"   ❌ Ошибка импорта PremiumManager: {e}")
            return
        
        # 2. Тест форматирования даты
        logger.info("2️⃣ Тестируем форматирование даты...")
        
        # Тестируем разные форматы даты
        test_dates = [
            "2025-08-15T06:10:22.418027",  # Supabase формат без Z
            "2025-08-15T06:10:22.418027Z", # Supabase формат с Z
            "2025-08-15T06:10:22+00:00",   # ISO формат с timezone
            datetime.now(),                 # datetime объект
            None                           # Пустая дата
        ]
        
        for i, test_date in enumerate(test_dates):
            try:
                logger.info(f"   Тест {i+1}: {type(test_date).__name__} = {test_date}")
                
                # Симулируем логику из handlers/settings.py
                first_purchase = ""
                if test_date:
                    if isinstance(test_date, str):
                        # Парсим ISO формат даты из Supabase
                        created_date = datetime.fromisoformat(test_date.replace('Z', '+00:00'))
                        first_purchase = f"📅 Первая покупка: {created_date.strftime('%d.%m.%Y')}"
                    else:
                        # Если это уже datetime объект
                        first_purchase = f"📅 Первая покупка: {test_date.strftime('%d.%m.%Y')}"
                else:
                    first_purchase = "📅 Первая покупка: не указана"
                
                logger.info(f"   ✅ Результат: {first_purchase}")
                
            except Exception as e:
                logger.error(f"   ❌ Ошибка форматирования: {e}")
        
        # 3. Тест получения статистики
        logger.info("3️⃣ Тестируем получение статистики...")
        
        # Инициализируем базу данных
        from database.universal_manager import universal_db_manager as db_manager
        await db_manager.initialize()
        
        test_user_id = 123456789
        stats = await premium_manager.get_user_premium_stats(test_user_id)
        
        logger.info(f"   📊 Статистика для пользователя {test_user_id}:")
        logger.info(f"      - Доступно: {stats['available']}")
        logger.info(f"      - Всего куплено: {stats['total_purchased']}")
        logger.info(f"      - Всего использовано: {stats['total_used']}")
        logger.info(f"      - Дата создания: {stats['created_at']} ({type(stats['created_at']).__name__})")
        
        # 4. Тест ai_quota_manager
        logger.info("4️⃣ Тестируем ai_quota_manager...")
        try:
            from services.ai_quota_manager import AIQuotaManager
            quota_manager = AIQuotaManager()
            quota_info = await quota_manager.get_user_quota_info(test_user_id)
            logger.info(f"   ✅ Квота получена: {quota_info}")
        except Exception as e:
            logger.error(f"   ❌ Ошибка ai_quota_manager: {e}")
        
        logger.info("🎉 Все тесты завершены!")
        
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
    asyncio.run(test_premium_fixes())