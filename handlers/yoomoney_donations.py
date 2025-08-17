"""
Обработчики пожертвований через YooMoney
"""
import logging
from typing import Optional

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from services.yoomoney_service import yoomoney_service
from database.universal_manager import universal_db_manager as db_manager

logger = logging.getLogger(__name__)
router = Router()

# Состояния для ввода произвольной суммы пожертвования
class DonationStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_message = State()

# === ПОЖЕРТВОВАНИЯ ЧЕРЕЗ YOOMONEY ===

@router.callback_query(F.data == "donate_yoomoney_menu")
async def show_yoomoney_donation_menu(callback: CallbackQuery, state: FSMContext):
    """Показывает меню пожертвований YooMoney"""
    try:
        if not yoomoney_service.is_enabled():
            await callback.answer("❌ YooMoney не настроен", show_alert=True)
            return
        
        # Создаем клавиатуру с предустановленными суммами
        keyboard = create_yoomoney_donation_keyboard()
        
        yoomoney_text = (
            "💰 **Пожертвование через YooMoney**\n\n"
            "🎯 **Преимущества YooMoney:**\n"
            "• Оплата с любых карт (Visa, MasterCard, МИР)\n"
            "• Быстрая и безопасная оплата\n"
            "• Не нужна регистрация\n"
            "• Мгновенное поступление средств\n\n"
            "💝 **Выберите сумму для пожертвования:**"
        )
        
        await callback.message.edit_text(
            yoomoney_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        await callback.answer("💰 Меню YooMoney пожертвований")
        
    except Exception as e:
        logger.error(f"Ошибка при показе меню YooMoney: {e}")
        await callback.answer("❌ Ошибка при загрузке меню", show_alert=True)


@router.callback_query(F.data.startswith("donate_yoomoney_"))
async def process_yoomoney_donation(callback: CallbackQuery, state: FSMContext):
    """Обработка пожертвований через YooMoney"""
    try:
        # Извлекаем сумму из callback_data
        amount_str = callback.data.replace("donate_yoomoney_", "")
        
        if amount_str == "custom":
            # Запрашиваем произвольную сумму
            await state.set_state(DonationStates.waiting_for_amount)
            
            await callback.message.edit_text(
                "💰 **Произвольная сумма пожертвования**\n\n"
                "💵 Введите сумму в рублях (от 1 до 50000):\n\n"
                "Например: 150",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(
                        text="⬅️ Назад к суммам",
                        callback_data="donate_yoomoney_menu"
                    )
                ]])
            )
            
            await callback.answer("💰 Введите сумму пожертвования")
            return
        
        # Проверяем, что это число
        if not amount_str.isdigit():
            await callback.answer("❌ Некорректная сумма", show_alert=True)
            return
            
        amount = float(amount_str)
        
        # Создаем ссылку для пожертвования
        donation_data = yoomoney_service.create_donation_link(
            amount=amount,
            user_id=callback.from_user.id,
            message="",
            return_url="https://t.me/bedrik12345_bot"
        )
        
        if donation_data:
            # Сохраняем информацию о платеже в базу данных как pending
            await save_pending_donation(
                user_id=callback.from_user.id,
                amount=amount,
                payment_id=donation_data['payment_id'],
                message=""
            )
            
            # Создаем клавиатуру с кнопкой оплаты
            keyboard = InlineKeyboardBuilder()
            keyboard.add(InlineKeyboardButton(
                text="💰 Перейти к оплате",
                url=donation_data['payment_url']
            ))
            keyboard.add(InlineKeyboardButton(
                text="⬅️ Назад к суммам",
                callback_data="donate_yoomoney_menu"
            ))
            keyboard.adjust(1)
            
            donation_text = (
                f"💰 **Пожертвование {amount}₽**\n\n"
                f"🎯 **Назначение:** Поддержка развития Gospel Bot\n"
                f"💳 **Способ оплаты:** YooMoney (любые карты)\n"
                f"🆔 **ID платежа:** {donation_data['payment_id']}\n\n"
                f"👆 **Нажмите кнопку ниже для перехода к оплате**\n\n"
                f"ℹ️ После успешной оплаты вы получите уведомление в боте."
            )
            
            await callback.message.edit_text(
                donation_text,
                reply_markup=keyboard.as_markup(),
                parse_mode="Markdown"
            )
            
            await callback.answer("💰 Ссылка для пожертвования создана!")
        else:
            await callback.answer("❌ Ошибка при создании ссылки", show_alert=True)
        
    except Exception as e:
        logger.error(f"Ошибка при создании пожертвования YooMoney: {e}")
        await callback.answer("❌ Ошибка при создании пожертвования", show_alert=True)


# === ОБРАБОТКА ВВОДА ПРОИЗВОЛЬНОЙ СУММЫ ===

@router.message(DonationStates.waiting_for_amount)
async def process_custom_donation_amount(message: Message, state: FSMContext):
    """Обработка ввода произвольной суммы пожертвования"""
    try:
        # Проверяем, что введено число
        try:
            amount = float(message.text.replace(',', '.'))
        except ValueError:
            await message.answer(
                "❌ Некорректная сумма. Введите число, например: 150",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(
                        text="⬅️ Назад к суммам",
                        callback_data="donate_yoomoney_menu"
                    )
                ]])
            )
            return
        
        # Проверяем лимиты
        if amount < 1:
            await message.answer(
                "❌ Минимальная сумма: 1₽",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(
                        text="⬅️ Назад к суммам",
                        callback_data="donate_yoomoney_menu"
                    )
                ]])
            )
            return
        
        if amount > 50000:
            await message.answer(
                "❌ Максимальная сумма: 50000₽",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(
                        text="⬅️ Назад к суммам",
                        callback_data="donate_yoomoney_menu"
                    )
                ]])
            )
            return
        
        # Сохраняем сумму и переходим к вводу сообщения
        await state.update_data(amount=amount)
        await state.set_state(DonationStates.waiting_for_message)
        
        await message.answer(
            f"💰 **Сумма пожертвования: {amount}₽**\n\n"
            f"💬 Хотите добавить сообщение к пожертвованию?\n\n"
            f"Введите сообщение или нажмите 'Пропустить':",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text="➡️ Пропустить",
                    callback_data=f"donate_yoomoney_skip_message_{amount}"
                )
            ], [
                InlineKeyboardButton(
                    text="⬅️ Назад к суммам",
                    callback_data="donate_yoomoney_menu"
                )
            ]])
        )
        
    except Exception as e:
        logger.error(f"Ошибка при обработке суммы пожертвования: {e}")
        await message.answer("❌ Ошибка при обработке суммы")


@router.message(DonationStates.waiting_for_message)
async def process_donation_message(message: Message, state: FSMContext):
    """Обработка сообщения к пожертвованию"""
    try:
        data = await state.get_data()
        amount = data.get('amount', 0)
        user_message = message.text[:200]  # Ограничиваем длину
        
        await create_donation_with_message(message, amount, user_message, state)
        
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения пожертвования: {e}")
        await message.answer("❌ Ошибка при обработке сообщения")


@router.callback_query(F.data.startswith("donate_yoomoney_skip_message_"))
async def skip_donation_message(callback: CallbackQuery, state: FSMContext):
    """Пропуск сообщения к пожертвованию"""
    try:
        amount_str = callback.data.replace("donate_yoomoney_skip_message_", "")
        amount = float(amount_str)
        
        await create_donation_with_message(callback.message, amount, "", state)
        await callback.answer("➡️ Сообщение пропущено")
        
    except Exception as e:
        logger.error(f"Ошибка при пропуске сообщения: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


async def create_donation_with_message(message_obj, amount: float, user_message: str, state: FSMContext):
    """Создает пожертвование с сообщением"""
    try:
        user_id = message_obj.from_user.id if hasattr(message_obj, 'from_user') else message_obj.chat.id
        
        # Создаем ссылку для пожертвования
        donation_data = yoomoney_service.create_donation_link(
            amount=amount,
            user_id=user_id,
            message=user_message,
            return_url="https://t.me/bedrik12345_bot"
        )
        
        if donation_data:
            # Сохраняем информацию о платеже в базу данных как pending
            await save_pending_donation(
                user_id=user_id,
                amount=amount,
                payment_id=donation_data['payment_id'],
                message=user_message
            )
            
            # Создаем клавиатуру с кнопкой оплаты
            keyboard = InlineKeyboardBuilder()
            keyboard.add(InlineKeyboardButton(
                text="💰 Перейти к оплате",
                url=donation_data['payment_url']
            ))
            keyboard.add(InlineKeyboardButton(
                text="⬅️ Назад к суммам",
                callback_data="donate_yoomoney_menu"
            ))
            keyboard.adjust(1)
            
            donation_text = (
                f"💰 **Пожертвование {amount}₽**\n\n"
                f"🎯 **Назначение:** Поддержка развития Gospel Bot\n"
                f"💳 **Способ оплаты:** YooMoney (любые карты)\n"
                f"🆔 **ID платежа:** {donation_data['payment_id']}\n"
            )
            
            if user_message:
                donation_text += f"💬 **Ваше сообщение:** {user_message}\n"
            
            donation_text += (
                f"\n👆 **Нажмите кнопку ниже для перехода к оплате**\n\n"
                f"ℹ️ После успешной оплаты вы получите уведомление в боте."
            )
            
            await message_obj.answer(
                donation_text,
                reply_markup=keyboard.as_markup(),
                parse_mode="Markdown"
            )
        else:
            await message_obj.answer("❌ Ошибка при создании ссылки для пожертвования")
        
        # Очищаем состояние
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка при создании пожертвования с сообщением: {e}")
        await message_obj.answer("❌ Ошибка при создании пожертвования")


async def save_pending_donation(user_id: int, amount: float, payment_id: str, message: str):
    """Сохраняет информацию о pending пожертвовании"""
    try:
        if db_manager.is_supabase:
            # Сохраняем в таблицу donations как pending
            result = db_manager.manager.client.table('donations').insert({
                'user_id': user_id,
                'amount_rub': int(amount),
                'amount_stars': 0,
                'payment_method': 'yoomoney',
                'payment_id': payment_id,
                'payment_status': 'pending',
                'message': message,
                'telegram_payment_charge_id': None
            }).execute()
            
            if result.data:
                logger.info(f"✅ Сохранено pending пожертвование: {payment_id}, {amount}₽")
            else:
                logger.error(f"❌ Не удалось сохранить pending пожертвование")
        
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения pending пожертвования: {e}")


def create_yoomoney_donation_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для пожертвований YooMoney"""
    amounts = yoomoney_service.get_donation_amounts()
    
    buttons = []
    
    # Создаем кнопки по 2 в ряд
    for i in range(0, len(amounts), 2):
        row = []
        for j in range(2):
            if i + j < len(amounts):
                amount = amounts[i + j]
                row.append(InlineKeyboardButton(
                    text=f"💰 {amount}₽",
                    callback_data=f"donate_yoomoney_{amount}"
                ))
        buttons.append(row)
    
    # Добавляем кнопку произвольной суммы
    buttons.append([
        InlineKeyboardButton(
            text="💵 Произвольная сумма",
            callback_data="donate_yoomoney_custom"
        )
    ])
    
    # Добавляем кнопку назад
    buttons.append([
        InlineKeyboardButton(
            text="⬅️ Назад к пожертвованиям",
            callback_data="settings_donation"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# === ПРОВЕРКА СТАТУСА ПЛАТЕЖЕЙ ===

async def check_pending_donations():
    """Проверяет статус pending пожертвований"""
    try:
        if not yoomoney_service.access_token:
            logger.info("ℹ️ YooMoney access token не настроен, проверка статуса недоступна")
            return
        
        if db_manager.is_supabase:
            # Получаем все pending пожертвования YooMoney
            result = db_manager.manager.client.table('donations').select('*').eq('payment_method', 'yoomoney').eq('payment_status', 'pending').execute()
            
            if result.data:
                logger.info(f"🔍 Найдено {len(result.data)} pending пожертвований YooMoney")
                
                for donation in result.data:
                    payment_id = donation['payment_id']
                    
                    # Проверяем статус через YooMoney API
                    payment_status = await yoomoney_service.check_payment_status(payment_id)
                    
                    if payment_status and payment_status['status'] == 'success':
                        # Обновляем статус в базе данных
                        update_result = db_manager.manager.client.table('donations').update({
                            'payment_status': 'completed',
                            'completed_at': 'now()'
                        }).eq('id', donation['id']).execute()
                        
                        if update_result.data:
                            logger.info(f"✅ Пожертвование {payment_id} подтверждено: {donation['amount_rub']}₽")
                            
                            # Отправляем уведомление пользователю
                            # TODO: Интеграция с ботом для отправки уведомлений
                        else:
                            logger.error(f"❌ Не удалось обновить статус пожертвования {payment_id}")
            else:
                logger.info("ℹ️ Pending пожертвований YooMoney не найдено")
        
    except Exception as e:
        logger.error(f"❌ Ошибка проверки pending пожертвований: {e}")