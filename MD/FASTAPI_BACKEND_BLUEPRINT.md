## Цель

Вынести функциональность Telegram‑бота в единый backend‑сервис на FastAPI, чтобы:
- подключать несколько клиентов (Telegram‑бот(ы), веб‑сайт, будущие мобильные клиенты);
- централизовать бизнес‑логику (ИИ, чтение, закладки, планы, платежи);
- иметь единые лимиты/квоты и учёт в Supabase;
- упростить масштабирование, мониторинг и релизы.

## Текущее состояние (что уже есть в боте)

- Библия/чтение: главы, навигация, форматирование, номера стихов (`utils/api_client.py`, `handlers/text_messages.py`).
- Закладки: добавление/удаление/списки, диапазоны глав/стихов (`handlers/bookmarks*.py`, `database/*`).
- Планы чтения: список, дни, прогресс, навигация (`handlers/reading_plans.py`, `services/universal_reading_plans.py`).
- Темы: подбор стихов по темам, поиск (`utils/topics.py`, Supabase таблица тем).
- ИИ‑функции: объяснение, ассистент, чат с памятью; квоты/лимиты и премиум‑учёт (`handlers/ai_assistant.py`, `handlers/ai_conversation.py`, `services/ai_quota_manager.py`, `services/premium_manager.py`).
- Платежи/донаты: YooKassa, YooMoney, Telegram Stars (готовые обработчики и вебхуки).
- БД: универсальный менеджер (SQLite/Postgres/Supabase), Supabase как основной [[универсальный менеджер]].

## Архитектура FastAPI backend

### Общая схема

- FastAPI приложение `app/`:
  - `app/main.py` — создание приложения, CORS, Lifespan (инициализация БД/квот), маршрутизация.
  - `app/api/` — модули API по доменам (bible, bookmarks, plans, topics, ai, payments, calendar, users).
  - `app/services/` — бизнес‑логика (обёртки над текущими `services/*`, `utils/*`).
  - `app/db/` — адаптер к `database/universal_manager.py` (переиспользуем) и модели Pydantic.
  - `app/integrations/` — YooKassa, YooMoney, Telegram Stars, Supabase SDK.
  - `app/core/` — конфиги, безопасность (JWT), квоты, фоновые задачи (reset квот).

### Данные и БД

- Переиспользуем `database/universal_manager.py` и `database/supabase_manager.py` — backend вызывает те же методы.
- Supabase как primary хранилище; service role key — только на backend.
- Таблицы:
  - уже существующие (users, bookmarks, reading_plans, …);
  - `ai_conversations`, `ai_messages` — для диалоговой памяти;
  - `ai_limits`, `premium_requests`, `premium_purchases`, `donations` — для квот/платежей.

### Идентификация/аутентификация

- Варианты клиентов:
  - Telegram‑бот: обращается к backend с внутренним токеном (API_KEY) + user_id из Telegram.
  - Веб/мобайл: JWT (OAuth/собственный логин), map к user_id.
- Внутренние эндпоинты (вебхуки платежей) — защищены сигнатурами/секретами.

### Квоты/лимиты

- Единый `AIQuotaManager` как сервис backend (фоновая задача сброса, учёт в Supabase).
- Любой клиентский вызов ИИ проходит через `check_and_increment_usage()`.

## API дизайн (черновик)

Версии: все маршруты под `/api/v1/…`.

### Auth

- `POST /api/v1/auth/token` — (опц.) Получение JWT для веб‑клиента.

### Библия

- `GET /api/v1/bible/chapter` — параметры: `book_id`, `chapter`, `translation`. Возвращает отформатированный текст (HTML/Markdown) + метаданные.
- `GET /api/v1/bible/reference` — параметры: `reference` («Книга N:M‑K»), `translation`.
- `GET /api/v1/bible/random-verse?translation=rst`.

### Закладки

- `GET /api/v1/bookmarks` — список.
- `POST /api/v1/bookmarks` — добавление (диапазоны глав/стихов поддерживаются).
- `DELETE /api/v1/bookmarks/{id}` — удаление.

### Планы чтения

- `GET /api/v1/plans` — список планов.
- `GET /api/v1/plans/{plan_id}` — инфо + дни.
- `POST /api/v1/plans/{plan_id}/set` — назначить план пользователю.
- `POST /api/v1/plans/{plan_id}/day/{n}/complete` — прогресс (день/часть).

### Темы

- `GET /api/v1/topics?query=…&limit=…` — поиск.
- `GET /api/v1/topics/{id}` — тема с перечнем стихов.

### ИИ: объяснение, ассистент, чат

- `POST /api/v1/ai/explain` — тело: `prompt`, опции; ответ: текст, лимиты, тип модели.
- `POST /api/v1/ai/suggest-verses` — тело: `problem_text`; ответ: `text`, `verse_refs[]`.
- `POST /api/v1/ai/chat/start` — создаёт/возвращает `conversation_id` (или re‑use). Возвращает приветствие и лимиты.
- `POST /api/v1/ai/chat/message` — тело: `conversation_id`, `message`; ответ: `text`, `verse_refs[]`, статус квот.
- `GET /api/v1/ai/chat/{conversation_id}/history?limit=…` — последние сообщения.
- `POST /api/v1/ai/chat/{conversation_id}/reset` — очистка оперативной памяти (и/или завершение беседы).
- `GET /api/v1/ai/limits` — текущий статус лимитов/премиум.

### Платежи/донаты

- YooKassa:
  - `POST /api/v1/payments/yookassa/create` — создать платеж (премиум/донат).
  - `POST /api/v1/webhooks/yookassa` — приём вебхука; завершение оплаты, обновление Supabase.
- YooMoney (если используется):
  - `POST /api/v1/payments/yoomoney/create` — получить ссылку.
- Telegram Stars — (опц.) endpoint для подтверждения/названия пакета.

### Календарь

- `GET /api/v1/calendar/today` — чтения дня, памятные даты, тропари (если источники доступны).

## Контракты (схемы, примеры)

Пример: `POST /api/v1/ai/chat/message`

Request:
```json
{
  "conversation_id": "b2b1d0b6-...",
  "message": "Испытываю тревогу и сомнения, какие места Писания помогут?"
}
```

Response:
```json
{
  "text": "Краткий ответ…", 
  "verse_refs": ["Мф 6:25-34", "Флп 4:6-7", "1Пет 5:7"],
  "limits": {
    "daily_limit": 5,
    "used_today": 3,
    "premium_left": 12
  },
  "model": "regular" 
}
```

## Модульность (сопоставление с текущим кодом)

- `app/services/bible_service.py` → обёртка над `utils/api_client.BibleAPIClient`.
- `app/services/bookmarks_service.py` → обёртка над методами universal_db_manager/SupabaseManager.
- `app/services/plans_service.py` → `services/universal_reading_plans` + БД.
- `app/services/topics_service.py` → Supabase topics + FTS.
- `app/services/ai_service.py` → `ask_gpt_explain`, `ask_gpt_bible_verses`, `ask_gpt_chat` + `parse_ai_response`.
- `app/services/ai_quota_service.py` → `services/ai_quota_manager` (reuse, перенос в backend, фоновые задачи).
- `app/services/premium_service.py` → `services/premium_manager`.
- `app/integrations/yookassa.py`, `yoomoney.py` → перенос из текущих сервисов.

## Безопасность

- Supabase service role key только на backend.
- JWT для внешних клиентов; для Telegram‑бота — статический API‑ключ + сигнатуры.
- CORS для веб‑клиента.
- Анти‑prompt‑injection: строгий системный промпт; фильтрация вывода; пост‑валидаторы ссылок.
- Rate Limit/Throttling (Redis/Memory) на критичных эндпоинтах.

## Наблюдаемость

- Структурные логи (JSON), корреляция `request_id`.
- Метрики: RPS/latency по эндпоинтам, успех/ошибка платежей, расход лимитов, токен‑cost.
- Трассировка (OTel) — опционально.

## Деплой

- Docker образ `backend` + `.env`:
  - `SUPABASE_URL`, `SUPABASE_KEY`
  - `OPENROUTER_API_KEY`, `OPENROUTER_PREMIUM_API_KEY`
  - `YOOKASSA_SHOP_ID`, `YOOKASSA_SECRET_KEY`, `YOOKASSA_WEBHOOK_SECRET`
  - `API_BASE_URL`, `API_KEY` (для бота), `JWT_SECRET`
- Nginx как reverse‑proxy; HTTPS (LetsEncrypt/сертификаты).
- CI/CD: build‑push Docker Hub → сервер pull‑run (как у бота сейчас).

## Миграция (пошагово)

1) Поднять FastAPI MVP:
   - Библия (chapter/reference), Закладки (CRUD), ИИ: `suggest-verses` + квоты.
2) Перевести бота на backend для этих функций (тонкий клиент: только UI + вызовы API).
3) Добавить чат‑ассистента (`/ai/chat/*`) и объяснение (`/ai/explain`).
4) Перенести Планы чтения и Темы.
5) Подключить платежи/вебхуки.
6) Подключить календарь.
7) Веб‑клиент (SPA) и/или SSR сайт на тот же API.

## Риски/вопросы

- Строгая синхронизация лимитов (backend — источник истины, бот не ведёт учёт).
- Производительность ИИ: кэширование коротких ответов; лимиты токенов; очереди.
- Совместимость форматирования (HTML/Markdown) между каналами.
- Обновление схем Supabase: миграции/скрипты.

## Итог

Да, вынести функции в FastAPI‑backend реально и целесообразно. Мы переиспользуем большую часть текущих сервисов/менеджеров, добавляем API‑контракты, единый учёт квот/платежей и открываем путь к веб‑сайту и мобильным клиентам.


