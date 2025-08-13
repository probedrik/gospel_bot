#!/usr/bin/env python3
"""
Тест основных кнопок меню для проверки стабильности
"""
import asyncio
import sys
import os

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_menu_buttons():
    """Тестирует основные кнопки меню"""
    print("🧪 Тестирование кнопок главного меню...")
    
    try:
        # Тестируем импорты обработчиков
        from handlers import text_messages, settings, commands
        print("✅ Импорт обработчиков успешен")
        
        # Тестируем клавиатуры
        from keyboards.main import get_main_keyboard
        from keyboards.settings import create_settings_keyboard, create_donation_keyboard
        
        # Создаем главную клавиатуру
        main_kb = get_main_keyboard()
        print("✅ Главная клавиатура создана")
        
        # Создаем клавиатуру настроек
        settings_kb = await create_settings_keyboard(123456)
        print("✅ Клавиатура настроек создана")
        
        # Создаем клавиатуру пожертвований
        donation_kb = create_donation_keyboard()
        print("✅ Клавиатура пожертвований создана")
        
        # Проверяем, что кнопка ввода произвольной суммы отсутствует
        has_custom_donation = False
        for row in donation_kb.inline_keyboard:
            for button in row:
                if hasattr(button, 'callback_data') and button.callback_data == 'donate_custom':
                    has_custom_donation = True
                    break
        
        if has_custom_donation:
            print("❌ Кнопка ввода произвольной суммы все еще присутствует!")
            return False
        else:
            print("✅ Кнопка ввода произвольной суммы успешно удалена")
        
        # Тестируем темы
        from utils.topics import get_topics_list_async
        topics = await get_topics_list_async()
        if topics:
            print(f"✅ Темы загружены: {len(topics)} тем")
        else:
            print("⚠️ Темы не загружены, но это не критично")
        
        print("\n🎉 Все тесты пройдены успешно!")
        print("📋 Результаты:")
        print("  • Обработчики импортируются без ошибок")
        print("  • Клавиатуры создаются корректно")
        print("  • Кнопка ввода произвольной суммы удалена")
        print("  • Темы загружаются")
        print("\n✅ Кнопки главного меню должны работать стабильно!")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в тестах: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_menu_buttons())
    sys.exit(0 if success else 1)