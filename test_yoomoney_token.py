#!/usr/bin/env python3
"""
Тест токена YooMoney по примеру из GitHub
"""
import os
import logging
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_yoomoney_token():
    """Тестирует токен YooMoney"""
    
    logger.info("🔑 Тестируем токен YooMoney...")
    
    try:
        # Проверяем наличие токена
        token = os.getenv('YOOMONEY_ACCESS_TOKEN')
        
        if not token or token == 'your_yoomoney_access_token':
            logger.warning("⚠️ YOOMONEY_ACCESS_TOKEN не настроен в .env файле")
            logger.info("💡 Добавьте в .env: YOOMONEY_ACCESS_TOKEN=your_real_token")
            return False
        
        # Импортируем библиотеку YooMoney
        try:
            from yoomoney import Client
            logger.info("✅ Библиотека yoomoney импортирована")
        except ImportError:
            logger.error("❌ Библиотека yoomoney не установлена!")
            logger.info("💡 Установите: pip install yoomoney")
            return False
        
        # Создаем клиента
        logger.info("🔧 Создаем клиента YooMoney...")
        client = Client(token)
        
        # Получаем информацию об аккаунте
        logger.info("📊 Получаем информацию об аккаунте...")
        user = client.account_info()
        
        # Выводим информацию как в примере GitHub
        logger.info("📋 Информация об аккаунте:")
        logger.info(f"   Account number: {user.account}")
        logger.info(f"   Account balance: {user.balance}")
        logger.info(f"   Account currency code in ISO 4217 format: {user.currency}")
        logger.info(f"   Account status: {user.account_status}")
        logger.info(f"   Account type: {user.account_type}")
        
        # Детальная информация о балансе
        logger.info("💰 Extended balance information:")
        for pair in vars(user.balance_details):
            balance_value = vars(user.balance_details).get(pair)
            logger.info(f"   \\t->{pair}: {balance_value}")
        
        # Информация о привязанных картах
        logger.info("💳 Information about linked bank cards:")
        cards = user.cards_linked
        
        if len(cards) != 0:
            for card in cards:
                logger.info(f"   {card.pan_fragment} - {card.type}")
        else:
            logger.info("   No card is linked to the account")
        
        # Проверяем возможность создания платежей
        logger.info("🔍 Проверяем возможности токена...")
        
        # Проверяем права токена
        if hasattr(user, 'account_status') and user.account_status:
            logger.info("✅ Токен действителен и имеет доступ к аккаунту")
            
            # Проверяем баланс
            if user.balance > 0:
                logger.info(f"✅ На счету есть средства: {user.balance} {user.currency}")
            else:
                logger.info(f"⚠️ Баланс счета: {user.balance} {user.currency}")
            
            # Проверяем статус аккаунта
            if user.account_status == 'identified':
                logger.info("✅ Аккаунт верифицирован (identified)")
            elif user.account_status == 'anonymous':
                logger.info("⚠️ Аккаунт анонимный (anonymous) - ограниченные возможности")
            else:
                logger.info(f"ℹ️ Статус аккаунта: {user.account_status}")
            
            return True
        else:
            logger.error("❌ Токен недействителен или нет доступа к аккаунту")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании токена: {e}")
        
        # Дополнительная диагностика
        if "401" in str(e) or "Unauthorized" in str(e):
            logger.error("🔐 Ошибка авторизации - проверьте токен")
        elif "403" in str(e) or "Forbidden" in str(e):
            logger.error("🚫 Доступ запрещен - проверьте права токена")
        elif "network" in str(e).lower() or "connection" in str(e).lower():
            logger.error("🌐 Проблема с сетевым соединением")
        else:
            logger.error(f"🔧 Техническая ошибка: {type(e).__name__}")
        
        return False

def get_token_info():
    """Показывает информацию о том, как получить токен"""
    
    logger.info("📖 Как получить токен YooMoney:")
    logger.info("")
    logger.info("1️⃣ Зарегистрируйтесь на https://yoomoney.ru")
    logger.info("2️⃣ Создайте приложение на https://yoomoney.ru/myservices/new")
    logger.info("3️⃣ Заполните форму:")
    logger.info("   - Название: Gospel Bot Donations")
    logger.info("   - Описание: Прием пожертвований")
    logger.info("   - Права: operation-history")
    logger.info("4️⃣ Получите client_id")
    logger.info("5️⃣ Перейдите по ссылке авторизации:")
    logger.info("   https://yoomoney.ru/oauth/authorize?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=https://your-domain.com&scope=operation-history")
    logger.info("6️⃣ Обменяйте код на токен через API")
    logger.info("")
    logger.info("💡 Или используйте готовые инструменты для получения токена")

if __name__ == "__main__":
    logger.info("🧪 Тест токена YooMoney")
    logger.info("=" * 50)
    
    success = test_yoomoney_token()
    
    if not success:
        logger.info("")
        logger.info("=" * 50)
        get_token_info()
    
    logger.info("")
    logger.info("🎉 Тестирование завершено!")