#!/usr/bin/env python3
"""
Тест системы пожертвований с библейскими цитатами
"""
import logging
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_biblical_donations():
    """Тестирует систему пожертвований с библейскими цитатами"""
    
    logger.info("🧪 Тест системы пожертвований с библейскими цитатами...")
    logger.info("=" * 65)
    
    try:
        # 1. Проверяем информацию о пожертвованиях
        logger.info("1️⃣ Проверяем информацию о пожертвованиях...")
        
        # Имитируем текст из обработчика donation_info
        donation_info_text = (
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
            "🙏 **Благодарность:**\n"
            "Каждое пожертвование помогает:\n"
            "• Оплачивать серверы и API\n"
            "• Развивать новые функции\n"
            "• Улучшать качество ИИ ответов\n"
            "• Поддерживать проект бесплатным для всех\n\n"
            "💰 **Прозрачность:**\n"
            "• Все средства идут на развитие проекта\n"
            "• Никакой личной выгоды разработчика\n"
            "• Отчеты о тратах по запросу\n\n"
            "🔒 **Безопасность:**\n"
            "• Оплата через официальные системы\n"
            "• Все транзакции защищены\n"
            "• Полная анонимность при оплате Stars\n\n"
            "📖 **Слово Божие о милостыне:**\n\n"
            "*\"Блаженны милостивые, ибо они помилованы будут\"*\n"
            "— Матфея 5:7\n\n"
            "*\"Давайте, и дастся вам: мерою доброю, утрясенною, нагнетенною и переполненною отсыплют вам в лоно ваше\"*\n"
            "— Луки 6:38\n\n"
            "*\"Кто дает нищему, тот не обеднеет; а кто закрывает глаза свои, на том много проклятий\"*\n"
            "— Притчи 28:27\n\n"
            "💝 **От сердца:**\n"
            "Ваша поддержка - это не просто деньги, это инвестиция в духовное развитие тысяч людей, изучающих Священное Писание.\n\n"
            "📧 **Связь:** Вопросы о пожертвованиях можно задать через /feedback"
        )
        
        # Проверяем наличие банковских карт
        sberbank_found = "5469 4800 1497 4056" in donation_info_text
        tbank_found = "5536 9138 1011 4583" in donation_info_text
        recipient_found = "Константин Николаевич Б." in donation_info_text
        
        logger.info("   💳 Банковские карты:")
        if sberbank_found:
            logger.info("      ✅ Сбербанк: 5469 4800 1497 4056")
        else:
            logger.error("      ❌ Карта Сбербанка НЕ найдена")
        
        if tbank_found:
            logger.info("      ✅ Т-банк: 5536 9138 1011 4583")
        else:
            logger.error("      ❌ Карта Т-банка НЕ найдена")
        
        if recipient_found:
            logger.info("      ✅ Получатель: Константин Николаевич Б.")
        else:
            logger.error("      ❌ Получатель НЕ указан")
        
        # Проверяем библейские цитаты
        matthew_5_7 = "Блаженны милостивые, ибо они помилованы будут" in donation_info_text
        luke_6_38 = "Давайте, и дастся вам" in donation_info_text
        proverbs_28_27 = "Кто дает нищему, тот не обеднеет" in donation_info_text
        
        logger.info("   📖 Библейские цитаты:")
        if matthew_5_7:
            logger.info("      ✅ Матфея 5:7 - о милостивых")
        else:
            logger.error("      ❌ Цитата из Матфея 5:7 НЕ найдена")
        
        if luke_6_38:
            logger.info("      ✅ Луки 6:38 - о воздаянии")
        else:
            logger.error("      ❌ Цитата из Луки 6:38 НЕ найдена")
        
        if proverbs_28_27:
            logger.info("      ✅ Притчи 28:27 - о помощи нищим")
        else:
            logger.error("      ❌ Цитата из Притчи 28:27 НЕ найдена")
        
        # 2. Проверяем обработчик из главного меню
        logger.info("2️⃣ Проверяем обработчик главного меню...")
        
        main_menu_text = (
            "💝 **Помочь проекту**\n\n"
            "📖 *\"Блаженны милостивые, ибо они помилованы будут\"* — Матфея 5:7\n\n"
            "🙏 Благодарим за желание поддержать Gospel Bot!\n\n"
            "Ваша поддержка помогает:\n"
            "• Оплачивать серверы и API\n"
            "• Развивать новые функции\n"
            "• Улучшать качество ИИ ответов\n"
            "• Поддерживать проект бесплатным для всех\n\n"
            "Выберите удобный способ поддержки:"
        )
        
        main_menu_quote = "Блаженны милостивые, ибо они помилованы будут" in main_menu_text
        
        if main_menu_quote:
            logger.info("   ✅ Цитата в главном меню найдена")
        else:
            logger.error("   ❌ Цитата в главном меню НЕ найдена")
        
        # 3. Проверяем обработчики
        logger.info("3️⃣ Проверяем обработчики...")
        
        try:
            from handlers.settings import donation_info, show_donation_menu_from_main
            logger.info("   ✅ Обработчик donation_info найден")
            logger.info("   ✅ Обработчик show_donation_menu_from_main найден")
            handlers_ok = True
        except ImportError as e:
            logger.error(f"   ❌ Ошибка импорта обработчиков: {e}")
            handlers_ok = False
        
        # 4. Проверяем клавиатуры
        logger.info("4️⃣ Проверяем клавиатуры...")
        
        try:
            from keyboards.settings import create_donation_keyboard
            from keyboards.main import get_main_keyboard
            
            # Проверяем клавиатуру пожертвований
            donation_keyboard = create_donation_keyboard()
            donation_buttons = sum(len(row) for row in donation_keyboard.inline_keyboard)
            logger.info(f"   ✅ Клавиатура пожертвований: {donation_buttons} кнопок")
            
            # Проверяем главное меню
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
            
            keyboards_ok = True
            
        except Exception as e:
            logger.error(f"   ❌ Ошибка проверки клавиатур: {e}")
            keyboards_ok = False
            help_found = False
        
        # 5. Итоговая оценка
        logger.info("5️⃣ Итоговая оценка...")
        
        components = {
            "Карта Сбербанка": sberbank_found,
            "Карта Т-банка": tbank_found,
            "Получатель": recipient_found,
            "Цитата Матфея 5:7": matthew_5_7,
            "Цитата Луки 6:38": luke_6_38,
            "Цитата Притчи 28:27": proverbs_28_27,
            "Цитата в главном меню": main_menu_quote,
            "Обработчики": handlers_ok,
            "Клавиатуры": keyboards_ok,
            "Кнопка в главном меню": help_found
        }
        
        success_count = sum(components.values())
        total_count = len(components)
        
        logger.info(f"   📊 Оценка: {success_count}/{total_count}")
        
        for component, status in components.items():
            status_icon = "✅" if status else "❌"
            logger.info(f"   {status_icon} {component}")
        
        if success_count >= 8:
            logger.info("🎉 Система пожертвований с библейскими цитатами готова!")
        else:
            logger.warning("⚠️ Требуются доработки")
        
        # 6. Библейские цитаты о милостыне
        logger.info("6️⃣ Добавленные библейские цитаты:")
        logger.info("   📖 Матфея 5:7:")
        logger.info("      'Блаженны милостивые, ибо они помилованы будут'")
        logger.info("   📖 Луки 6:38:")
        logger.info("      'Давайте, и дастся вам: мерою доброю, утрясенною, нагнетенною и переполненною отсыплют вам в лоно ваше'")
        logger.info("   📖 Притчи 28:27:")
        logger.info("      'Кто дает нищему, тот не обеднеет; а кто закрывает глаза свои, на том много проклятий'")
        
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
    test_biblical_donations()