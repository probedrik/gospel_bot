## Gospel Backend (FastAPI) — краткий запуск

### Установка

1) Python 3.10+
2) Установить зависимости (используется общий `requirements.txt` проекта бота, FastAPI/uvicorn уже есть если нет — добавить):

```bash
pip install fastapi uvicorn
```

### Переменные окружения

Нужны те же переменные, что у бота, минимум:

```env
SUPABASE_URL=...
SUPABASE_KEY=...
OPENROUTER_API_KEY=...
```

### Запуск дев-сервера

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Проверка

- Здоровье: `GET http://localhost:8000/health`
- Лимиты ИИ: `GET http://localhost:8000/api/v1/ai/limits?user_id=123`
- Глава: `GET http://localhost:8000/api/v1/bible/chapter?book_id=40&chapter=6&translation=rst`
- Предложить стихи: `POST http://localhost:8000/api/v1/ai/suggest-verses`

```json
{
  "user_id": 123,
  "problem_text": "испытываю тревогу и сомнения"
}
```

- Чат — старт: `POST /api/v1/ai/chat/start` — `{ "user_id": 123 }`
- Чат — сообщение: `POST /api/v1/ai/chat/message`

```json
{
  "user_id": 123,
  "conversation_id": "...",
  "message": "что почитать, когда тревожно?"
}
```

### Примечания

- Backend использует существующие менеджеры БД/квот из бота, поэтому переменные и таблицы Supabase обязательны.
- Для production добавьте CORS‑лист, API‑ключи, JWT и docker‑compose.


