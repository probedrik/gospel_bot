#!/usr/bin/env python3
"""
Скрипт для инициализации таблицы ai_settings
"""
import asyncio
import logging
from database.universal_manager import universal_db_manager

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_ai_settings():
    """Инициализирует таблицу ai_settings"""
    try:
        logger.info("🚀 Инициализация таблицы ai_settings...")
        
        # Инициализируем менеджер базы данных
        await universal_db_manager.initialize()
        
        # Создаем таблицу ai_settings
        success = await universal_db_manager.create_ai_settings_table()
        
        if success:
            logger.info("✅ Таблица ai_settings успешно создана и инициализирована!")
            
            # Проверяем, что настройки созданы
            from services.ai_settings_manager import ai_settings_manager
            
            daily_limit = await ai_settings_manager.get_daily_limit()
            premium_price = await ai_settings_manager.get_premium_price()
            premium_requests = await ai_settings_manager.get_premium_requests()
            
            logger.info(f"📊 Текущие настройки:")
            logger.info(f"   • Дневной лимит: {daily_limit}")
            logger.info(f"   • Цена премиум пакета: {premium_price}₽")
            logger.info(f"   • Запросов в пакете: {premium_requests}")
            
        else:
            logger.error("❌ Ошибка создания таблицы ai_settings")
            
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации: {e}")
    finally:
        # Закрываем соединения
        await universal_db_manager.close()

if __name__ == "__main__":
    asyncio.run(init_ai_settings())