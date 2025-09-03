# Python Backend (FastAPI) for YooKassa

Запуск локально (Windows PowerShell):

```powershell
# 1) Создать и активировать venv (опционально, но рекомендуется)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2) Установить зависимости
pip install -r pyserver/requirements.txt

# 3) Задать переменные окружения (тестовые значения)
$env:YOOKASSA_SHOP_ID="1131092"
$env:YOOKASSA_SECRET_KEY="test_tsvBacBKexSzSEM88wamXbVRyR3A0n59keUSyADRnjM"
$env:CLIENT_ORIGIN="http://localhost:5173"

# 4) Запуск сервера
uvicorn pyserver.main:app --host 0.0.0.0 --port 8001 --reload
```

Эндпоинты:
- GET `/health` — проверка статуса
- POST `/api/yookassa/create-payment` — создаёт платёж и возвращает `confirmation_token`

Пример запроса:
```bash
curl -X POST "http://localhost:8001/api/yookassa/create-payment" \
  -H "Content-Type: application/json" \
  -d '{"amount": 100.0, "description": "Пожертвование"}'
```

Интеграция во фронтенд уже сделана: кнопка "Пожертвовать" вызывает этот эндпоинт и открывает виджет YooKassa.

