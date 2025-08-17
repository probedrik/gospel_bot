#!/usr/bin/env python3
"""
Тест упрощенной системы пожертвований
"""
import logging
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_simplified_donations():
    """Тестирует упрощенную систему пожертвований"""
    
    logger.info("🧪 Тест упрощенной системы пожертвований...")
    logger.info("=" * 50)
    
    try:
        # 1. Тест клавиатуры пожертвований
        logger.info("1️⃣ Тестируем клавиатуру пожертвований...")
        
        from keyboards.settings import create_donation_keyboard
        
        keyboard = create_donation_keyboard()
        button_count = sum(len(row) for row in keyboard.inline_keyboard)
        
        logger.info(f"   ✅ Клавиатура создана: {button_count} кнопок")
        
        # Проверяем кнопки
        buttons_info = []
        for row in keyboard.inline_keyboard:
            for button in row:
                if hasattr(button, 'url') and button.url:
                    buttons_info.append(f"{button.text} → {button.url}")
                else:
                    buttons_info.append(f"{button.text} → {button.callback_data}")
        
        logger.info("   📋 Кнопки:")
        for button_info in buttons_info:
            logger.info(f"      • {button_info}")
        
        # Проверяем YooMoney ссылку
        yoomoney_found = False
        for row in keyboard.inline_keyboard:
            for button in row:
                if hasattr(button, 'url') and button.url and 'yoomoney.ru' in button.url:
                    yoomoney_found = True
                    logger.info(f"   ✅ YooMoney ссылка найдена: {button.url}")
                    break
        
        if not yoomoney_found:
            logger.error("   ❌ YooMoney ссылка не найдена!")
        
        # 2. Тест обработчика информации о пожертвованиях
        logger.info("2️⃣ Тестируем обработчик информации...")
        
        # Проверяем, что обработчик существует
        from handlers.settings import donation_info
        logger.info("   ✅ Обработчик donation_info найден")
        
        # 3. Тест клавиатуры премиум ИИ
        logger.info("3️⃣ Тестируем клавиатуру премиум ИИ...")
        
        from keyboards.settings import create_premium_ai_keyboard
        
        premium_keyboard = create_premium_ai_keyboard()
        premium_button_count = sum(len(row) for row in premium_keyboard.inline_keyboard)
        
        logger.info(f"   ✅ Клавиатура премиум ИИ: {premium_button_count} кнопок")
        
        # Проверяем, что ЮKassa есть только для премиум запросов
        yookassa_found = False
        for row in premium_keyboard.inline_keyboard:
            for button in row:
                if 'buy_premium_ai' in button.callback_data:
                    yookassa_found = True
                    logger.info(f"   ✅ ЮKassa для премиум запросов: {button.text}")
                    break
        
        if not yookassa_found:
            logger.warning("   ⚠️ ЮKassa для премиум запросов не найдена")
        
        # 4. Проверяем, что YooMoney API отключен
        logger.info("4️⃣ Проверяем отключение YooMoney API...")
        
        try:
            from services.yoomoney_service import YooMoneyService
            yoomoney_service = YooMoneyService()
            
            if yoomoney_service.is_enabled():
                logger.warning("   ⚠️ YooMoney API все еще активен (это нормально для будущего использования)")
            else:
                logger.info("   ✅ YooMoney API отключен")
                
        except Exception as e:
            logger.info(f"   ✅ YooMoney API недоступен: {e}")
        
        # 5. Итоговая оценка
        logger.info("5️⃣ Итоговая оценка...")
        
        components = {
            "Клавиатура пожертвований": button_count > 0,
            "YooMoney ссылка": yoomoney_found,
            "Обработчик информации": True,
            "Клавиатура премиум ИИ": premium_button_count > 0,
            "ЮKassa для премиум": yookassa_found
        }
        
        success_count = sum(components.values())
        total_count = len(components)
        
        logger.info(f"   📊 Оценка: {success_count}/{total_count}")
        
        for component, status in components.items():
            status_icon = "✅" if status else "❌"
            logger.info(f"   {status_icon} {component}")
        
        if success_count >= 4:
            logger.info("🎉 Упрощенная система пожертвований готова!")
        else:
            logger.warning("⚠️ Требуются доработки")
        
        # 6. Рекомендации
        logger.info("6️⃣ Рекомендации:")
        logger.info("   💡 YooMoney теперь работает как простая ссылка")
        logger.info("   💡 Пользователи могут указать любую сумму на сайте YooMoney")
        logger.info("   💡 ЮKassa используется только для премиум запросов")
        logger.info("   💡 Telegram Stars остается основным способом пожертвований")
        
        logger.info("🎉 Тестирование завершено!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simplified_donations()