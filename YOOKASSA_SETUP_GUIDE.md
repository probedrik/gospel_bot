# 💳 Руководство по настройке ЮKassa

## 🎯 Обзор

Это руководство поможет настроить интеграцию с ЮKassa для приема платежей в Gospel Bot.

## 📋 Что нужно

### 1. Аккаунт ЮKassa
- Зарегистрируйтесь на [yookassa.ru](https://yookassa.ru)
- Пройдите верификацию
- Получите доступ к личному кабинету

### 2. Настройки магазина
- **Shop ID** - идентификатор магазина
- **Secret Key** - секретный ключ для API
- **Webhook Secret** - секрет для проверки подписи вебхуков (опционально)

### 3. Домен для вебхуков
- Публичный домен с SSL сертификатом
- Или ngrok для тестирования

## ⚙️ Настройка

### 1. Переменные окружения

Добавьте в `.env` файл:

```env
# ЮKassa настройки
YOOKASSA_SHOP_ID=your_shop_id_here
YOOKASSA_SECRET_KEY=your_secret_key_here
YOOKASSA_WEBHOOK_SECRET=your_webhook_secret_here

# Webhook URL (для справки)
WEBHOOK_URL=https://yourdomain.com/webhook/yookassa
```

### 2. Получение данных из ЮKassa

1. **Войдите в личный кабинет ЮKassa**
2. **Перейдите в раздел "Настройки" → "Данные для разработчиков"**
3. **Скопируйте:**
   - Shop ID (идентификатор магазина)
   - Секретный ключ

### 3. Настройка вебхуков

1. **В личном кабинете ЮKassa:**
   - Перейдите в "Настройки" → "Уведомления"
   - Добавьте URL: `https://yourdomain.com/webhook/yookassa`
   - Выберите события:
     - ✅ `payment.succeeded` - успешный платеж
     - ✅ `payment.canceled` - отмененный платеж
     - ✅ `payment.waiting_for_capture` - ожидает подтверждения

2. **Настройте секрет вебхука (рекомендуется):**
   - Сгенерируйте случайную строку (32+ символов)
   - Укажите в настройках ЮKassa
   - Добавьте в `YOOKASSA_WEBHOOK_SECRET`

## 🚀 Развертывание

### Вариант 1: Docker Compose (рекомендуется)

```bash
# Запуск с webhook сервером
docker-compose -f docker-compose.yookassa.yml up -d

# Проверка статуса
docker-compose -f docker-compose.yookassa.yml ps

# Логи
docker-compose -f docker-compose.yookassa.yml logs -f
```

### Вариант 2: Отдельные процессы

```bash
# Терминал 1: Основной бот
python bot.py

# Терминал 2: Webhook сервер
python webhook_server.py
```

### Вариант 3: Ngrok для тестирования

```bash
# Установите ngrok
# Запустите webhook сервер
python webhook_server.py

# В другом терминале
ngrok http 8080

# Используйте ngrok URL в настройках ЮKassa
# Например: https://abc123.ngrok.io/webhook/yookassa
```

## 🧪 Тестирование

### 1. Проверка webhook сервера

```bash
# Health check
curl http://localhost:8080/health

# Информация о сервисе
curl http://localhost:8080/
```

### 2. Тестовый платеж

1. **В боте:**
   - Настройки → Премиум ИИ → Купить запросы
   - Выберите пакет и нажмите "Оплатить"

2. **Проверьте логи:**
   - Создание платежа в ЮKassa
   - Получение вебхука при оплате
   - Обновление баланса пользователя

### 3. Тестовые карты ЮKassa

```
Успешная оплата: 5555 5555 5555 4444
Отклоненная:     5555 5555 5555 4477
3D-Secure:       5555 5555 5555 4453

CVC: любой 3-значный код
Срок: любая будущая дата
```

## 📊 Мониторинг

### Логи webhook сервера

```bash
# Docker
docker logs gospel-webhook-server -f

# Прямой запуск
tail -f logs/webhook.log
```

### Проверка платежей в ЮKassa

1. **Личный кабинет ЮKassa**
2. **Раздел "Платежи"**
3. **Фильтр по статусам и датам**

### Проверка в базе данных

```sql
-- Последние платежи
SELECT * FROM premium_purchases 
ORDER BY created_at DESC 
LIMIT 10;

-- Статистика по пользователю
SELECT 
    user_id,
    SUM(requests_count) as total_requests,
    SUM(amount_rub) as total_spent
FROM premium_purchases 
WHERE payment_status = 'completed'
GROUP BY user_id;
```

## 🔧 Устранение неполадок

### Проблема: Вебхуки не приходят

**Решения:**
1. Проверьте URL в настройках ЮKassa
2. Убедитесь, что сервер доступен извне
3. Проверьте SSL сертификат
4. Посмотрите логи Nginx/прокси

### Проблема: Неверная подпись

**Решения:**
1. Проверьте `YOOKASSA_WEBHOOK_SECRET`
2. Убедитесь, что секрет совпадает в ЮKassa и .env
3. Временно отключите проверку подписи для отладки

### Проблема: Платежи не обрабатываются

**Решения:**
1. Проверьте логи webhook сервера
2. Убедитесь, что база данных доступна
3. Проверьте метаданные в платеже
4. Посмотрите статус платежа в ЮKassa

## 📈 Производительность

### Рекомендации

1. **Используйте Redis для кэширования**
2. **Настройте мониторинг (Prometheus + Grafana)**
3. **Логируйте все операции**
4. **Используйте очереди для обработки платежей**

### Масштабирование

```yaml
# docker-compose.scale.yml
services:
  webhook-server:
    deploy:
      replicas: 3
    
  nginx:
    depends_on:
      - webhook-server
```

## 🔒 Безопасность

### Обязательно

1. **Используйте HTTPS**
2. **Проверяйте подписи вебхуков**
3. **Ограничивайте доступ к webhook URL**
4. **Логируйте все операции**
5. **Регулярно ротируйте секретные ключи**

### Дополнительно

1. **Rate limiting**
2. **IP whitelist для ЮKassa**
3. **Мониторинг подозрительной активности**

## 📞 Поддержка

### ЮKassa
- Документация: [yookassa.ru/docs](https://yookassa.ru/docs)
- Поддержка: support@yookassa.ru
- Telegram: @yookassa_support

### Gospel Bot
- GitHub Issues
- Telegram: @your_support_bot

---

**Готово!** 🎉

После настройки пользователи смогут покупать премиум запросы через ЮKassa с автоматическим зачислением на баланс.