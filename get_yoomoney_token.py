#!/usr/bin/env python3
"""
Утилита для получения токена YooMoney
"""
import os
import logging
import webbrowser
from urllib.parse import urlparse, parse_qs

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_yoomoney_token():
    """Помогает получить токен YooMoney"""
    
    logger.info("🔑 Получение токена YooMoney")
    logger.info("=" * 50)
    
    # Шаг 1: Создание приложения
    logger.info("1️⃣ Создание приложения YooMoney")
    logger.info("")
    logger.info("📝 Перейдите на: https://yoomoney.ru/myservices/new")
    logger.info("📋 Заполните форму:")
    logger.info("   • Название: Gospel Bot Donations")
    logger.info("   • Описание: Прием пожертвований для библейского бота")
    logger.info("   • Сайт: https://github.com/your-username/gospel-bot")
    logger.info("   • Redirect URI: https://your-domain.com/callback")
    logger.info("   • Права доступа: ✅ operation-history")
    logger.info("")
    
    # Получаем client_id
    client_id = input("🔑 Введите client_id вашего приложения: ").strip()
    
    if not client_id:
        logger.error("❌ Client ID обязателен!")
        return
    
    # Шаг 2: Генерация ссылки авторизации
    logger.info("")
    logger.info("2️⃣ Авторизация")
    
    redirect_uri = "https://your-domain.com/callback"
    scope = "operation-history"
    
    auth_url = (
        f"https://yoomoney.ru/oauth/authorize?"
        f"client_id={client_id}&"
        f"response_type=code&"
        f"redirect_uri={redirect_uri}&"
        f"scope={scope}"
    )
    
    logger.info("🔗 Ссылка для авторизации:")
    logger.info(auth_url)
    logger.info("")
    
    # Открываем браузер
    try:
        webbrowser.open(auth_url)
        logger.info("🌐 Браузер открыт автоматически")
    except:
        logger.info("🌐 Скопируйте ссылку в браузер вручную")
    
    logger.info("")
    logger.info("👆 Перейдите по ссылке и разрешите доступ")
    logger.info("📋 После разрешения вы будете перенаправлены на redirect_uri")
    logger.info("🔍 В адресной строке найдите параметр 'code'")
    logger.info("📝 Пример: https://your-domain.com/callback?code=ABC123...")
    logger.info("")
    
    # Получаем код авторизации
    auth_code = input("🔑 Введите код авторизации (параметр 'code'): ").strip()
    
    if not auth_code:
        logger.error("❌ Код авторизации обязателен!")
        return
    
    # Шаг 3: Обмен кода на токен
    logger.info("")
    logger.info("3️⃣ Получение токена")
    
    try:
        import requests
        
        token_url = "https://yoomoney.ru/oauth/token"
        
        data = {
            'code': auth_code,
            'client_id': client_id,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri
        }
        
        logger.info("📡 Отправляем запрос на получение токена...")
        
        response = requests.post(token_url, data=data)
        
        if response.status_code == 200:
            token_data = response.json()
            
            if 'access_token' in token_data:
                access_token = token_data['access_token']
                
                logger.info("🎉 Токен получен успешно!")
                logger.info("")
                logger.info("🔑 Ваш access token:")
                logger.info(f"   {access_token}")
                logger.info("")
                logger.info("📝 Добавьте в .env файл:")
                logger.info(f"   YOOMONEY_ACCESS_TOKEN={access_token}")
                logger.info("")
                
                # Предлагаем протестировать токен
                test_token = input("🧪 Протестировать токен сейчас? (y/n): ").strip().lower()
                
                if test_token == 'y':
                    # Временно устанавливаем токен для теста
                    os.environ['YOOMONEY_ACCESS_TOKEN'] = access_token
                    
                    from test_yoomoney_token import test_yoomoney_token
                    test_yoomoney_token()
                
            else:
                logger.error("❌ Токен не найден в ответе")
                logger.error(f"📋 Ответ сервера: {token_data}")
                
        else:
            logger.error(f"❌ Ошибка получения токена: {response.status_code}")
            logger.error(f"📋 Ответ сервера: {response.text}")
            
    except ImportError:
        logger.error("❌ Библиотека requests не установлена!")
        logger.info("💡 Установите: pip install requests")
        logger.info("")
        logger.info("🔧 Или получите токен вручную:")
        logger.info("📡 POST запрос на: https://yoomoney.ru/oauth/token")
        logger.info("📋 Параметры:")
        logger.info(f"   code={auth_code}")
        logger.info(f"   client_id={client_id}")
        logger.info(f"   grant_type=authorization_code")
        logger.info(f"   redirect_uri={redirect_uri}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при получении токена: {e}")

def show_token_scopes():
    """Показывает доступные права доступа"""
    
    logger.info("🔐 Доступные права доступа (scopes):")
    logger.info("")
    logger.info("📊 operation-history - Просмотр истории операций")
    logger.info("   • Получение списка операций")
    logger.info("   • Детали операций")
    logger.info("   • Статусы платежей")
    logger.info("")
    logger.info("💰 operation-details - Детали операций")
    logger.info("   • Подробная информация об операциях")
    logger.info("")
    logger.info("💳 incoming-transfers - Входящие переводы")
    logger.info("   • Информация о входящих платежах")
    logger.info("")
    logger.info("📋 account-info - Информация об аккаунте")
    logger.info("   • Баланс")
    logger.info("   • Статус аккаунта")
    logger.info("   • Привязанные карты")
    logger.info("")
    logger.info("💡 Для нашего бота достаточно: operation-history")

if __name__ == "__main__":
    logger.info("🔑 Утилита получения токена YooMoney")
    logger.info("=" * 50)
    
    choice = input("Выберите действие:\n1 - Получить токен\n2 - Показать права доступа\n3 - Тест существующего токена\nВыбор (1-3): ").strip()
    
    if choice == "1":
        get_yoomoney_token()
    elif choice == "2":
        show_token_scopes()
    elif choice == "3":
        from test_yoomoney_token import test_yoomoney_token
        test_yoomoney_token()
    else:
        logger.info("❌ Неверный выбор")
    
    logger.info("")
    logger.info("🎉 Готово!")