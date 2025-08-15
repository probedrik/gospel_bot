"""
Обработчики платежей через Telegram Stars
"""
import logging
from typing import Optional

from aiogram import Router, F
from aiogram.types import (
    CallbackQuery, Message, PreCheckoutQuery, SuccessfulPayment,
    LabeledPrice
)
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from database.universal_manager import universal_db_manager as db_manager
from services.premium_manager import PremiumManager
from config.ai_settings import STAR_PREMIUM_PACKAGES

logger = logging.getLogger(__name__)
router = Router()

# Инициализируем менеджер премиум запросов
premium_manager = None

async def get_premium_manager():
    """Получает инициализированный менеджер премиум запросов"""
    global premium_manager
    if premium_manager is None:
        premium_manager = PremiumManager()
    return premium_manager

# === ПОЖЕРТВОВАНИЯ ЧЕРЕЗ TELEGRAM STARS ===

@router.callback_query(F.data.startswith("donate_stars_") & ~F.data.in_(["donate_stars_menu"]))
async def process_stars_donation(callback: CallbackQuery, state: FSMContext):
    """Обработка пожертвований через Telegram Stars"""
    try:
        logger.info(f"🌟 Обработка пожертвования: callback_data = {callback.data}")
        
        # Извлекаем сумму из callback_data
        amount_str = callback.data.replace("donate_stars_", "")
        
        # Проверяем, что это число
        if not amount_str.isdigit():
            logger.error(f"❌ Некорректная сумма в callback_data: '{amount_str}' из '{callback.data}'")
            await callback.answer("❌ Некорректная сумма", show_alert=True)
            return
            
        amount_stars = int(amount_str)
        
        logger.info(f"🌟 Пожертвование Stars: пользователь {callback.from_user.id}, сумма {amount_stars}")
        
        # Создаем инвойс для Stars
        prices = [LabeledPrice(label=f"Пожертвование {amount_stars} Stars", amount=amount_stars)]
        
        # Отправляем инвойс
        await callback.message.answer_invoice(
            title=f"Пожертвование {amount_stars} ⭐",
            description=f"Поддержка проекта библейского бота через {amount_stars} Telegram Stars",
            payload=f"donation_stars_{amount_stars}_{callback.from_user.id}",
            provider_token="",  # Для Stars не нужен
            currency="XTR",  # Telegram Stars
            prices=prices,
            start_parameter="donation_stars",
            need_name=False,
            need_phone_number=False,
            need_email=False,
            need_shipping_address=False,
            send_phone_number_to_provider=False,
            send_email_to_provider=False,
            is_flexible=False
        )
        
        await callback.answer("💫 Инвойс для пожертвования создан!")
        
    except Exception as e:
        logger.error(f"Ошибка при создании инвойса для пожертвования: {e}")
        await callback.answer("❌ Ошибка при создании платежа", show_alert=True)


# === ПОКУПКА ПРЕМИУМ ЗАПРОСОВ ЧЕРЕЗ TELEGRAM STARS ===

@router.callback_query(F.data.startswith("buy_premium_stars_") & ~F.data.in_(["buy_premium_stars"]))
async def process_premium_stars_purchase(callback: CallbackQuery, state: FSMContext):
    """Обработка покупки премиум запросов через Telegram Stars"""
    try:
        logger.info(f"🌟 Обработка покупки премиум запросов: callback_data = {callback.data}")
        
        # Извлекаем количество запросов из callback_data
        requests_str = callback.data.replace("buy_premium_stars_", "")
        
        # Проверяем, что это валидный пакет
        if requests_str not in STAR_PREMIUM_PACKAGES:
            logger.error(f"❌ Неизвестный пакет: '{requests_str}' из '{callback.data}'")
            await callback.answer("❌ Неизвестный пакет", show_alert=True)
            return
        
        package = STAR_PREMIUM_PACKAGES[requests_str]
        requests_count = package["requests"]
        cost_stars = package["cost_stars"]
        description = package["description"]
        
        logger.info(f"🌟 Покупка премиум запросов: пользователь {callback.from_user.id}, "
                   f"{requests_count} запросов за {cost_stars} Stars")
        
        # Создаем инвойс для Stars
        prices = [LabeledPrice(
            label=f"{requests_count} премиум запросов", 
            amount=cost_stars
        )]
        
        # Отправляем инвойс
        await callback.message.answer_invoice(
            title=f"{requests_count} премиум запросов ⭐",
            description=f"{description}: {requests_count} запросов к премиум ИИ за {cost_stars} Telegram Stars",
            payload=f"premium_stars_{requests_count}_{cost_stars}_{callback.from_user.id}",
            provider_token="",  # Для Stars не нужен
            currency="XTR",  # Telegram Stars
            prices=prices,
            start_parameter="premium_stars",
            need_name=False,
            need_phone_number=False,
            need_email=False,
            need_shipping_address=False,
            send_phone_number_to_provider=False,
            send_email_to_provider=False,
            is_flexible=False
        )
        
        await callback.answer("💫 Инвойс для покупки премиум запросов создан!")
        
    except Exception as e:
        logger.error(f"Ошибка при создании инвойса для премиум запросов: {e}")
        await callback.answer("❌ Ошибка при создании платежа", show_alert=True)


# === ОБРАБОТКА PRE-CHECKOUT QUERY ===

@router.pre_checkout_query()
async def process_pre_checkout_query(query: PreCheckoutQuery):
    """Подтверждение платежа перед списанием Stars"""
    try:
        logger.info(f"💳 Pre-checkout query: {query.id}, payload: {query.invoice_payload}")
        
        # Проверяем валюту
        if query.currency != "XTR":
            await query.answer(ok=False, error_message="Поддерживаются только Telegram Stars")
            return
        
        # Парсим payload
        payload_parts = query.invoice_payload.split("_")
        if len(payload_parts) < 3:
            await query.answer(ok=False, error_message="Некорректные данные платежа")
            return
        
        payment_type = payload_parts[0]  # donation или premium
        
        if payment_type == "donation":
            # Для пожертвований всегда разрешаем
            await query.answer(ok=True)
            
        elif payment_type == "premium":
            # Для премиум запросов проверяем корректность данных
            if len(payload_parts) >= 4:
                requests_count = int(payload_parts[2])
                cost_stars = int(payload_parts[3])
                
                # Проверяем соответствие пакету
                package_found = False
                for package_key, package_data in STAR_PREMIUM_PACKAGES.items():
                    if (package_data["requests"] == requests_count and 
                        package_data["cost_stars"] == cost_stars):
                        package_found = True
                        break
                
                if package_found:
                    await query.answer(ok=True)
                else:
                    await query.answer(ok=False, error_message="Некорректные данные пакета")
            else:
                await query.answer(ok=False, error_message="Некорректные данные платежа")
        else:
            await query.answer(ok=False, error_message="Неизвестный тип платежа")
            
    except Exception as e:
        logger.error(f"Ошибка в pre_checkout_query: {e}")
        await query.answer(ok=False, error_message="Внутренняя ошибка сервера")


# === ОБРАБОТКА УСПЕШНОГО ПЛАТЕЖА ===

@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    """Обработка успешного платежа через Telegram Stars"""
    try:
        payment: SuccessfulPayment = message.successful_payment
        user_id = message.from_user.id
        
        logger.info(f"💰 Успешный платеж: пользователь {user_id}, "
                   f"сумма {payment.total_amount} {payment.currency}, "
                   f"payload: {payment.invoice_payload}")
        
        # Проверяем валюту
        if payment.currency != "XTR":
            logger.error(f"Неподдерживаемая валюта: {payment.currency}")
            await message.answer("❌ Ошибка: неподдерживаемая валюта")
            return
        
        # Парсим payload
        payload_parts = payment.invoice_payload.split("_")
        if len(payload_parts) < 3:
            logger.error(f"Некорректный payload: {payment.invoice_payload}")
            await message.answer("❌ Ошибка: некорректные данные платежа")
            return
        
        payment_type = payload_parts[0]  # donation или premium
        
        if payment_type == "donation":
            # Обрабатываем пожертвование
            await process_donation_payment(message, payment, payload_parts)
            
        elif payment_type == "premium":
            # Обрабатываем покупку премиум запросов
            await process_premium_payment(message, payment, payload_parts)
            
        else:
            logger.error(f"Неизвестный тип платежа: {payment_type}")
            await message.answer("❌ Ошибка: неизвестный тип платежа")
            
    except Exception as e:
        logger.error(f"Ошибка при обработке успешного платежа: {e}")
        await message.answer("❌ Произошла ошибка при обработке платежа. Обратитесь к администратору.")


async def process_donation_payment(message: Message, payment: SuccessfulPayment, payload_parts: list):
    """Обработка пожертвования"""
    try:
        user_id = message.from_user.id
        amount_stars = payment.total_amount
        telegram_payment_charge_id = payment.telegram_payment_charge_id
        
        # Сохраняем пожертвование в базу данных
        pm = await get_premium_manager()
        donation_id = await pm.create_star_donation(
            user_id=user_id,
            amount_stars=amount_stars,
            telegram_payment_charge_id=telegram_payment_charge_id,
            message=f"Пожертвование через Telegram Stars от @{message.from_user.username or 'unknown'}"
        )
        
        if donation_id:
            # Отправляем благодарность
            thank_you_text = (
                f"🙏 <b>Спасибо за пожертвование!</b>\n\n"
                f"⭐ Сумма: {amount_stars} Telegram Stars\n"
                f"📅 Дата: {message.date.strftime('%d.%m.%Y %H:%M')}\n"
                f"🆔 ID транзакции: {telegram_payment_charge_id}\n\n"
                f"Ваша поддержка помогает развивать проект и делать его лучше для всех пользователей!\n\n"
                f"🤖 Продолжайте изучать Священное Писание с нашим ботом!"
            )
            
            await message.answer(thank_you_text, parse_mode="HTML")
            
            # Логируем успешное пожертвование
            logger.info(f"✅ Пожертвование обработано: пользователь {user_id}, "
                       f"{amount_stars} Stars, donation_id {donation_id}")
        else:
            await message.answer("❌ Ошибка при сохранении пожертвования. Обратитесь к администратору.")
            
    except Exception as e:
        logger.error(f"Ошибка при обработке пожертвования: {e}")
        await message.answer("❌ Ошибка при обработке пожертвования. Обратитесь к администратору.")


async def process_premium_payment(message: Message, payment: SuccessfulPayment, payload_parts: list):
    """Обработка покупки премиум запросов"""
    try:
        user_id = message.from_user.id
        amount_stars = payment.total_amount
        telegram_payment_charge_id = payment.telegram_payment_charge_id
        
        # Извлекаем данные из payload
        if len(payload_parts) >= 4:
            requests_count = int(payload_parts[2])
            cost_stars = int(payload_parts[3])
        else:
            logger.error(f"Некорректный payload для премиум покупки: {payment.invoice_payload}")
            await message.answer("❌ Ошибка: некорректные данные покупки")
            return
        
        # Проверяем соответствие суммы
        if amount_stars != cost_stars:
            logger.error(f"Несоответствие суммы: ожидалось {cost_stars}, получено {amount_stars}")
            await message.answer("❌ Ошибка: несоответствие суммы платежа")
            return
        
        # Сохраняем покупку в базу данных
        pm = await get_premium_manager()
        purchase_id = await pm.create_star_premium_purchase(
            user_id=user_id,
            requests_count=requests_count,
            amount_stars=amount_stars,
            telegram_payment_charge_id=telegram_payment_charge_id
        )
        
        if purchase_id:
            # Получаем текущий баланс премиум запросов
            current_balance = await pm.get_user_premium_requests(user_id)
            
            # Отправляем подтверждение
            success_text = (
                f"✅ <b>Премиум запросы успешно приобретены!</b>\n\n"
                f"🌟 Куплено: {requests_count} премиум запросов\n"
                f"⭐ Стоимость: {amount_stars} Telegram Stars\n"
                f"💎 Текущий баланс: {current_balance} запросов\n"
                f"📅 Дата: {message.date.strftime('%d.%m.%Y %H:%M')}\n"
                f"🆔 ID транзакции: {telegram_payment_charge_id}\n\n"
                f"🤖 Теперь вы можете использовать премиум ИИ для подробного разбора библейских текстов!\n\n"
                f"💡 Используйте кнопку '🤖 ИИ разбор' при чтении глав или стихов."
            )
            
            await message.answer(success_text, parse_mode="HTML")
            
            # Логируем успешную покупку
            logger.info(f"✅ Премиум запросы куплены: пользователь {user_id}, "
                       f"{requests_count} запросов за {amount_stars} Stars, purchase_id {purchase_id}")
        else:
            await message.answer("❌ Ошибка при обработке покупки. Обратитесь к администратору.")
            
    except Exception as e:
        logger.error(f"Ошибка при обработке покупки премиум запросов: {e}")
        await message.answer("❌ Ошибка при обработке покупки. Обратитесь к администратору.")


# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===

async def get_user_premium_balance(user_id: int) -> int:
    """Получает баланс премиум запросов пользователя"""
    try:
        pm = await get_premium_manager()
        return await pm.get_user_premium_requests(user_id)
    except Exception as e:
        logger.error(f"Ошибка при получении баланса премиум запросов: {e}")
        return 0


async def get_user_donation_stats(user_id: int) -> dict:
    """Получает статистику пожертвований пользователя"""
    try:
        # Здесь можно добавить запрос к базе данных для получения статистики
        # Пока возвращаем заглушку
        return {
            "total_donations": 0,
            "total_stars": 0,
            "last_donation_date": None
        }
    except Exception as e:
        logger.error(f"Ошибка при получении статистики пожертвований: {e}")
        return {
            "total_donations": 0,
            "total_stars": 0,
            "last_donation_date": None
        }