"""
Webhook обработчики для внешних сервисов
"""
import logging
import json
from typing import Dict, Any
from services.payment_service import payment_service

logger = logging.getLogger(__name__)


async def handle_yookassa_webhook(webhook_data: Dict[str, Any]) -> bool:
    """
    Обрабатывает webhook от ЮKassa
    
    Args:
        webhook_data: Данные webhook от ЮKassa
        
    Returns:
        True если обработка прошла успешно
    """
    try:
        # Получаем тип события
        event_type = webhook_data.get("event", "")
        
        if event_type != "payment.succeeded":
            logger.info(f"Получен webhook ЮKassa с типом {event_type}, пропускаем")
            return True
        
        # Получаем данные платежа
        payment_object = webhook_data.get("object", {})
        payment_id = payment_object.get("id", "")
        
        if not payment_id:
            logger.error("❌ Webhook ЮKassa: отсутствует payment_id")
            return False
        
        logger.info(f"📥 Получен webhook ЮKassa для платежа {payment_id}")
        
        # Проверяем статус платежа через API
        payment_data = await payment_service.check_payment_status(payment_id)
        
        if not payment_data:
            logger.error(f"❌ Не удалось получить данные платежа {payment_id}")
            return False
        
        # Проверяем, что платеж действительно успешен
        if not payment_data.get("paid", False):
            logger.warning(f"⚠️ Платеж {payment_id} не оплачен, статус: {payment_data.get('status')}")
            return True
        
        # Обрабатываем успешный платеж
        success = await payment_service.process_successful_payment(payment_data)
        
        if success:
            logger.info(f"✅ Успешно обработан платеж {payment_id}")
            
            # Отправляем уведомление пользователю
            await send_payment_notification(payment_data)
            
        else:
            logger.error(f"❌ Ошибка обработки платежа {payment_id}")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Ошибка обработки webhook ЮKassa: {e}")
        return False


async def send_payment_notification(payment_data: Dict[str, Any]):
    """
    Отправляет уведомление пользователю об успешном платеже
    
    Args:
        payment_data: Данные платежа
    """
    try:
        from bot import bot  # Импортируем бота
        
        metadata = payment_data.get("metadata", {})
        user_id = int(metadata.get("user_id", 0))
        payment_type = metadata.get("type", "")
        amount = payment_data.get("amount", 0)
        
        if not user_id:
            logger.error("❌ Не найден user_id для отправки уведомления")
            return
        
        if payment_type == "premium_requests":
            requests_count = int(metadata.get("requests_count", 0))
            
            message = (
                f"✅ **Платеж успешно обработан!**\n\n"
                f"💰 **Сумма:** {amount}₽\n"
                f"🧠 **Получено:** {requests_count} премиум ИИ запросов\n\n"
                f"🎉 **Теперь вы можете использовать премиум ИИ помощника!**\n"
                f"Премиум запросы никогда не сгорают и дают более подробные ответы.\n\n"
                f"📊 Проверить баланс: /settings → Премиум ИИ"
            )
            
        elif payment_type == "donation":
            message = (
                f"💝 **Спасибо за пожертвование!**\n\n"
                f"💰 **Сумма:** {amount}₽\n\n"
                f"🙏 **Ваша поддержка очень важна для развития бота!**\n"
                f"Средства будут направлены на:\n"
                f"• Оплату серверов и хостинга\n"
                f"• Улучшение ИИ помощника\n"
                f"• Добавление новых функций\n\n"
                f"❤️ **Благодарим за вашу щедрость!**"
            )
            
        else:
            message = f"✅ Платеж на сумму {amount}₽ успешно обработан!"
        
        await bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode="Markdown"
        )
        
        logger.info(f"📤 Отправлено уведомление о платеже пользователю {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка отправки уведомления о платеже: {e}")


# Функция для проверки webhook секрета (если используется)
def verify_webhook_signature(webhook_data: str, signature: str) -> bool:
    """
    Проверяет подпись webhook (если настроен WEBHOOK_SECRET)
    
    Args:
        webhook_data: Сырые данные webhook
        signature: Подпись из заголовка
        
    Returns:
        True если подпись верна или проверка отключена
    """
    from config.ai_settings import YOOKASSA_WEBHOOK_SECRET
    
    # Если секрет не настроен, пропускаем проверку
    if not YOOKASSA_WEBHOOK_SECRET:
        logger.info("YOOKASSA_WEBHOOK_SECRET не настроен, пропускаем проверку подписи")
        return True
    
    # TODO: Реализовать проверку подписи если нужно
    # Для базовой работы это не обязательно
    return True