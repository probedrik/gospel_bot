#!/usr/bin/env python3
"""
Тест фильтрации callback_data для платежей
"""
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_callback_filtering():
    """Тестирует правильность фильтрации callback_data"""
    
    logger.info("🧪 Тестируем фильтрацию callback_data...")
    
    # Тестовые callback_data
    test_callbacks = [
        # Должны обрабатываться
        "donate_stars_1",
        "donate_stars_10", 
        "donate_stars_25",
        "donate_stars_50",
        "donate_stars_100",
        "buy_premium_stars_10",
        "buy_premium_stars_25",
        "buy_premium_stars_50",
        "buy_premium_stars_100",
        
        # НЕ должны обрабатываться
        "donate_stars_menu",
        "buy_premium_stars",
        "donate_menu",
        "settings_donation"
    ]
    
    logger.info("1️⃣ Тестируем пожертвования...")
    
    for callback_data in test_callbacks:
        # Проверяем условие для пожертвований
        starts_with_donate_stars = callback_data.startswith("donate_stars_")
        is_excluded = callback_data in ["donate_stars_menu"]
        should_process_donation = starts_with_donate_stars and not is_excluded
        
        if should_process_donation:
            # Проверяем, что можем извлечь число
            amount_str = callback_data.replace("donate_stars_", "")
            if amount_str.isdigit():
                logger.info(f"   ✅ {callback_data} → обработается как пожертвование {amount_str} Stars")
            else:
                logger.error(f"   ❌ {callback_data} → не число: '{amount_str}'")
        elif starts_with_donate_stars:
            logger.info(f"   ⚪ {callback_data} → исключен из обработки пожертвований")
    
    logger.info("2️⃣ Тестируем премиум запросы...")
    
    for callback_data in test_callbacks:
        # Проверяем условие для премиум запросов
        starts_with_premium = callback_data.startswith("buy_premium_stars_")
        is_excluded = callback_data in ["buy_premium_stars"]
        should_process_premium = starts_with_premium and not is_excluded
        
        if should_process_premium:
            # Проверяем, что это валидный пакет
            requests_str = callback_data.replace("buy_premium_stars_", "")
            from config.ai_settings import STAR_PREMIUM_PACKAGES
            if requests_str in STAR_PREMIUM_PACKAGES:
                logger.info(f"   ✅ {callback_data} → обработается как премиум пакет {requests_str}")
            else:
                logger.error(f"   ❌ {callback_data} → неизвестный пакет: '{requests_str}'")
        elif starts_with_premium:
            logger.info(f"   ⚪ {callback_data} → исключен из обработки премиум запросов")
    
    logger.info("🎉 Тест завершен!")

if __name__ == "__main__":
    test_callback_filtering()