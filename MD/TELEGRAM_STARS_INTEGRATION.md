# 🌟 Интеграция с Telegram Stars

## 📋 Что уже готово

### ✅ Интерфейс пользователя
- Добавлена кнопка "⭐ Telegram Stars" в меню пожертвований
- Создано меню для выбора суммы Stars (10, 25, 50, 100, 250, 500)
- Добавлена опция "🌟 Купить за Telegram Stars" в меню премиума
- Настроены пакеты премиум запросов за Stars:
  - 10 запросов = 25 Stars (2.5 Stars за запрос)
  - 25 запросов = 50 Stars (2.0 Stars за запрос)
  - 50 запросов = 100 Stars (2.0 Stars за запрос)
  - 100 запросов = 180 Stars (1.8 Stars за запрос) 💎

### ✅ База данных
- Обновлены таблицы `premium_purchases` и `donations` для поддержки Stars
- Добавлена новая таблица `star_transactions` для отслеживания операций
- Добавлены индексы для оптимизации

### ✅ Бэкенд
- Расширен `PremiumManager` методами для работы с Stars:
  - `create_star_donation()` - создание пожертвования через Stars
  - `create_star_premium_purchase()` - покупка премиума за Stars
  - `get_user_star_transactions()` - история транзакций
  - `verify_star_transaction()` - проверка транзакции

### ✅ Совместимость
- Сохранена полная совместимость с рублевыми платежами
- Пользователи могут выбирать между Stars и рублями

## 🔧 Что нужно доделать для продакшена

### 1. Настройка Bot API для Stars
В aiogram 3.19+ поддержка Telegram Stars реализуется через:

```python
from aiogram.types import LabeledPrice

# Пример создания инвойса для Stars
await bot.send_invoice(
    chat_id=user_id,
    title="Пожертвование проекту",
    description="Поддержите развитие библейского бота",
    payload="donation_stars_50",
    provider_token="",  # Пустая строка для Telegram Stars
    currency="XTR",     # Валюта Telegram Stars
    prices=[LabeledPrice(label="Пожертвование", amount=50)],  # amount в Stars
    # Другие параметры...
)
```

### 2. Обработка платежей Stars
Добавить обработчики для `successful_payment` и `pre_checkout_query`:

```python
from aiogram.types import SuccessfulPayment, PreCheckoutQuery

@router.pre_checkout_query()
async def process_pre_checkout_query(query: PreCheckoutQuery):
    """Подтверждение платежа перед списанием Stars"""
    if query.currency == "XTR":  # Telegram Stars
        await query.answer(ok=True)
    else:
        await query.answer(ok=False, error_message="Unsupported currency")

@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    """Обработка успешного платежа"""
    payment = message.successful_payment
    
    if payment.currency == "XTR":  # Telegram Stars
        # Извлекаем данные из payload
        payload_parts = payment.invoice_payload.split("_")
        
        if payload_parts[0] == "donation":
            # Обработка пожертвования
            stars_amount = int(payload_parts[2])
            await premium_manager.create_star_donation(
                user_id=message.from_user.id,
                amount_stars=stars_amount,
                telegram_payment_charge_id=payment.telegram_payment_charge_id
            )
        
        elif payload_parts[0] == "premium":
            # Обработка покупки премиума
            requests_count = int(payload_parts[2])
            stars_amount = int(payload_parts[3])
            await premium_manager.create_star_premium_purchase(
                user_id=message.from_user.id,
                requests_count=requests_count,
                amount_stars=stars_amount,
                telegram_payment_charge_id=payment.telegram_payment_charge_id
            )
```

### 3. Обновление обработчиков кнопок
Заменить TODO в `handlers/settings.py`:

```python
@router.callback_query(F.data.startswith("donate_stars_"))
async def process_stars_donation(callback: CallbackQuery, state: FSMContext):
    """Обработка пожертвований через Telegram Stars"""
    data_parts = callback.data.split("_")
    
    if len(data_parts) >= 3:
        stars_amount = int(data_parts[2])
        
        await callback.message.bot.send_invoice(
            chat_id=callback.from_user.id,
            title="Пожертвование проекту",
            description=f"Поддержка развития библейского бота - {stars_amount} Stars",
            payload=f"donation_stars_{stars_amount}",
            provider_token="",  # Пустая строка для Stars
            currency="XTR",
            prices=[LabeledPrice(label="Пожертвование", amount=stars_amount)],
            need_name=False,
            need_phone_number=False,
            need_email=False,
            need_shipping_address=False,
            send_phone_number_to_provider=False,
            send_email_to_provider=False,
            is_flexible=False
        )
        
        await callback.answer("💫 Создан инвойс для оплаты через Telegram Stars!")
```

### 4. Конфигурация
Добавить в `.env` настройки (если понадобятся):

```env
# Telegram Stars (обычно токен не нужен, но на всякий случай)
TELEGRAM_STARS_ENABLED=true
TELEGRAM_STARS_MIN_AMOUNT=1
TELEGRAM_STARS_MAX_AMOUNT=2500
```

## 🚀 Запуск в продакшене

1. **Обновите aiogram**: `pip install aiogram>=3.19.0`
2. **Примените миграцию БД**: Выполните SQL из `database/premium_requests_schema.sql`
3. **Добавьте обработчики платежей**: Реализуйте пункты 2-3 выше
4. **Протестируйте**: Начните с небольших сумм Stars
5. **Мониторинг**: Отслеживайте таблицу `star_transactions`

## 💡 Преимущества Telegram Stars

- ✅ **Простота**: Никаких банковских реквизитов
- ✅ **Скорость**: Мгновенные транзакции
- ✅ **Безопасность**: Встроено в Telegram
- ✅ **Анонимность**: Не нужны персональные данные
- ✅ **Низкие комиссии**: Telegram берет меньше, чем банки
- ✅ **Глобальность**: Работает во всех странах где есть Telegram

## 📊 Аналитика

После запуска можно добавить админ-команды для анализа:

```python
@router.message(Command("stars_stats"))
async def stars_statistics(message: Message):
    """Статистика по Telegram Stars (только для админа)"""
    if message.from_user.id != ADMIN_USER_ID:
        return
    
    # Получение статистики из базы данных
    stats = await premium_manager.get_star_transactions_stats()
    
    stats_text = (
        "🌟 **Статистика Telegram Stars**\n\n"
        f"📊 **Всего транзакций**: {stats['total_transactions']}\n"
        f"💰 **Общая сумма**: {stats['total_stars']} Stars\n"
        f"🎁 **Пожертвования**: {stats['donations_count']} ({stats['donations_stars']} Stars)\n"
        f"⭐ **Премиум покупки**: {stats['premium_count']} ({stats['premium_stars']} Stars)\n"
        f"📈 **За последние 7 дней**: {stats['week_transactions']} транзакций\n"
    )
    
    await message.answer(stats_text, parse_mode="Markdown")
```

---

## ✅ ИНТЕГРАЦИЯ ЗАВЕРШЕНА!

### 🚀 Система полностью готова к работе

**Что готово:**
- ✅ Обработчики Telegram Stars в `handlers/payments.py`
- ✅ Обновленные клавиатуры с опциями Stars
- ✅ База данных поддерживает Stars транзакции  
- ✅ Премиум система работает с Stars и рублями
- ✅ Пожертвования принимают Stars и рубли
- ✅ Все зависимости обновлены (aiogram 3.21.0)

**Как использовать:**
1. Пользователь выбирает "💰 Пожертвования" → "⭐ Telegram Stars"
2. Выбирает сумму Stars (10, 25, 50, 100, 250, 500)
3. Telegram показывает native Stars payment UI
4. После оплаты бот автоматически сохраняет в БД и благодарит

**Премиум через Stars:**
1. Пользователь выбирает "⭐ Премиум ИИ" → "🌟 Купить за Telegram Stars"  
2. Выбирает пакет (10/25/50/100 запросов)
3. Оплачивает через Telegram Stars
4. Запросы автоматически добавляются к балансу

**Совместимость:**
- Рублевые платежи через ЮKassa работают параллельно
- Пользователи могут выбирать удобный способ оплаты
- Все данные хранятся в одной БД с разными полями для типа платежа

### 🎉 Готово к деплою!

Система готова к использованию в production с поддержкой Telegram Stars и сохранением всех существующих функций.

**Тестирование:**
- Обязательно протестируйте в production (Stars недоступны в тесте)
- Начните с минимальных сумм
- Убедитесь, что платежи включены в BotFather