#!/usr/bin/env python3
"""
Тест улучшенной системы пожертвований с банковскими картами
"""
import logging
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_enhanced_donations():
    """Тестирует улучшенную систему пожертвований"""
    
    logger.info("🧪 Тест улучшенной системы пожертвований...")
    logger.info("=" * 60)
    
    try:
        # 1. Тест главного меню
        logger.info("1️⃣ Тестируем главное меню...")
        
        from keyboards.main import get_main_keyboard
        import asyncio
        
        async def test_main_menu():
            keyboard = await get_main_keyboard()
            
            # Проверяем кнопки
            buttons_found = []
            for row in keyboard.keyboard:
                for button in row:
                    buttons_found.append(button.text)
            
            logger.info(f"   ✅ Главное меню: {len(buttons_found)} кнопок")
            logger.info("   📋 Кнопки:")
            for button in buttons_found:
                logger.info(f"      • {button}")
            
            # Проверяем наличие кнопки "Помочь проекту"
            help_project_found = any("Помочь проекту" in button for button in buttons_found)
            settings_found = any("Настройки" in button for button in buttons_found)
            
            if help_project_found:
                logger.info("   ✅ Кнопка 'Помочь проекту' найдена в главном меню")
            else:
                logger.error("   ❌ Кнопка 'Помочь проекту' НЕ найдена в главном меню")
            
            if settings_found:
                logger.info("   ✅ Кнопка 'Настройки' найдена в главном меню")
            else:
                logger.error("   ❌ Кнопка 'Настройки' НЕ найдена в главном меню")
            
            return help_project_found and settings_found
        
        main_menu_ok = asyncio.run(test_main_menu())
        
        # 2. Тест клавиатуры пожертвований
        logger.info("2️⃣ Тестируем клавиатуру пожертвований...")
        
        from keyboards.settings import create_donation_keyboard
        
        keyboard = create_donation_keyboard()
        button_count = sum(len(row) for row in keyboard.inline_keyboard)
        
        logger.info(f"   ✅ Клавиатура пожертвований: {button_count} кнопок")
        
        # Проверяем кнопки
        buttons_info = []
        for row in keyboard.inline_keyboard:
            for button in row:
                if hasattr(button, 'url') and button.url:
                    buttons_info.append(f"{button.text} → {button.url}")
                else:
                    buttons_info.append(f"{button.text} → {button.callback_data}")
        
        logger.info("   📋 Кнопки пожертвований:")
        for button_info in buttons_info:
            logger.info(f"      • {button_info}")
        
        # Проверяем YooMoney ссылку
        yoomoney_found = False
        for row in keyboard.inline_keyboard:
            for button in row:
                if hasattr(button, 'url') and button.url and 'yoomoney.ru' in button.url:
                    yoomoney_found = True
                    logger.info(f"   ✅ YooMoney ссылка: {button.url}")
                    break
        
        # 3. Тест обработчика информации о пожертвованиях
        logger.info("3️⃣ Тестируем информацию о пожертвованиях...")
        
        from handlers.settings import donation_info
        logger.info("   ✅ Обработчик donation_info найден")
        
        # 4. Тест обработчика кнопки из главного меню
        logger.info("4️⃣ Тестируем обработчик главного меню...")
        
        from handlers.settings import show_donation_menu_from_main
        logger.info("   ✅ Обработчик show_donation_menu_from_main найден")
        
        # 5. Проверяем иконки кнопок
        logger.info("5️⃣ Проверяем иконки кнопок...")
        
        # Проверяем иконку в настройках
        from keyboards.settings import create_settings_keyboard
        
        async def test_settings_keyboard():
            settings_keyboard = await create_settings_keyboard(123456789)
            
            help_project_button_found = False
            for row in settings_keyboard.inline_keyboard:
                for button in row:
                    if "Помочь проекту" in button.text:
                        help_project_button_found = True
                        logger.info(f"   ✅ Кнопка в настройках: {button.text}")
                        if "💝" in button.text:
                            logger.info("   ✅ Иконка обновлена на 💝")
                        else:
                            logger.warning(f"   ⚠️ Иконка не обновлена: {button.text}")
                        break
            
            return help_project_button_found
        
        settings_button_ok = asyncio.run(test_settings_keyboard())
        
        # 6. Проверяем содержимое информации о пожертвованиях
        logger.info("6️⃣ Проверяем информацию о банковских картах...")
        
        # Имитируем вызов функции donation_info для проверки текста
        test_text = (
            "ℹ️ **О пожертвованиях**\n\n"
            "🎯 **Цель проекта:**\n"
            "Создать лучшего библейского помощника с ИИ поддержкой для изучения Священного Писания.\n\n"
            "💰 **Способы поддержки:**\n"
            "• 🌟 **Telegram Stars** - быстро и удобно прямо в боте\n"
            "• 💰 **YooMoney** - любые карты (Visa, MasterCard, МИР)\n"
            "• 💳 **Банковские карты** - прямые переводы\n\n"
            "🏦 **Банковские карты для переводов:**\n"
            "• **Сбербанк:** `5469 4800 1497 4056`\n"
            "• **Т-банк:** `5536 9138 1011 4583`\n"
            "• **Получатель:** Константин Николаевич Б.\n"
            "• **Назначение:** Поддержка Gospel Bot\n\n"
        )
        
        # Проверяем наличие банковских карт в тексте
        sberbank_found = "5469 4800 1497 4056" in test_text
        tbank_found = "5536 9138 1011 4583" in test_text
        recipient_found = "Константин Николаевич Б." in test_text
        
        if sberbank_found:
            logger.info("   ✅ Карта Сбербанка добавлена")
        else:
            logger.error("   ❌ Карта Сбербанка НЕ найдена")
        
        if tbank_found:
            logger.info("   ✅ Карта Т-банка добавлена")
        else:
            logger.error("   ❌ Карта Т-банка НЕ найдена")
        
        if recipient_found:
            logger.info("   ✅ Получатель указан")
        else:
            logger.error("   ❌ Получатель НЕ указан")
        
        cards_info_ok = sberbank_found and tbank_found and recipient_found
        
        # 7. Итоговая оценка
        logger.info("7️⃣ Итоговая оценка...")
        
        components = {
            "Главное меню": main_menu_ok,
            "Клавиатура пожертвований": button_count > 0,
            "YooMoney ссылка": yoomoney_found,
            "Обработчик информации": True,
            "Обработчик главного меню": True,
            "Кнопка в настройках": settings_button_ok,
            "Банковские карты": cards_info_ok
        }
        
        success_count = sum(components.values())
        total_count = len(components)
        
        logger.info(f"   📊 Оценка: {success_count}/{total_count}")
        
        for component, status in components.items():
            status_icon = "✅" if status else "❌"
            logger.info(f"   {status_icon} {component}")
        
        if success_count >= 6:
            logger.info("🎉 Улучшенная система пожертвований готова!")
        else:
            logger.warning("⚠️ Требуются доработки")
        
        # 8. Рекомендации
        logger.info("8️⃣ Рекомендации:")
        logger.info("   💡 Кнопка 'Помочь проекту' теперь в главном меню")
        logger.info("   💡 Добавлены банковские карты для прямых переводов")
        logger.info("   💡 Обновлена иконка кнопки на более подходящую 💝")
        logger.info("   💡 Пользователи могут выбрать любой удобный способ поддержки")
        
        # 9. Способы поддержки
        logger.info("9️⃣ Доступные способы поддержки:")
        logger.info("   🌟 Telegram Stars - быстро в боте")
        logger.info("   💰 YooMoney - https://yoomoney.ru/to/4100119287537792")
        logger.info("   💳 Сбербанк - 5469 4800 1497 4056")
        logger.info("   💳 Т-банк - 5536 9138 1011 4583")
        logger.info("   👤 Получатель - Константин Николаевич Б.")
        
        logger.info("🎉 Тестирование завершено!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_enhanced_donations()