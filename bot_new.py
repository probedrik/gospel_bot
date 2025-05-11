# ===============================
# Импорт стандартных модулей
# ===============================

"""
# Пример содержимого config.py для улучшенной архитектуры:
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = "https://justbible.ru/api"
AVAILABLE_TRANSLATIONS = {
    "rst": "Синодальный перевод",
    "rbo": "Современный перевод РБО"
}
DATA_PATH = "./data"
"""

import logging
import asyncio
from datetime import datetime

# ===============================
# Импорт библиотек для бота и HTTP-запросов
# ===============================
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
import aiohttp
import pandas as pd

# ===============================
# Настройка логирования
# ===============================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ===============================
# Конфигурация бота
# ===============================

# Загружаем переменные окружения из .env файла (если он есть)
load_dotenv()

# Получаем токен бота из переменной окружения или используем запасной вариант
BOT_TOKEN = os.getenv(
    "BOT_TOKEN", "7915703119:AAFMqfiFwYw6p-deMgrVghRBcXXtGKMCs8g")
MESS_MAX_LENGTH = 4096

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ===============================
# Загрузка данных из Excel
# ===============================
try:
    df = pd.read_excel("file.xlsx")
    df1 = pd.read_excel("plan.xlsx")
    df1["day"] = df1["day"].dt.strftime("%Y-%m-%d")
    book_names = df["Книга Библии"].tolist()
    book_values = df["book"].tolist()
    book_dict = dict(zip(book_values, book_names))
except FileNotFoundError:
    logging.error("Ошибка: файлы не найдены.")
    exit()
except KeyError as e:
    logging.error(f"Ошибка в структуре Excel: {e}")
    exit()

# ===============================
# Глобальные данные Библии
# ===============================
# Словарь соответствия сокращений книг - ОБНОВЛЕННЫЙ по данным из Excel
book_dict2 = {
    "Быт": 1, "Исх": 2, "Лев": 3, "Чис": 4, "Втор": 5, "Нав": 6, "Суд": 7, "Руф": 8,
    "1Цар": 9, "2Цар": 10, "3Цар": 11, "4Цар": 12, "1Пар": 13, "2Пар": 14, "Езд": 15,
    "Неем": 16, "Есф": 17, "Иов": 18, "Пс": 19, "Прит": 20, "Еккл": 21, "Песн": 22,
    "Ис": 23, "Иер": 24, "Плач": 25, "Иез": 26, "Дан": 27, "Ос": 28, "Иоил": 29,
    "Ам": 30, "Авд": 31, "Ион": 32, "Мих": 33, "Наум": 34, "Авв": 35, "Соф": 36,
    "Агг": 37, "Зах": 38, "Мал": 39, "Мф": 40, "Мк": 41, "Лк": 42, "Ин": 43,
    "Деян": 44, "Иак": 45, "1Пет": 46, "2Пет": 47, "1Ин": 48, "2Ин": 49, "3Ин": 50,
    "Иуд": 51, "Рим": 52, "1Кор": 53, "2Кор": 54, "Гал": 55, "Еф": 56, "Флп": 57,
    "Кол": 58, "1Фес": 59, "2Фес": 60, "1Тим": 61, "2Тим": 62, "Тит": 63, "Флм": 64,
    "Евр": 65, "Откр": 66
}

# Максимальное количество глав в каждой книге (правильные значения)
max_chapters = {
    # Ветхий Завет
    1: 50, 2: 40, 3: 27, 4: 36, 5: 34, 6: 24, 7: 21, 8: 4,
    9: 31, 10: 24, 11: 22, 12: 25, 13: 29, 14: 36, 15: 10,
    16: 13, 17: 10, 18: 42, 19: 150, 20: 31, 21: 12, 22: 8,
    23: 66, 24: 52, 25: 5, 26: 48, 27: 12, 28: 14, 29: 3,
    30: 9, 31: 1, 32: 4, 33: 7, 34: 3, 35: 3, 36: 3,
    37: 2, 38: 14, 39: 4,
    # Новый Завет
    40: 28, 41: 16, 42: 24, 43: 21, 44: 28, 45: 5, 46: 5,
    47: 3, 48: 5, 49: 1, 50: 1, 51: 1, 52: 16, 53: 16,
    54: 13, 55: 6, 56: 6, 57: 4, 58: 4, 59: 5, 60: 3,
    61: 6, 62: 4, 63: 3, 64: 1, 65: 13, 66: 22
}

# ===============================
# Глобальные состояния пользователей
# ===============================
user_page = {}
user_chosen_book = {}
user_current_chapter = {}

# ===============================
# API-функции
# ===============================

# Создаем кэш для хранения результатов запросов
_chapter_cache = {}
_session = None


async def get_session():
    global _session
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession()
    return _session


async def close_session():
    global _session
    if _session and not _session.closed:
        await _session.close()


async def get_chapter_gospel(book: int, chapter: int, translation: str = "rst") -> str:
    # Проверяем наличие результата в кэше
    cache_key = f"{book}_{chapter}_{translation}"
    if cache_key in _chapter_cache:
        return _chapter_cache[cache_key]

    url = f"https://justbible.ru/api/bible?translation={translation}&book={book}&chapter={chapter}"
    try:
        session = await get_session()
        async with session.get(url, timeout=10) as response:
            response.raise_for_status()
            data = await response.json()
    except Exception as e:
        logging.error(f"API Error: {e}")
        return f"Ошибка: {e}"

    verses = [v for k, v in data.items() if k != "info"]
    testament = "Ветхий завет" if book < 40 else "Новый завет"
    text = f"{testament}. {data['info']['book']} {chapter}:\n{' '.join(verses)}"

    # Сохраняем результат в кэш
    _chapter_cache[cache_key] = text
    return text


async def get_random_verse_rbo(translation: str = "rbo") -> str:
    try:
        session = await get_session()
        async with session.get(f"https://justbible.ru/api/random?translation={translation}", timeout=10) as response:
            data = await response.json()
        return f"{data['info']} - {data['verse']}"
    except Exception as e:
        logging.error(f"Random verse error: {e}")
        return "Не удалось получить стих"


async def search_bible_text(search_query: str, translation: str = "rst") -> str:
    """
    Поиск слова или фразы в тексте Библии
    """
    if len(search_query) < 3:
        return "Поисковый запрос должен содержать минимум 3 символа."

    url = f"https://justbible.ru/api/search?translation={translation}&search={search_query}"
    try:
        session = await get_session()
        async with session.get(url, timeout=15) as response:
            response.raise_for_status()
            data = await response.json()

        if not data:
            return f"По запросу '{search_query}' ничего не найдено."

        result = f"Результаты поиска '{search_query}' ({len(data)} найдено):\n\n"

        for i, item in enumerate(data, 1):
            if i > 20:  # Ограничим вывод первыми 20 результатами
                result += f"\n... и еще {len(data) - 20} результатов"
                break

            result += f"{i}. {item['reference']}: {item['text']}\n\n"

        return result
    except Exception as e:
        logging.error(f"Search error: {e}")
        return f"Ошибка при поиске: {e}"

# ===============================
# Вспомогательная функция для разбивки длинных сообщений
# ===============================


def split_text(text: str, max_length: int = MESS_MAX_LENGTH) -> list[str]:
    """
    Разбивает длинный текст на части, не превышающие максимальную длину.
    Старается сохранить целостность абзацев.
    """
    if len(text) <= max_length:
        return [text]

    parts = []
    while len(text) > 0:
        # Ищем последний перенос строки в допустимом диапазоне
        split_position = text.rfind('\n', 0, max_length)

        # Если не нашли перенос - ищем последний пробел
        if split_position == -1:
            split_position = text.rfind(' ', 0, max_length)

        # Если совсем не нашли подходящего места - форсированно обрезаем
        if split_position == -1:
            split_position = max_length

        part = text[:split_position].strip()
        if part:
            parts.append(part)
        text = text[split_position:].strip()

    return parts
# ===============================
# Функции клавиатур (ИСПРАВЛЕННЫЕ)
# ===============================


def create_book_keyboard(chat_id: int, page: int = 0, per_page: int = 10) -> InlineKeyboardMarkup:
    buttons = []
    start = page * per_page
    end = start + per_page

    # Добавляем кнопки книг
    for i in range(start, min(end, len(book_names))):
        buttons.append([
            InlineKeyboardButton(
                text=book_names[i],
                callback_data=f"select_book_{book_values[i]}"
            )
        ])

    # Добавляем навигацию
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"nav_page_{page-1}"
            )
        )
    if end < len(book_names):
        nav_buttons.append(
            InlineKeyboardButton(
                text="➡️ Вперед",
                callback_data=f"nav_page_{page+1}"
            )
        )

    if nav_buttons:
        buttons.append(nav_buttons)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_next_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text="Следующая глава",
                callback_data="next_chapter"
            )
        ]]
    )


def create_navigation_keyboard(has_previous: bool = True, has_next: bool = True) -> InlineKeyboardMarkup:
    buttons = []

    nav_row = []
    if has_previous:
        nav_row.append(
            InlineKeyboardButton(
                text="⬅️ Предыдущая глава",
                callback_data="prev_chapter"
            )
        )

    if has_next:
        nav_row.append(
            InlineKeyboardButton(
                text="➡️ Следующая глава",
                callback_data="next_chapter"
            )
        )

    buttons.append(nav_row)

    # Добавляем кнопку возврата в главное меню
    buttons.append([
        InlineKeyboardButton(
            text="🏠 Вернуться в меню",
            callback_data="back_to_menu"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_reading_buttons(reading_str: str) -> InlineKeyboardMarkup:
    buttons = []
    for part in reading_str.split(";"):
        part = part.strip()
        if not part:
            continue

        try:
            book_code, chapters = part.split(".")
            book_code = book_code.strip()
            chapters = chapters.strip()

            if book_code not in book_dict2:
                continue

            book_id = book_dict2[book_code]

            # Обработка диапазона глав
            if "-" in chapters:
                start, end = map(int, chapters.split("-"))
                for chapter in range(start, end+1):
                    buttons.append([
                        InlineKeyboardButton(
                            text=f"{book_code} {chapter}",
                            callback_data=f"daily_{book_id}_{chapter}"
                        )
                    ])
            else:
                buttons.append([
                    InlineKeyboardButton(
                        text=f"{book_code} {chapters}",
                        callback_data=f"daily_{book_id}_{chapters}"
                    )
                ])
        except Exception as e:
            logging.error(f"Error parsing reading: {e}")

    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ===============================
# Обработчики сообщений
# ===============================


@dp.message(Command("start"))
async def start(message: types.Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Выбрать книгу, главу")],
            [KeyboardButton(text="Случайные главы")],
            [KeyboardButton(text="Поиск по слову")],
            [KeyboardButton(text="Что читать сегодня")]
        ],
        resize_keyboard=True
    )

    welcome_text = (
        "🙏 Добро пожаловать в Библейский бот!\n\n"
        "Этот бот поможет вам:\n"
        "📖 Читать книги Библии\n"
        "✨ Получать случайные стихи\n"
        "🔍 Искать слова в тексте Библии\n"
        "📅 Следовать ежедневному плану чтения\n\n"
        "Используйте кнопки меню ниже для навигации."
    )

    await message.answer(welcome_text, reply_markup=kb)


@dp.message(F.text == "Выбрать книгу, главу")
async def book_selection(message: types.Message):
    user_page[message.chat.id] = 0
    await message.answer(
        "Выберите книгу:",
        reply_markup=create_book_keyboard(message.chat.id)
    )


@dp.message(F.text == "Случайные главы")
async def random_verse(message: types.Message):
    text = await get_random_verse_rbo()
    await message.answer(text)


@dp.message(F.text == "Что читать сегодня")
async def daily_reading(message: types.Message):
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        plan = df1[df1["day"] == today].iloc[0]
        await message.answer(
            f"Чтение на {today}:",
            reply_markup=create_reading_buttons(plan["book_list"])
        )
    except IndexError:
        await message.answer("На сегодня чтений нет")

# ===============================
# Обработчики колбэков
# ===============================


@dp.callback_query(F.data.startswith("select_book_"))
async def book_selected(callback: types.CallbackQuery):
    book_id = int(callback.data.split("_")[2])
    user_chosen_book[callback.message.chat.id] = book_id

    book_name = book_dict.get(book_id, f"Книга {book_id}")

    # Используем правильные значения из нашего словаря
    max_chapter = max_chapters.get(book_id, 150)

    logging.info(
        f"Выбрана книга: {book_name} (ID: {book_id}), макс. глав: {max_chapter}")

    await callback.answer(f"Выбрана книга: {book_name}")
    await callback.message.answer(
        f"Выбрана книга: {book_name}\n"
        f"Введите номер главы (от 1 до {max_chapter}):"
    )


@dp.callback_query(F.data.startswith("nav_page_"))
async def page_navigation(callback: types.CallbackQuery):
    page = int(callback.data.split("_")[2])
    chat_id = callback.message.chat.id
    user_page[chat_id] = page
    await callback.message.edit_reply_markup(
        reply_markup=create_book_keyboard(chat_id, page)
    )


@dp.callback_query(F.data == "next_chapter")
async def next_chapter(callback: types.CallbackQuery):
    chat_id = callback.message.chat.id
    if chat_id not in user_chosen_book or chat_id not in user_current_chapter:
        return await callback.answer("Сначала выберите книгу и главу")

    book = user_chosen_book[chat_id]
    chapter = user_current_chapter[chat_id] + 1

    # ПРИМЕЧАНИЕ: 2 Петра имеет ID 47, а не 61
    # Специальная проверка для 2 Петра (ID 47)
    if book == 47 and chapter > 3:  # 2 Петра имеет 3 главы
        await callback.answer(f"Это последняя глава книги")
        return

    # Для других книг используем словарь max_chapters
    max_chapter = max_chapters.get(book, 150)

    if chapter > max_chapter:
        await callback.answer(f"Это последняя глава книги")
        return

    text = await get_chapter_gospel(book, chapter)

    # Проверка успешности получения текста
    if "Ошибка:" in text:
        await callback.answer("Глава не найдена")
        return

    user_current_chapter[chat_id] = chapter

    for part in split_text(text):  # Разбиваем перед отправкой
        await callback.message.answer(part)

    # Используем новую клавиатуру с навигацией
    has_previous = chapter > 1
    # Проверка для 2 Петра (ID 47)
    has_next = chapter < 3 if book == 47 else chapter < max_chapter
    await callback.message.answer(
        "Выберите действие:",
        reply_markup=create_navigation_keyboard(has_previous, has_next)
    )
    await callback.answer()


@dp.callback_query(F.data == "prev_chapter")
async def prev_chapter(callback: types.CallbackQuery):
    chat_id = callback.message.chat.id
    if chat_id not in user_chosen_book or chat_id not in user_current_chapter:
        return await callback.answer("Сначала выберите книгу и главу")

    book = user_chosen_book[chat_id]
    chapter = user_current_chapter[chat_id] - 1

    # Проверяем, не вышли ли за пределы первой главы
    if chapter < 1:
        await callback.answer("Это первая глава книги")
        return

    text = await get_chapter_gospel(book, chapter)

    # Проверка успешности получения текста
    if "Ошибка:" in text:
        await callback.answer("Глава не найдена")
        return

    user_current_chapter[chat_id] = chapter

    for part in split_text(text):
        await callback.message.answer(part)

    # Используем новую клавиатуру с навигацией
    has_previous = chapter > 1
    # Получаем максимальное количество глав
    # ПРИМЕЧАНИЕ: 2 Петра имеет ID 47, а не 61
    # Специальная проверка для 2 Петра (ID 47)
    if book == 47:
        max_chapter = 3  # 2 Петра имеет 3 главы
    else:
        max_chapter = max_chapters.get(book, 150)

    has_next = chapter < max_chapter
    await callback.message.answer(
        "Выберите действие:",
        reply_markup=create_navigation_keyboard(has_previous, has_next)
    )
    await callback.answer()


@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Выбрать книгу, главу")],
            [KeyboardButton(text="Случайные главы")],
            [KeyboardButton(text="Поиск по слову")],
            [KeyboardButton(text="Что читать сегодня")]
        ],
        resize_keyboard=True
    )
    await callback.message.answer("Главное меню:", reply_markup=kb)
    await callback.answer()


@dp.callback_query(F.data.startswith("daily_"))
async def daily_selected(callback: types.CallbackQuery):
    _, book_id, chapter = callback.data.split("_")
    book_id = int(book_id)
    chapter = int(chapter)

    # Сохраняем выбранную книгу и главу
    user_chosen_book[callback.message.chat.id] = book_id
    user_current_chapter[callback.message.chat.id] = chapter

    text = await get_chapter_gospel(book_id, chapter)

    for part in split_text(text):  # Разбиваем перед отправкой
        await callback.message.answer(part)

    # Используем новую клавиатуру с навигацией
    has_previous = chapter > 1

    # ПРИМЕЧАНИЕ: 2 Петра имеет ID 47, а не 61
    # Специальная проверка для 2 Петра (ID 47)
    if book_id == 47:
        max_chapter = 3  # 2 Петра имеет 3 главы
    else:
        max_chapter = max_chapters.get(book_id, 150)

    has_next = chapter < max_chapter

    await callback.message.answer(
        "Выберите действие:",
        reply_markup=create_navigation_keyboard(has_previous, has_next)
    )


@dp.message(F.text.isdigit())
async def chapter_input(message: types.Message):
    chat_id = message.chat.id
    if chat_id not in user_chosen_book:
        return await message.answer("Сначала выберите книгу из списка")

    try:
        chapter = int(message.text)
        book = user_chosen_book[chat_id]

        # ПРИМЕЧАНИЕ: 2 Петра имеет ID 47, а не 61
        # Специальная проверка для 2 Петра (ID 47)
        if book == 47:  # 2 Петра
            max_chapter = 3  # Жестко закрепляем 3 главы
        else:
            # Для других книг используем словарь max_chapters
            max_chapter = max_chapters.get(book, 150)

        book_name = book_dict.get(book, f"Книга {book}")
        logging.info(
            f"Ввод главы для {book_name} (ID: {book}): введено {chapter}, макс. {max_chapter}")

        if chapter < 1 or chapter > max_chapter:
            return await message.answer(f"Книга '{book_name}' содержит {max_chapter} глав. Пожалуйста, введите корректный номер главы (от 1 до {max_chapter})")

        text = await get_chapter_gospel(book, chapter)

        # Дополнительная проверка успешности получения текста
        if "Ошибка:" in text:
            return await message.answer(f"Глава не найдена. {text}")

        user_current_chapter[chat_id] = chapter

        for part in split_text(text):  # Разбиваем перед отправкой
            await message.answer(part)

        # Добавляем клавиатуру навигации
        has_previous = chapter > 1
        # Проверка для 2 Петра (ID 47)
        has_next = chapter < 3 if book == 47 else chapter < max_chapter
        await message.answer(
            "Выберите действие:",
            reply_markup=create_navigation_keyboard(has_previous, has_next)
        )
    except Exception as e:
        logging.error(f"Error in chapter_input: {e}")
        await message.answer(f"Произошла ошибка: {e}. Пожалуйста, попробуйте еще раз.")


# ===============================
# Обработчики для поиска по слову
# ===============================

# Словарь для хранения состояния поиска
user_search_state = {}


@dp.message(F.text == "Поиск по слову")
async def search_word_command(message: types.Message):
    """Обработчик для команды поиска по слову"""
    user_search_state[message.chat.id] = "waiting_for_search_query"

    # Создаем клавиатуру с кнопкой отмены
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Отмена поиска")]
        ],
        resize_keyboard=True
    )

    await message.answer(
        "Введите слово или фразу для поиска в тексте Библии (минимум 3 символа):",
        reply_markup=kb
    )


@dp.message(F.text == "Отмена поиска")
async def cancel_search(message: types.Message):
    """Обработчик для отмены поиска"""
    if message.chat.id in user_search_state:
        del user_search_state[message.chat.id]

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Выбрать книгу, главу")],
            [KeyboardButton(text="Случайные главы")],
            [KeyboardButton(text="Поиск по слову")],
            [KeyboardButton(text="Что читать сегодня")]
        ],
        resize_keyboard=True
    )

    await message.answer("Поиск отменен. Вернулись в главное меню.", reply_markup=kb)


@dp.message(lambda message: message.chat.id in user_search_state and user_search_state[message.chat.id] == "waiting_for_search_query")
async def process_search_query(message: types.Message):
    """Обработчик для поиска по введенному запросу"""
    search_query = message.text.strip()

    # Удаляем состояние поиска
    del user_search_state[message.chat.id]

    # Возвращаем основную клавиатуру
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Выбрать книгу, главу")],
            [KeyboardButton(text="Случайные главы")],
            [KeyboardButton(text="Поиск по слову")],
            [KeyboardButton(text="Что читать сегодня")]
        ],
        resize_keyboard=True
    )

    # Отправляем сообщение о начале поиска
    await message.answer(f"Ищу '{search_query}' в тексте Библии...", reply_markup=kb)

    # Выполняем поиск
    result = await search_bible_text(search_query)

    # Разбиваем результат на части, если он слишком длинный
    for part in split_text(result):
        await message.answer(part)

# ===============================
# Запуск бота
# ===============================


async def main():
    # Регистрируем обработчик для корректного закрытия соединений
    try:
        logging.info("Starting bot...")
        await dp.start_polling(bot)
    finally:
        logging.info("Closing HTTP session...")
        await close_session()
        logging.info("Bot stopped")

if __name__ == "__main__":
    asyncio.run(main())
