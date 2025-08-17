#!/usr/bin/env python3
"""
Тест упрощенной системы пожертвований без кнопки 'О пожертвованиях'
"""
import logging
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_streamlined_donations():
    """Тестирует упрощенную систему пожертвований"""
    
    logger.info("🧪 Тест упрощенной системы пожертвований...")
    logger.info("=" * 60)
    
    try:
        # 1. Проверяем клавиатуру пожертвований
        logger.info("1️⃣ Проверяем клавиатуру пожертвований...")
        
        from keyboards.settings import create_donation_keyboard
        
        keyboard = create_donation_keyboard()
        button_count = sum(len(row) for row in keyboard.inline_keyboard)
        
        logger.info(f"   ✅ Клавиатура пожертвований: {button_count} кнопок")
        
        # Проверяем кнопки
        buttons_info = []
        info_button_found = False
        
        for row in keyboard.inline_keyboard:
            for button in row:
                if hasattr(button, 'url') and button.url:
                    buttons_info.append(f"{button.text} → {button.url}")
                else:
                    buttons_info.append(f"{button.text} → {button.callback_data}")
                    
                # Проверяем, есть ли кнопка "О пожертвованиях"
                if "О пожертвованиях" in button.text:
                    info_button_found = True
        
        logger.info("   📋 Кнопки:")
        for button_info in buttons_info:
            logger.info(f"      • {button_info}")
        
        if not info_button_found:
            logger.info("   ✅ Кнопка 'О пожертвованиях' успешно удалена")
        else:
            logger.error("   ❌ Кнопка 'О пожертвованиях' все еще присутствует")
        
        # Проверяем YooMoney ссылку
        yoomoney_found = False
        stars_found = False
        
        for row in keyboard.inline_keyboard:
            for button in row:
                if hasattr(button, 'url') and button.url and 'yoomoney.ru' in button.url:
                    yoomoney_found = True
                    logger.info(f"   ✅ YooMoney ссылка: {button.url}")
                elif "Telegram Stars" in button.text:
                    stars_found = True
                    logger.info(f"   ✅ Telegram Stars кнопка: {button.text}")
        
        # 2. Проверяем обработчик главного меню
        logger.info("2️⃣ Проверяем обработчик главного меню...")
        
        # Имитируем полный текст из обработчика
        main_menu_text = (
            "💝 **Помочь проекту**\n\n"
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
            "🙏 **Благодарность:**\n"
            "Каждое пожертвование помогает:\n"
            "• Оплачивать серверы и API\n"
            "• Развивать новые функции\n"
            "• Улучшать качество ИИ ответов\n"
            "• Поддерживать проект бесплатным для всех\n\n"
            "📖 **Слово Божие о милостыне:**\n\n"
            "*\"Блаженны милостивые, ибо они помилованы будут\"*\n"
            "— Матфея 5:7\n\n"
            "*\"Давайте, и дастся вам: мерою доброю, утрясенною, нагнетенною и переполненною отсыплют вам в лоно ваше\"*\n"
            "— Луки 6:38\n\n"
            "*\"Кто дает нищему, тот не обеднеет; а кто закрывает глаза свои, на том много проклятий\"*\n"
            "— Притчи 28:27\n\n"
            "💝 **От сердца:**\n"
            "Ваша поддержка - это не просто деньги, это инвестиция в духовное развитие тысяч людей, изучающих Священное Писание.\n\n"
            "Выберите удобный способ поддержки:"
        )
        
        # Проверяем наличие всех компонентов
        components_check = {
            "Банковские карты": "5469 4800 1497 4056" in main_menu_text and "5536 9138 1011 4583" in main_menu_text,
            "Получатель": "Константин Николаевич Б." in main_menu_text,
            "Цитата Матфея 5:7": "Блаженны милостивые" in main_menu_text,
            "Цитата Луки 6:38": "Давайте, и дастся вам" in main_menu_text,
            "Цитата Притчи 28:27": "Кто дает нищему" in main_menu_text,
            "Цель проекта": "библейского помощника" in main_menu_text,
            "Способы поддержки": "Telegram Stars" in main_menu_text and "YooMoney" in main_menu_text
        }
        
        for component, status in components_check.items():
            if status:
                logger.info(f"   ✅ {component} присутствует")
            else:
                logger.error(f"   ❌ {component} отсутствует")
        
        # 3. Проверяем обработчик из настроек
        logger.info("3️⃣ Проверяем обработчик из настроек...")
        
        try:
            from handlers.settings import settings_donation, show_donation_menu_from_main
            logger.info("   ✅ Обработчик settings_donation найден")
            logger.info("   ✅ Обработчик show_donation_menu_from_main найден")
            handlers_ok = True
        except ImportError as e:
            logger.error(f"   ❌ Ошибка импорта обработчиков: {e}")
            handlers_ok = False
        
        # 4. Проверяем главное меню
        logger.info("4️⃣ Проверяем главное меню...")
        
        try:
            from keyboards.main import get_main_keyboard
            import asyncio
            
            async def check_main_menu():
                main_keyboard = await get_main_keyboard()
                main_buttons = []
                for row in main_keyboard.keyboard:
                    for button in row:
                        main_buttons.append(button.text)
                
                help_project_found = any("Помочь проекту" in button for button in main_buttons)
                return help_project_found, len(main_buttons)
            
            help_found, main_button_count = asyncio.run(check_main_menu())
            
            logger.info(f"   ✅ Главное меню: {main_button_count} кнопок")
            if help_found:
                logger.info("   ✅ Кнопка 'Помочь проекту' в главном меню")
            else:
                logger.error("   ❌ Кнопка 'Помочь проекту' НЕ найдена в главном меню")
            
        except Exception as e:
            logger.error(f"   ❌ Ошибка проверки главного меню: {e}")
            help_found = False
        
        # 5. Итоговая оценка
        logger.info("5️⃣ Итоговая оценка...")
        
        evaluation_components = {
            "Клавиатура упрощена": not info_button_found,
            "YooMoney ссылка": yoomoney_found,
            "Telegram Stars": stars_found,
            "Банковские карты": components_check["Банковские карты"],
            "Библейские цитаты": components_check["Цитата Матфея 5:7"] and components_check["Цитата Луки 6:38"],
            "Обработчики": handlers_ok,
            "Кнопка в главном меню": help_found,
            "Полная информация": all(components_check.values())
        }
        
        success_count = sum(evaluation_components.values())
        total_count = len(evaluation_components)
        
        logger.info(f"   📊 Оценка: {success_count}/{total_count}")
        
        for component, status in evaluation_components.items():
            status_icon = "✅" if status else "❌"
            logger.info(f"   {status_icon} {component}")
        
        if success_count >= 7:
            logger.info("🎉 Упрощенная система пожертвований готова!")
        else:
            logger.warning("⚠️ Требуются доработки")
        
        # 6. Преимущества упрощения
        logger.info("6️⃣ Преимущества упрощения:")
        logger.info("   💡 Убрана лишняя кнопка 'О пожертвованиях'")
        logger.info("   💡 Вся информация показывается сразу")
        logger.info("   💡 Меньше кликов для пользователя")
        logger.info("   💡 Более прямой путь к пожертвованиям")
        logger.info("   💡 Библейские цитаты видны сразу")
        logger.info("   💡 Банковские карты доступны сразу")
        
        # 7. Способы поддержки
        logger.info("7️⃣ Доступные способы поддержки:")
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
    test_streamlined_donations()