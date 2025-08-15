#!/usr/bin/env python3
"""
Тест отображения инвойсов без черного окна
"""
import asyncio
import logging
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_invoice_parameters():
    """Проверяет параметры инвойса"""
    
    logger.info("🧪 Проверяем параметры инвойса...")
    
    # Читаем файл payments.py
    with open('handlers/payments.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Проверяем, что photo параметры удалены
    photo_params = ['photo_url', 'photo_size', 'photo_width', 'photo_height']
    found_params = []
    
    for param in photo_params:
        if param in content:
            found_params.append(param)
    
    if found_params:
        logger.error(f"❌ Найдены photo параметры: {found_params}")
        logger.error("Эти параметры создают черное окно в инвойсе!")
    else:
        logger.info("✅ Photo параметры удалены - черное окно не должно появляться")
    
    # Проверяем новые суммы пожертвований
    logger.info("🔍 Проверяем суммы пожертвований...")
    
    with open('keyboards/settings.py', 'r', encoding='utf-8') as f:
        keyboard_content = f.read()
    
    donation_amounts = ['donate_stars_1', 'donate_stars_10', 'donate_stars_25', 'donate_stars_50', 'donate_stars_100']
    found_amounts = []
    
    for amount in donation_amounts:
        if amount in keyboard_content:
            found_amounts.append(amount.replace('donate_stars_', '') + ' Stars')
    
    logger.info(f"💰 Доступные суммы пожертвований: {', '.join(found_amounts)}")
    
    if len(found_amounts) == 5:
        logger.info("✅ Все суммы пожертвований настроены корректно")
    else:
        logger.warning(f"⚠️ Ожидалось 5 сумм, найдено {len(found_amounts)}")
    
    logger.info("🎉 Проверка завершена!")

if __name__ == "__main__":
    test_invoice_parameters()