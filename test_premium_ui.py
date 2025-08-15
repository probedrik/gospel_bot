#!/usr/bin/env python3
"""
Тест нового интерфейса премиум ИИ
"""
import asyncio
import logging
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_premium_ui():
    """Тестирует новый интерфейс премиум ИИ"""
    
    try:
        logger.info("🧪 Тестируем новый интерфейс премиум ИИ...")
        
        # 1. Проверяем клавиатуру
        logger.info("1️⃣ Проверяем клавиатуру премиум ИИ...")
        
        from keyboards.settings import create_premium_ai_keyboard
        keyboard = create_premium_ai_keyboard()
        
        # Извлекаем тексты кнопок
        button_texts = []
        for row in keyboard.inline_keyboard:
            for button in row:
                button_texts.append(button.text)
        
        logger.info("   📋 Кнопки в клавиатуре:")
        for i, text in enumerate(button_texts, 1):
            logger.info(f"      {i}. {text}")
        
        # Проверяем, что кнопки "Мои премиум запросы" нет
        if "📊 Мои премиум запросы" in button_texts:
            logger.error("   ❌ Кнопка 'Мои премиум запросы' все еще есть!")
        else:
            logger.info("   ✅ Кнопка 'Мои премиум запросы' успешно удалена")
        
        # 2. Тестируем генерацию текста
        logger.info("2️⃣ Тестируем генерацию текста с балансом...")
        
        # Инициализируем базу данных
        from database.universal_manager import universal_db_manager as db_manager
        await db_manager.initialize()
        
        # Получаем статистику для тестового пользователя
        from services.premium_manager import PremiumManager
        premium_manager = PremiumManager()
        
        test_user_id = 123456789
        stats = await premium_manager.get_user_premium_stats(test_user_id)
        
        logger.info(f"   📊 Статистика пользователя {test_user_id}:")
        logger.info(f"      - Доступно: {stats['available']}")
        logger.info(f"      - Всего куплено: {stats['total_purchased']}")
        logger.info(f"      - Всего использовано: {stats['total_used']}")
        logger.info(f"      - Дата создания: {stats['created_at']}")
        
        # 3. Тестируем форматирование даты
        logger.info("3️⃣ Тестируем форматирование даты...")
        
        first_purchase = ""
        if stats['created_at']:
            try:
                if isinstance(stats['created_at'], str):
                    from datetime import datetime
                    created_date = datetime.fromisoformat(stats['created_at'].replace('Z', '+00:00'))
                    first_purchase = f"📅 Первая покупка: {created_date.strftime('%d.%m.%Y')}"
                else:
                    first_purchase = f"📅 Первая покупка: {stats['created_at'].strftime('%d.%m.%Y')}"
            except Exception as e:
                logger.error(f"Ошибка форматирования даты: {e}")
                first_purchase = f"📅 Первая покупка: {stats['created_at']}"
        
        logger.info(f"   ✅ Дата отформатирована: {first_purchase}")
        
        # 4. Генерируем полный текст как в обработчике
        logger.info("4️⃣ Генерируем полный текст интерфейса...")
        
        from services.ai_settings_manager import ai_settings_manager
        daily_limit = await ai_settings_manager.get_daily_limit()
        
        balance_text = (
            f"📊 **Ваши премиум запросы**\n\n"
            f"⭐ **Доступно:** {stats['available']} запросов\n"
            f"📈 **Всего куплено:** {stats['total_purchased']}\n"
            f"📉 **Всего использовано:** {stats['total_used']}\n{first_purchase}\n\n"
        )
        
        info_text = (
            balance_text +
            "🧠 **Два уровня ИИ помощника:**\n"
            "• **Обычный ИИ:** Краткие ответы (до 2000 символов), базовая модель\n"
            "• **Премиум ИИ:** Подробный анализ (до 4000 символов), продвинутая модель\n\n"
            "🎯 **Принцип работы:**\n"
            f"• **Премиум пользователи всегда используют премиум ИИ!**\n"
            f"• Сначала тратятся дневные лимиты ({daily_limit} запросов с премиум ИИ)\n"
            "• Затем используются купленные премиум запросы\n"
            "• Премиум запросы никогда не сгорают\n\n"
            "ℹ️ **Как работает:**\n"
            "• Не сгорают со временем\n"
            "• Используются после дневных лимитов\n"
            "• Накапливаются при покупке"
        )
        
        logger.info("   📝 Сгенерированный текст:")
        logger.info("   " + "="*50)
        for line in info_text.split('\n'):
            logger.info(f"   {line}")
        logger.info("   " + "="*50)
        
        # 5. Проверяем длину текста
        text_length = len(info_text)
        logger.info(f"   📏 Длина текста: {text_length} символов")
        
        if text_length > 4096:
            logger.warning(f"   ⚠️ Текст слишком длинный для Telegram ({text_length} > 4096)")
        else:
            logger.info("   ✅ Длина текста в пределах лимита Telegram")
        
        logger.info("🎉 Тестирование завершено!")
        
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
    asyncio.run(test_premium_ui())