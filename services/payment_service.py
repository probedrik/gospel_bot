"""
Сервис для работы с платежами через ЮKassa
"""
import logging
import uuid
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class PaymentService:
    """Сервис для работы с платежами ЮKassa"""

    def __init__(self):
        try:
            from yookassa import Configuration, Payment
            from config.ai_settings import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY
            
            self.Payment = Payment  # Сохраняем класс Payment
            
            # Настройка ЮKassa
            if YOOKASSA_SHOP_ID and YOOKASSA_SECRET_KEY:
                Configuration.account_id = YOOKASSA_SHOP_ID
                Configuration.secret_key = YOOKASSA_SECRET_KEY
                self.enabled = True
                logger.info("✅ ЮKassa настроена и готова к работе")
            else:
                self.enabled = False
                logger.warning("⚠️ ЮKassa не настроена - отсутствуют SHOP_ID или SECRET_KEY")
        except ImportError:
            self.enabled = False
            logger.error("❌ Библиотека yookassa не установлена. Установите: pip install yookassa")
        except Exception as e:
            self.enabled = False
            logger.error(f"❌ Ошибка инициализации ЮKassa: {e}")

    def is_enabled(self) -> bool:
        """Проверяет, настроена ли ЮKassa"""
        return self.enabled

    async def create_premium_payment(
        self, 
        user_id: int, 
        requests_count: int, 
        amount: float,
        return_url: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Создает платеж для покупки премиум запросов
        
        Args:
            user_id: ID пользователя
            requests_count: Количество запросов
            amount: Сумма в рублях
            return_url: URL для возврата после оплаты
            
        Returns:
            Словарь с данными платежа или None при ошибке
        """
        if not self.enabled:
            logger.error("ЮKassa не настроена")
            return None

        try:
            # Генерируем уникальный ключ идемпотентности
            idempotency_key = str(uuid.uuid4())
            
            # Создаем платеж
            payment = self.Payment.create({
                "amount": {
                    "value": f"{amount:.2f}",
                    "currency": "RUB"
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": return_url or "https://t.me/bedrik12345_bot"
                },
                "capture": True,
                "description": f"Покупка {requests_count} премиум ИИ запросов",
                "receipt": {
                    "customer": {
                        "email": f"user{user_id}@gospel-bot.local"
                    },
                    "items": [
                        {
                            "description": f"Премиум ИИ запросы ({requests_count} шт.)",
                            "quantity": "1.00",
                            "amount": {
                                "value": f"{amount:.2f}",
                                "currency": "RUB"
                            },
                            "vat_code": 1,  # НДС не облагается
                            "payment_mode": "full_payment",
                            "payment_subject": "service"
                        }
                    ]
                },
                "metadata": {
                    "user_id": str(user_id),
                    "type": "premium_requests",
                    "requests_count": str(requests_count)
                }
            }, idempotency_key)

            logger.info(f"✅ Создан платеж {payment.id} для пользователя {user_id}")
            
            return {
                "payment_id": payment.id,
                "confirmation_url": payment.confirmation.confirmation_url,
                "status": payment.status,
                "amount": amount,
                "requests_count": requests_count
            }

        except Exception as e:
            logger.error(f"❌ Ошибка создания платежа: {e}")
            return None

    async def create_donation_payment(
        self, 
        user_id: int, 
        amount: float,
        message: str = "",
        return_url: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Создает платеж для пожертвования
        
        Args:
            user_id: ID пользователя
            amount: Сумма в рублях
            message: Сообщение от пользователя
            return_url: URL для возврата после оплаты
            
        Returns:
            Словарь с данными платежа или None при ошибке
        """
        if not self.enabled:
            logger.error("ЮKassa не настроена")
            return None

        try:
            # Генерируем уникальный ключ идемпотентности
            idempotency_key = str(uuid.uuid4())
            
            # Создаем платеж
            payment = self.Payment.create({
                "amount": {
                    "value": f"{amount:.2f}",
                    "currency": "RUB"
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": return_url or "https://t.me/bedrik12345_bot"
                },
                "capture": True,
                "description": f"Пожертвование на развитие бота",
                "receipt": {
                    "customer": {
                        "email": f"user{user_id}@gospel-bot.local"
                    },
                    "items": [
                        {
                            "description": "Пожертвование на развитие бота",
                            "quantity": "1.00",
                            "amount": {
                                "value": f"{amount:.2f}",
                                "currency": "RUB"
                            },
                            "vat_code": 1,  # НДС не облагается
                            "payment_mode": "full_payment",
                            "payment_subject": "service"
                        }
                    ]
                },
                "metadata": {
                    "user_id": str(user_id),
                    "type": "donation",
                    "message": message[:100]  # Ограничиваем длину
                }
            }, idempotency_key)

            logger.info(f"✅ Создан платеж-пожертвование {payment.id} для пользователя {user_id}")
            
            return {
                "payment_id": payment.id,
                "confirmation_url": payment.confirmation.confirmation_url,
                "status": payment.status,
                "amount": amount
            }

        except Exception as e:
            logger.error(f"❌ Ошибка создания платежа-пожертвования: {e}")
            return None

    async def check_payment_status(self, payment_id: str) -> Optional[Dict[str, Any]]:
        """
        Проверяет статус платежа
        
        Args:
            payment_id: ID платежа
            
        Returns:
            Словарь с информацией о платеже или None при ошибке
        """
        if not self.enabled:
            return None

        try:
            payment = self.Payment.find_one(payment_id)
            
            return {
                "payment_id": payment.id,
                "status": payment.status,
                "paid": payment.paid,
                "amount": float(payment.amount.value),
                "currency": payment.amount.currency,
                "metadata": payment.metadata
            }

        except Exception as e:
            logger.error(f"❌ Ошибка проверки статуса платежа {payment_id}: {e}")
            return None

    async def process_successful_payment(self, payment_data: Dict[str, Any]) -> bool:
        """
        Обрабатывает успешный платеж
        
        Args:
            payment_data: Данные платежа
            
        Returns:
            True если обработка прошла успешно
        """
        try:
            metadata = payment_data.get("metadata", {})
            user_id = int(metadata.get("user_id", 0))
            payment_type = metadata.get("type", "")
            
            if not user_id:
                logger.error("❌ Не найден user_id в метаданных платежа")
                return False

            from services.premium_manager import PremiumManager
            premium_manager = PremiumManager()

            if payment_type == "premium_requests":
                # Обработка покупки премиум запросов
                requests_count = int(metadata.get("requests_count", 0))
                amount = payment_data.get("amount", 0)
                
                # Добавляем премиум запросы
                success = await premium_manager.add_premium_requests(user_id, requests_count)
                
                if success:
                    # Создаем запись о покупке
                    await premium_manager.create_premium_purchase(
                        user_id=user_id,
                        requests_count=requests_count,
                        amount_rub=amount,
                        payment_id=payment_data["payment_id"]
                    )
                    
                    logger.info(f"✅ Обработана покупка {requests_count} запросов для пользователя {user_id}")
                    return True

            elif payment_type == "donation":
                # Обработка пожертвования
                amount = payment_data.get("amount", 0)
                message = metadata.get("message", "")
                
                # Создаем запись о пожертвовании
                await premium_manager.create_donation(
                    user_id=user_id,
                    amount_rub=amount,
                    payment_id=payment_data["payment_id"],
                    message=message
                )
                
                logger.info(f"✅ Обработано пожертвование {amount}₽ от пользователя {user_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"❌ Ошибка обработки успешного платежа: {e}")
            return False


# Глобальный экземпляр сервиса
payment_service = PaymentService()