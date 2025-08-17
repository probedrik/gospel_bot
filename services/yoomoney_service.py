"""
Сервис для работы с YooMoney (пожертвования)
"""
import logging
import uuid
from typing import Optional, Dict, Any
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


class YooMoneyService:
    """Сервис для работы с YooMoney пожертвованиями"""

    def __init__(self):
        try:
            import os
            
            # Получаем настройки из переменных окружения
            self.wallet_number = os.getenv('YOOMONEY_WALLET_NUMBER')
            self.access_token = os.getenv('YOOMONEY_ACCESS_TOKEN')
            
            if self.wallet_number:
                self.enabled = True
                logger.info("✅ YooMoney настроен и готов к работе")
                logger.info(f"   Кошелек: {self.wallet_number}")
            else:
                self.enabled = False
                logger.warning("⚠️ YooMoney не настроен - отсутствует YOOMONEY_WALLET_NUMBER")
                
        except Exception as e:
            self.enabled = False
            logger.error(f"❌ Ошибка инициализации YooMoney: {e}")

    def is_enabled(self) -> bool:
        """Проверяет, настроен ли YooMoney"""
        return self.enabled

    def create_donation_link(
        self, 
        amount: float, 
        user_id: int,
        message: str = "",
        return_url: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Создает ссылку для пожертвования через YooMoney
        
        Args:
            amount: Сумма в рублях
            user_id: ID пользователя
            message: Сообщение от пользователя
            return_url: URL для возврата после оплаты
            
        Returns:
            Словарь с данными ссылки или None при ошибке
        """
        if not self.enabled:
            logger.error("YooMoney не настроен")
            return None

        try:
            # Генерируем уникальный ID платежа
            payment_id = f"donation_{user_id}_{uuid.uuid4().hex[:8]}"
            
            # Параметры для YooMoney
            params = {
                'receiver': self.wallet_number,
                'quickpay-form': 'donate',  # Форма пожертвования
                'targets': f'Пожертвование на развитие Gospel Bot',  # Назначение платежа
                'paymentType': 'AC',  # Способ оплаты (AC - с любой карты)
                'sum': f'{amount:.2f}',  # Сумма
                'label': payment_id,  # Метка платежа для идентификации
                'successURL': return_url or 'https://t.me/bedrik12345_bot',  # URL успеха
            }
            
            # Если есть сообщение от пользователя, добавляем его к назначению
            if message:
                params['targets'] = f'Пожертвование на развитие Gospel Bot: {message[:50]}'
            
            # Формируем URL
            base_url = 'https://yoomoney.ru/quickpay/confirm.xml'
            payment_url = f"{base_url}?{urlencode(params)}"
            
            logger.info(f"✅ Создана ссылка для пожертвования {payment_id}: {amount}₽")
            
            return {
                "payment_id": payment_id,
                "payment_url": payment_url,
                "amount": amount,
                "user_id": user_id,
                "message": message,
                "status": "pending"
            }

        except Exception as e:
            logger.error(f"❌ Ошибка создания ссылки для пожертвования: {e}")
            return None

    async def check_payment_status(self, payment_id: str) -> Optional[Dict[str, Any]]:
        """
        Проверяет статус платежа через YooMoney API
        
        Args:
            payment_id: ID платежа (label)
            
        Returns:
            Информация о платеже или None
        """
        if not self.access_token:
            logger.warning("⚠️ YOOMONEY_ACCESS_TOKEN не настроен, проверка статуса недоступна")
            return None

        try:
            from yoomoney import Client
            
            client = Client(self.access_token)
            
            # Получаем историю операций
            history = client.operation_history(label=payment_id)
            
            if history.operations:
                operation = history.operations[0]
                
                return {
                    "payment_id": payment_id,
                    "operation_id": operation.operation_id,
                    "status": operation.status,
                    "amount": float(operation.amount),
                    "datetime": operation.datetime,
                    "title": operation.title,
                    "sender": operation.sender if hasattr(operation, 'sender') else None
                }
            else:
                logger.info(f"ℹ️ Платеж {payment_id} не найден в истории")
                return None
                
        except Exception as e:
            logger.error(f"❌ Ошибка проверки статуса платежа: {e}")
            return None

    def get_donation_amounts(self) -> list:
        """Возвращает предустановленные суммы для пожертвований"""
        return [50, 100, 200, 500, 1000, 2000]

    def create_custom_donation_link(
        self, 
        user_id: int,
        message: str = "",
        return_url: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Создает ссылку для пожертвования с произвольной суммой
        
        Args:
            user_id: ID пользователя
            message: Сообщение от пользователя
            return_url: URL для возврата после оплаты
            
        Returns:
            Словарь с данными ссылки или None при ошибке
        """
        if not self.enabled:
            logger.error("YooMoney не настроен")
            return None

        try:
            # Генерируем уникальный ID платежа
            payment_id = f"donation_custom_{user_id}_{uuid.uuid4().hex[:8]}"
            
            # Параметры для YooMoney (без суммы - пользователь введет сам)
            params = {
                'receiver': self.wallet_number,
                'quickpay-form': 'donate',
                'targets': f'Пожертвование на развитие Gospel Bot',
                'paymentType': 'AC',
                'label': payment_id,
                'successURL': return_url or 'https://t.me/bedrik12345_bot',
                'need-fio': 'false',  # Не запрашиваем ФИО
                'need-email': 'false',  # Не запрашиваем email
                'need-phone': 'false',  # Не запрашиваем телефон
                'need-address': 'false',  # Не запрашиваем адрес
            }
            
            # Если есть сообщение от пользователя, добавляем его к назначению
            if message:
                params['targets'] = f'Пожертвование на развитие Gospel Bot: {message[:50]}'
            
            # Формируем URL
            base_url = 'https://yoomoney.ru/quickpay/confirm.xml'
            payment_url = f"{base_url}?{urlencode(params)}"
            
            logger.info(f"✅ Создана ссылка для произвольного пожертвования {payment_id}")
            
            return {
                "payment_id": payment_id,
                "payment_url": payment_url,
                "amount": None,  # Произвольная сумма
                "user_id": user_id,
                "message": message,
                "status": "pending"
            }

        except Exception as e:
            logger.error(f"❌ Ошибка создания ссылки для произвольного пожертвования: {e}")
            return None

    async def check_payment_status(self, payment_id: str) -> Optional[Dict[str, Any]]:
        """
        Проверяет статус платежа через YooMoney API
        
        Args:
            payment_id: ID платежа для проверки
            
        Returns:
            Словарь со статусом платежа или None если не найден
        """
        if not self.access_token:
            logger.warning("Access token не настроен для проверки статуса")
            return None

        try:
            # Используем библиотеку yoomoney для проверки
            from yoomoney import Client
            
            client = Client(self.access_token)
            
            # Получаем историю операций
            history = client.operation_history(records=50)
            
            # Ищем операцию с нашим payment_id в label
            for operation in history.operations:
                if hasattr(operation, 'label') and operation.label == payment_id:
                    return {
                        'payment_id': payment_id,
                        'status': 'success' if operation.status == 'success' else 'pending',
                        'amount': float(operation.amount) if operation.amount else 0,
                        'datetime': operation.datetime.isoformat() if operation.datetime else None,
                        'operation_id': operation.operation_id
                    }
            
            # Если не найдено, возвращаем None
            return None
            
        except ImportError:
            logger.error("❌ Библиотека yoomoney не установлена")
            return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки статуса платежа: {e}")
            return None


# Глобальный экземпляр сервиса
yoomoney_service = YooMoneyService()