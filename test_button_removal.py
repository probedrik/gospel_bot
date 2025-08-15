#!/usr/bin/env python3
"""
Тест удаления кнопки "Как работает премиум"
"""
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_button_removal():
    """Тестирует удаление кнопки из клавиатуры"""
    
    logger.info("🧪 Тестируем удаление кнопки 'Как работает премиум'...")
    
    try:
        # Импортируем клавиатуру
        from keyboards.settings import create_premium_ai_keyboard
        keyboard = create_premium_ai_keyboard()
        
        # Извлекаем все тексты кнопок
        button_texts = []
        button_callbacks = []
        
        for row in keyboard.inline_keyboard:
            for button in row:
                button_texts.append(button.text)
                button_callbacks.append(button.callback_data)
        
        logger.info("📋 Текущие кнопки в клавиатуре премиум ИИ:")
        for i, (text, callback) in enumerate(zip(button_texts, button_callbacks), 1):
            logger.info(f"   {i}. {text} → {callback}")
        
        # Проверяем, что кнопки "Как работает премиум" нет
        removed_buttons = [
            "ℹ️ Как работает премиум",
            "📊 Мои премиум запросы"
        ]
        
        for removed_button in removed_buttons:
            if removed_button in button_texts:
                logger.error(f"   ❌ Кнопка '{removed_button}' все еще есть!")
            else:
                logger.info(f"   ✅ Кнопка '{removed_button}' успешно удалена")
        
        # Проверяем, что остались только нужные кнопки
        expected_buttons = [
            "⭐ Купить +30 запросов (100₽)",
            "🌟 Купить за Telegram Stars", 
            "⬅️ Назад к настройкам"
        ]
        
        logger.info("🎯 Ожидаемые кнопки:")
        for expected in expected_buttons:
            if expected in button_texts:
                logger.info(f"   ✅ {expected}")
            else:
                logger.warning(f"   ⚠️ Отсутствует: {expected}")
        
        # Проверяем общее количество кнопок
        logger.info(f"📊 Всего кнопок: {len(button_texts)}")
        
        if len(button_texts) == 3:
            logger.info("✅ Количество кнопок корректное (3)")
        else:
            logger.warning(f"⚠️ Неожиданное количество кнопок: {len(button_texts)}")
        
        logger.info("🎉 Тест завершен!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_button_removal()