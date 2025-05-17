# Библейский бот - документация

## Обзор
Бот предоставляет доступ к текстам Библии через Telegram. Он позволяет выбирать книги и главы, сохранять закладки, искать стихи по ссылкам, получать случайные стихи и менять переводы Библии.

## Архитектура

### Структура проекта
```
├── bot.py                # Основной файл для запуска бота
├── bot_new.py            # Альтернативная версия бота (монолитная)
├── config/               # Конфигурация
│   └── settings.py       # Настройки бота
├── handlers/             # Обработчики событий
│   ├── callbacks.py      # Обработчики колбэков от кнопок
│   ├── commands.py       # Обработчики команд
│   ├── text_messages.py  # Обработчики текстовых сообщений
│   ├── bookmarks.py      # Обработчики закладок
│   └── bookmark_callbacks.py # Колбэки для работы с закладками
├── keyboards/            # Клавиатуры 
│   └── main.py           # Кнопки и клавиатуры интерфейса
├── middleware/           # Мидлвари
│   └── state.py          # Управление состоянием пользователя
└── utils/                # Вспомогательные модули
    ├── api_client.py     # Клиент для работы с API Библии
    ├── bible_data.py     # Данные о книгах и главах Библии
    └── text_utils.py     # Функции для работы с текстом
```

### Используемые технологии
- **Python** - язык программирования
- **aiogram 3.x** - фреймворк для Telegram-ботов
- **aiohttp** - асинхронная библиотека для HTTP-запросов
- **pandas** - для работы с Excel-файлами данных

## Основные функции бота

### 1. Выбор книги и главы
Доступ из меню через кнопку "📖 Выбрать книгу". Работает в два этапа:
1. Выбор книги из списка (пагинация по 10 книг)
2. Ввод номера главы

Обработчики:
- `handlers/text_messages.py`: `select_book()` - выбор книги
- `handlers/callbacks.py`: `book_selected()` - колбэк выбора книги
- `handlers/text_messages.py`: `chapter_input()` - ввод номера главы

### 2. Навигация по главам
После открытия главы можно переключаться между ними с помощью кнопок "Предыдущая глава" и "Следующая глава".

Обработчики:
- `handlers/callbacks.py`: `next_chapter()` - переход к следующей главе
- `handlers/callbacks.py`: `prev_chapter()` - переход к предыдущей главе

### 3. Поиск стихов по ссылке
Пользователь может искать стихи, указав ссылку в формате "Книга глава:стих" (например, "Быт 1:1").

Обработчики:
- `handlers/text_messages.py`: `search_verse()` - интерфейс поиска стиха
- `handlers/text_messages.py`: `verse_reference()` - обработка введенной ссылки

### 4. Закладки
Пользователь может сохранять закладки и возвращаться к ним позже.

Обработчики:
- `handlers/bookmark_callbacks.py`: `add_bookmark()` - добавление закладки
- `handlers/bookmarks.py`: `show_bookmarks()` - просмотр закладок
- `handlers/bookmark_callbacks.py`: `clear_bookmarks()` - очистка всех закладок

### 5. Случайный стих
Получение случайного стиха из Библии через кнопку "📊 Случайный стих".

Обработчик:
- `handlers/text_messages.py`: `random_verse()`

### 6. Смена перевода
Пользователь может переключаться между синодальным и современным переводом.

Обработчики:
- `handlers/text_messages.py`: `change_translation_message()`
- `handlers/callbacks.py`: `change_translation()`

### 7. Поиск по слову (опционально)
Поиск слов в тексте Библии (функция может быть отключена через настройки).

Обработчики:
- `handlers/text_messages.py`: `search_word_command()`, `process_search_query()`
- Настройка в `config/settings.py`: `ENABLE_WORD_SEARCH`

## API и данные

### API Библии
Бот использует API JustBible (https://justbible.ru/api):
- `/bible?translation=&book=&chapter=` - получение главы
- `/random?translation=` - случайный стих
- `/search?translation=&search=` - поиск по слову

### Форматы данных
1. **Книги**: ID и название книги хранятся в Excel-файле `file.xlsx`
2. **План чтения**: хранится в Excel-файле `plan.xlsx` с датами и ссылками на главы

### Кэширование
Реализовано кэширование для API-запросов в `utils/api_client.py`:
- Каждый запрос кэшируется на `CACHE_TTL` секунд (по умолчанию 3600 секунд = 1 час)
- Ключи кэша: `chapter_{book}_{chapter}_{translation}`, `search_{translation}_{query}`

## Управление состоянием

### Состояние пользователя
Управление через `middleware/state.py`:
- `chosen_book` - ID выбранной книги
- `current_chapter` - текущая глава
- `current_translation` - текущий перевод (по умолчанию "rst")
- `page` - текущая страница в списке книг
- `bookmarks` - сохраненные закладки

Функции для работы с состоянием:
- `get_chosen_book()`, `set_chosen_book()`
- `get_current_chapter()`, `set_current_chapter()`
- `get_current_translation()`, `set_current_translation()`
- `get_page()`, `set_page()`
- `get_bookmarks()`, `add_bookmark()`, `remove_bookmark()`, `clear_bookmarks()`

## База данных

### Структура базы данных
Бот использует SQLite для хранения пользовательских данных и закладок:
- Файл базы данных: `data/database.db`
- Таблицы:
  - `users` - информация о пользователях (id, username, name)
  - `bookmarks` - сохраненные закладки пользователей (user_id, book_id, chapter, display_text)

### Работа с базой данных
Класс `DatabaseManager` в `database/db_manager.py` предоставляет методы для:
- `add_user()` - добавление/обновление пользователя
- `add_bookmark()` - добавление закладки
- `get_bookmarks()` - получение списка закладок пользователя
- `remove_bookmark()` - удаление конкретной закладки
- `clear_bookmarks()` - удаление всех закладок пользователя

### Доступ к базе данных
База данных доступна для обработчиков через:
1. Middleware `database/db_middleware.py`, который добавляет объект БД в контекст диспетчера
2. Параметр `db` в функциях обработчиков

### Резервное копирование
Закладки хранятся как в базе данных, так и в состоянии пользователя, что обеспечивает работу даже при проблемах с БД.

## Специфические особенности

### Обработка длинных текстов
Тексты глав разбиваются на части перед отправкой в Telegram (лимит 4096 символов):
- `utils/text_utils.py`: `split_text()` - разбивает текст на части

### Специальные проверки для 2 Петра
В боте есть особые проверки для книги "2 Петра" (ID 47), которая имеет 3 главы:
- Предотвращение перехода на несуществующие главы
- Жестко заданный лимит в 3 главы для этой книги

### Монолитная версия
Файл `bot_new.py` содержит монолитную версию бота без модульной структуры. Основная разработка ведется в модульной версии.

## Запуск бота

1. Настройка переменных окружения:
   - Создать файл `.env` с переменной `BOT_TOKEN`

2. Установка зависимостей:
   ```
   pip install aiogram aiohttp pandas python-dotenv
   ```

3. Запуск бота:
   ```
   python bot.py
   ```

## Запуск с использованием Docker

### Использование Docker Compose (рекомендуется)

1. Настройка переменных окружения:
   - Создать файл `.env` с переменной `BOT_TOKEN`

2. Запуск с помощью Docker Compose:
   ```
   docker-compose up -d
   ```

3. Просмотр логов:
   ```
   docker-compose logs -f
   ```

4. Остановка бота:
   ```
   docker-compose down
   ```

### Использование Docker напрямую

1. Сборка образа:
   ```
   docker build -t bible-bot .
   ```

2. Запуск контейнера:
   ```
   docker run -d --name bible-bot --restart unless-stopped -v $(pwd)/data:/app/data -v $(pwd)/logs:/app/logs --env-file .env bible-bot
   ```

3. Просмотр логов:
   ```
   docker logs -f bible-bot
   ```

4. Остановка и удаление контейнера:
   ```
   docker stop bible-bot
   docker rm bible-bot
   ```

## Отладка и логирование
- Уровень логирования настраивается в `config/settings.py` через `LOG_LEVEL`
- Логи включают информацию о выборе книг, глав, API-запросах и ошибках

## Расширение функциональности

### Добавление новых функций
1. Создать обработчики в соответствующих файлах `handlers/`
2. При необходимости добавить кнопки в `keyboards/main.py` 
3. Добавить параметр в `config/settings.py` для возможности включения/отключения функции

### Добавление новых API-методов
1. Добавить метод в класс `BibleAPIClient` в `utils/api_client.py`
2. Реализовать кэширование результатов при необходимости

![CodeRabbit Pull Request Reviews](https://img.shields.io/coderabbit/prs/github/probedrik/gospel_bot?utm_source=oss&utm_medium=github&utm_campaign=probedrik%2Fgospel_bot&labelColor=171717&color=FF570A&link=https%3A%2F%2Fcoderabbit.ai&label=CodeRabbit+Reviews)
