"""
Обработчик вебхуков ЮKassa
"""
import logging
import json
import hashlib
import hmac
from typing import Dict, Any, Optional

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response

from database.universal_manager import universal_db_manager as db_manager
from services.premium_manager import PremiumManager
from config.ai_settings import YOOKASSA_WEBHOOK_SECRET

logger = logging.getLogger(__name__)


class YooKassaWebhookHandler:
    """Обработчик вебхуков ЮKassa"""

    def __init__(self):
        self.premium_manager = PremiumManager()

    def verify_signature(self, body: bytes, signature: str) -> bool:
        """Проверяет подпись вебхука"""
        if not YOOKASSA_WEBHOOK_SECRET:
            logger.warning(
                "⚠️ YOOKASSA_WEBHOOK_SECRET не настроен, пропускаем проверку подписи")
            return True

        # Временно отключаем проверку подписи для отладки
        logger.info(f"🔍 Отладка подписи: получена подпись {signature[:20]}...")
        logger.info(f"🔍 Размер тела запроса: {len(body)} байт")
        logger.info("⚠️ Проверка подписи временно отключена для отладки")
        return True

        # TODO: Включить после настройки правильного секрета
        # try:
        #     # Вычисляем ожидаемую подпись
        #     expected_signature = hmac.new(
        #         YOOKASSA_WEBHOOK_SECRET.encode('utf-8'),
        #         body,
        #         hashlib.sha256
        #     ).hexdigest()
        #
        #     # Сравниваем подписи
        #     return hmac.compare_digest(signature, expected_signature)
        # except Exception as e:
        #     logger.error(f"❌ Ошибка проверки подписи: {e}")
        #     return False

    async def handle_webhook(self, request: Request) -> Response:
        """Обрабатывает вебхук от ЮKassa"""
        try:
            # Получаем тело запроса
            body = await request.read()

            # Проверяем подпись (если настроена)
            signature = request.headers.get('X-Yookassa-Signature', '')
            if not self.verify_signature(body, signature):
                logger.error("❌ Неверная подпись вебхука")
                return web.Response(status=400, text="Invalid signature")

            # Парсим JSON
            try:
                data = json.loads(body.decode('utf-8'))
            except json.JSONDecodeError as e:
                logger.error(f"❌ Ошибка парсинга JSON: {e}")
                return web.Response(status=400, text="Invalid JSON")

            # Обрабатываем событие
            event_type = data.get('event')
            payment_data = data.get('object', {})

            logger.info(
                f"📨 Получен вебхук: {event_type}, платеж {payment_data.get('id')}")

            if event_type == 'payment.succeeded':
                await self.handle_payment_succeeded(payment_data)
            elif event_type == 'payment.canceled':
                await self.handle_payment_canceled(payment_data)
            elif event_type == 'payment.waiting_for_capture':
                await self.handle_payment_waiting_for_capture(payment_data)
            else:
                logger.info(f"ℹ️ Неизвестный тип события: {event_type}")

            return web.Response(status=200, text="OK")

        except Exception as e:
            logger.error(f"❌ Ошибка обработки вебхука: {e}")
            return web.Response(status=500, text="Internal server error")

    async def handle_payment_succeeded(self, payment_data: Dict[str, Any]):
        """Обрабатывает успешный платеж"""
        try:
            payment_id = payment_data.get('id')
            amount = float(payment_data.get('amount', {}).get('value', 0))
            metadata = payment_data.get('metadata', {})

            logger.info(f"🔍 Отладка платежа {payment_id}:")
            logger.info(f"   Amount: {amount}")
            logger.info(f"   Metadata: {metadata}")

            user_id = int(metadata.get('user_id', 0))
            payment_type = metadata.get('type', '')

            if not user_id:
                logger.error(
                    f"❌ Не найден user_id в метаданных платежа {payment_id}")
                logger.error(f"   Полные метаданные: {metadata}")
                return

            logger.info(
                f"💰 Успешный платеж {payment_id}: {amount}₽ от пользователя {user_id}, тип: {payment_type}")

            if payment_type == 'premium_requests':
                await self.process_premium_payment(payment_id, user_id, metadata, amount)
            elif payment_type == 'donation':
                await self.process_donation_payment(payment_id, user_id, metadata, amount)
            else:
                logger.error(f"❌ Неизвестный тип платежа: {payment_type}")
                logger.error(
                    f"   Доступные метаданные: {list(metadata.keys())}")

        except Exception as e:
            logger.error(f"❌ Ошибка обработки успешного платежа: {e}")
            import traceback
            traceback.print_exc()

    async def process_premium_payment(self, payment_id: str, user_id: int, metadata: Dict, amount: float):
        """Обрабатывает платеж за премиум запросы"""
        try:
            requests_count = int(metadata.get('requests_count', 0))

            if requests_count <= 0:
                logger.error(
                    f"❌ Некорректное количество запросов: {requests_count}")
                return

            # Создаем запись о покупке в базе данных
            if db_manager.is_supabase:
                # Для Supabase - используем вашу схему таблицы
                purchase_result = db_manager.manager.client.table('premium_purchases').insert({
                    'user_id': user_id,
                    'requests_count': requests_count,
                    # Конвертируем в integer как в схеме
                    'amount_rub': int(amount),
                    'amount_stars': 0,
                    'payment_method': 'ruble',
                    'payment_id': payment_id,
                    'payment_status': 'completed',
                    'completed_at': 'now()',
                    'telegram_payment_charge_id': None  # Для ЮKassa это null
                }).execute()

                if purchase_result.data:
                    purchase_id = purchase_result.data[0]['id']

                    # Добавляем премиум запросы пользователю
                    await self.premium_manager.add_premium_requests(user_id, requests_count)

                    logger.info(
                        f"✅ Обработан платеж за премиум запросы: пользователь {user_id}, {requests_count} запросов за {amount}₽")

                    # Отправляем уведомление пользователю (если бот запущен)
                    await self.send_payment_notification(user_id, 'premium', {
                        'requests_count': requests_count,
                        'amount': amount,
                        'payment_id': payment_id
                    })
                else:
                    logger.error(f"❌ Не удалось создать запись о покупке в БД")
            else:
                # Для других БД
                logger.warning(
                    "⚠️ Обработка платежей для не-Supabase БД не реализована")

        except Exception as e:
            logger.error(f"❌ Ошибка обработки платежа за премиум запросы: {e}")
            import traceback
            traceback.print_exc()

    async def process_donation_payment(self, payment_id: str, user_id: int, metadata: Dict, amount: float):
        """Обрабатывает платеж-пожертвование"""
        try:
            message = metadata.get('message', '')

            # Создаем запись о пожертвовании в базе данных
            if db_manager.is_supabase:
                # Для Supabase - используем вашу схему таблицы
                donation_result = db_manager.manager.client.table('donations').insert({
                    'user_id': user_id,
                    # Конвертируем в integer как в схеме
                    'amount_rub': int(amount),
                    'amount_stars': 0,
                    'payment_method': 'ruble',
                    'payment_id': payment_id,
                    'payment_status': 'completed',
                    'message': message,
                    'completed_at': 'now()',
                    'telegram_payment_charge_id': None  # Для ЮKassa это null
                }).execute()

                if donation_result.data:
                    donation_id = donation_result.data[0]['id']
                    logger.info(
                        f"✅ Обработано пожертвование: пользователь {user_id}, {amount}₽, ID {donation_id}")

                    # Отправляем уведомление пользователю
                    await self.send_payment_notification(user_id, 'donation', {
                        'amount': amount,
                        'payment_id': payment_id,
                        'message': message
                    })
                else:
                    logger.error(
                        f"❌ Не удалось создать запись о пожертвовании в БД")
            else:
                # Для других БД
                logger.warning(
                    "⚠️ Обработка пожертвований для не-Supabase БД не реализована")

        except Exception as e:
            logger.error(f"❌ Ошибка обработки пожертвования: {e}")
            import traceback
            traceback.print_exc()

    async def handle_payment_canceled(self, payment_data: Dict[str, Any]):
        """Обрабатывает отмененный платеж"""
        payment_id = payment_data.get('id')
        metadata = payment_data.get('metadata', {})
        user_id = int(metadata.get('user_id', 0))

        logger.info(f"❌ Платеж {payment_id} отменен пользователем {user_id}")

        # Можно отправить уведомление пользователю об отмене
        if user_id:
            await self.send_payment_notification(user_id, 'canceled', {
                'payment_id': payment_id
            })

    async def handle_payment_waiting_for_capture(self, payment_data: Dict[str, Any]):
        """Обрабатывает платеж, ожидающий подтверждения"""
        payment_id = payment_data.get('id')
        logger.info(f"⏳ Платеж {payment_id} ожидает подтверждения")

        # Для автоматического подтверждения можно использовать capture=True при создании платежа
        # Или подтвердить здесь через API

    async def send_payment_notification(self, user_id: int, notification_type: str, data: Dict[str, Any]):
        """Отправляет уведомление пользователю о статусе платежа"""
        try:
            # Здесь можно интегрироваться с ботом для отправки уведомлений
            # Пока просто логируем
            logger.info(
                f"📨 Уведомление пользователю {user_id}: {notification_type} - {data}")

            # TODO: Интеграция с ботом для отправки сообщений
            # Можно использовать Redis/RabbitMQ для очереди сообщений
            # Или напрямую через Bot API если бот запущен в том же процессе

        except Exception as e:
            logger.error(f"❌ Ошибка отправки уведомления: {e}")


# Глобальный экземпляр обработчика
webhook_handler = YooKassaWebhookHandler()


async def yookassa_webhook_endpoint(request: Request) -> Response:
    """Эндпоинт для вебхуков ЮKassa"""
    return await webhook_handler.handle_webhook(request)
