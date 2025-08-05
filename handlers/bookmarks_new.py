"""
Новый обработчик закладок с поддержкой диапазонов и пагинации
"""
import logging
import math
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from database.universal_manager import universal_db_manager as db_manager
from keyboards.bookmarks import (
    create_bookmarks_menu_keyboard,
    create_bookmarks_list_keyboard,
    create_bookmark_action_keyboard
)
from utils.bible_data import bible_data

logger = logging.getLogger(__name__)
router = Router()

# Константы
BOOKMARKS_PER_PAGE = 16


@router.message(F.text == "📝 Мои закладки")
async def show_bookmarks_menu(message: Message, state: FSMContext):
    """Показывает главное меню закладок"""
    keyboard = create_bookmarks_menu_keyboard()
    await message.answer(
        "📝 **Мои закладки**\n\n"
        "Выберите тип закладок для просмотра:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "bookmarks_menu")
async def show_bookmarks_menu_callback(callback: CallbackQuery, state: FSMContext):
    """Показывает главное меню закладок через callback"""
    keyboard = create_bookmarks_menu_keyboard()
    await callback.message.edit_text(
        "📝 **Мои закладки**\n\n"
        "Выберите тип закладок для просмотра:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "bookmarks_bible")
async def show_bible_bookmarks(callback: CallbackQuery, state: FSMContext):
    """Показывает библейские закладки"""
    await show_bookmarks_page(callback, "bible", 0)


@router.callback_query(F.data == "bookmarks_commentaries")
async def show_commentary_bookmarks(callback: CallbackQuery, state: FSMContext):
    """Показывает сохраненные разборы"""
    await show_bookmarks_page(callback, "commentaries", 0)


@router.callback_query(F.data.regexp(r'^bookmarks_page_(bible|commentaries)_(\d+)$'))
async def show_bookmarks_page_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик переключения страниц закладок"""
    import re
    match = re.match(
        r'^bookmarks_page_(bible|commentaries)_(\d+)$', callback.data)
    if match:
        bookmark_type = match.group(1)
        page = int(match.group(2))
        await show_bookmarks_page(callback, bookmark_type, page)


async def show_bookmarks_page(callback: CallbackQuery, bookmark_type: str, page: int):
    """
    Показывает страницу закладок определенного типа

    Args:
        callback: Callback query
        bookmark_type: Тип закладок ("bible" или "commentaries")
        page: Номер страницы (начиная с 0)
    """
    user_id = callback.from_user.id

    try:
        if bookmark_type == "bible":
            # Получаем библейские закладки
            raw_bookmarks = await db_manager.get_bookmarks(user_id)
            bookmarks = []

            for bookmark in raw_bookmarks:
                # Проверяем формат данных (словарь для Supabase/PostgreSQL или кортеж для SQLite)
                if isinstance(bookmark, dict):
                    # Supabase/PostgreSQL формат - словарь
                    book_id = bookmark.get('book_id')
                    chapter_start = bookmark.get('chapter_start')
                    chapter_end = bookmark.get('chapter_end')
                    verse_start = bookmark.get('verse_start')
                    verse_end = bookmark.get('verse_end')
                    display_text = bookmark.get('display_text')
                    note = bookmark.get('note')
                    created_at = bookmark.get('created_at')
                else:
                    # SQLite формат - кортеж
                    if len(bookmark) >= 8:  # Новый формат с chapter_start, chapter_end
                        book_id, chapter_start, chapter_end, display_text, verse_start, verse_end, note, created_at = bookmark
                    else:  # Старый формат для совместимости
                        book_id, chapter_start, display_text = bookmark[:3]
                        chapter_end = verse_start = verse_end = note = created_at = None

                # Получаем название книги
                book_name = bible_data.get_book_name_by_id(book_id)

                bookmarks.append({
                    'book_id': book_id,
                    'book_name': book_name,
                    'chapter_start': chapter_start,
                    'chapter_end': chapter_end,
                    'verse_start': verse_start,
                    'verse_end': verse_end,
                    'display_text': display_text,
                    'note': note,
                    'created_at': created_at
                })

            title = "📖 **Закладки Библии**"
            empty_message = "У вас пока нет сохраненных закладок Библии.\\n\\n" \
                "Добавляйте закладки при чтении глав и стихов!"

        elif bookmark_type == "commentaries":
            # Получаем сохраненные разборы
            raw_commentaries = await db_manager.get_saved_commentaries(user_id)
            bookmarks = []

            for commentary in raw_commentaries:
                bookmarks.append({
                    'id': commentary.get('id'),
                    'reference_text': commentary.get('reference_text', 'Неизвестно'),
                    'commentary_text': commentary.get('commentary_text', ''),
                    'commentary_type': commentary.get('commentary_type', 'ai'),
                    'created_at': commentary.get('created_at')
                })

            title = "💬 **Сохраненные разборы**"
            empty_message = "У вас пока нет сохраненных разборов.\n\n" \
                "Сохраняйте интересные толкования при чтении!"

        else:
            await callback.answer("Неизвестный тип закладок")
            return

        # Проверяем, есть ли закладки
        if not bookmarks:
            keyboard = create_bookmarks_menu_keyboard()
            await callback.message.edit_text(
                f"{title}\n\n{empty_message}",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            await callback.answer()
            return

        # Вычисляем пагинацию
        total_bookmarks = len(bookmarks)
        total_pages = math.ceil(total_bookmarks / BOOKMARKS_PER_PAGE)

        # Проверяем корректность номера страницы
        if page < 0 or page >= total_pages:
            page = 0

        # Получаем закладки для текущей страницы
        start_index = page * BOOKMARKS_PER_PAGE
        end_index = min(start_index + BOOKMARKS_PER_PAGE, total_bookmarks)
        page_bookmarks = bookmarks[start_index:end_index]

        # Создаем клавиатуру
        keyboard = create_bookmarks_list_keyboard(
            page_bookmarks, page, bookmark_type, total_pages
        )

        # Формируем текст сообщения
        message_text = f"{title}\n\n"
        if total_pages > 1:
            message_text += f"Страница {page + 1} из {total_pages}\n"
            message_text += f"Показано {len(page_bookmarks)} из {total_bookmarks} закладок\n\n"
        else:
            message_text += f"Всего закладок: {total_bookmarks}\n\n"

        message_text += "Выберите закладку для открытия:"

        await callback.message.edit_text(
            message_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при показе закладок: {e}")
        await callback.answer("Произошла ошибка при загрузке закладок")


@router.callback_query(F.data.regexp(r'^open_bookmark_(bible|commentaries)_(\d+)$'))
async def open_bookmark(callback: CallbackQuery, state: FSMContext):
    """Открывает выбранную закладку"""
    import re
    match = re.match(
        r'^open_bookmark_(bible|commentaries)_(\d+)$', callback.data)
    if not match:
        await callback.answer("Ошибка в данных закладки")
        return

    bookmark_type = match.group(1)
    bookmark_index = int(match.group(2))
    user_id = callback.from_user.id

    try:
        if bookmark_type == "bible":
            # Открываем библейскую закладку
            await open_bible_bookmark(callback, state, bookmark_index)
        elif bookmark_type == "commentaries":
            # Открываем сохраненный разбор
            await open_commentary_bookmark(callback, state, bookmark_index)

    except Exception as e:
        logger.error(f"Ошибка при открытии закладки: {e}")
        await callback.answer("Произошла ошибка при открытии закладки")


async def open_bible_bookmark(callback: CallbackQuery, state: FSMContext, bookmark_index: int):
    """Открывает библейскую закладку"""
    user_id = callback.from_user.id

    # Получаем все закладки и находим нужную
    raw_bookmarks = await db_manager.get_bookmarks(user_id)

    if bookmark_index >= len(raw_bookmarks):
        await callback.answer("Закладка не найдена")
        return

    bookmark = raw_bookmarks[bookmark_index]

    # Парсим данные закладки
    if isinstance(bookmark, dict):
        # Supabase/PostgreSQL формат - словарь
        book_id = bookmark.get('book_id')
        chapter_start = bookmark.get('chapter_start')
        chapter_end = bookmark.get('chapter_end')
        verse_start = bookmark.get('verse_start')
        verse_end = bookmark.get('verse_end')
        display_text = bookmark.get('display_text')
        note = bookmark.get('note')
    else:
        # SQLite формат - кортеж
        if len(bookmark) >= 8:
            book_id, chapter_start, chapter_end, display_text, verse_start, verse_end, note, created_at = bookmark
        else:
            book_id, chapter_start, display_text = bookmark[:3]
            chapter_end = verse_start = verse_end = note = None

    # Формируем ссылку для открытия
    book_name = bible_data.get_book_name_by_id(book_id)

    if chapter_end and chapter_end != chapter_start:
        reference = f"{book_name} {chapter_start}-{chapter_end}"
    elif verse_start and verse_end and verse_start != verse_end:
        reference = f"{book_name} {chapter_start}:{verse_start}-{verse_end}"
    elif verse_start:
        reference = f"{book_name} {chapter_start}:{verse_start}"
    else:
        reference = f"{book_name} {chapter_start}"

    # Открываем текст через обработчик ссылок
    from handlers.verse_reference import get_verse_by_reference
    try:
        text, info = await get_verse_by_reference(state, reference)

        # Создаем клавиатуру с действиями
        page = bookmark_index // BOOKMARKS_PER_PAGE
        keyboard = create_bookmark_action_keyboard(
            bookmark_index, "bible", page, bookmark_data=bookmark)

        # Используем HTML формат, как в остальном приложении
        message_text = f"📖 <b>{reference}</b>\n\n{text}"
        if note:
            message_text += f"\n\n📝 <i>Заметка:</i> {note}"

        await callback.message.edit_text(
            message_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при открытии библейской закладки: {e}")
        await callback.answer("Ошибка при открытии текста")


async def open_commentary_bookmark(callback: CallbackQuery, state: FSMContext, bookmark_index: int):
    """Открывает сохраненный разбор"""
    user_id = callback.from_user.id

    # Получаем все сохраненные разборы и находим нужный
    commentaries = await db_manager.get_saved_commentaries(user_id)

    if bookmark_index >= len(commentaries):
        await callback.answer("Разбор не найден")
        return

    commentary = commentaries[bookmark_index]

    # Создаем клавиатуру с действиями
    page = bookmark_index // BOOKMARKS_PER_PAGE
    keyboard = create_bookmark_action_keyboard(
        bookmark_index, "commentaries", page)

    # Формируем сообщение
    reference = commentary.get('reference_text', 'Неизвестно')
    commentary_text = commentary.get('commentary_text', 'Текст не найден')
    commentary_type = commentary.get('commentary_type', 'ai')

    type_name = "🤖 ИИ разбор" if commentary_type == "ai" else "📝 Комментарий"

    # Убираем лишние символы и форматируем как в оригинальном ИИ разборе
    clean_text = commentary_text.replace(
        '\\n\\n', '\n').replace('\\n', '\n').strip()

    # Используем тот же формат, что и в format_ai_or_commentary
    import html
    import re

    # СНАЧАЛА очищаем от HTML тегов
    cleaned_text = re.sub(r'<[^>]*>', '', clean_text)  # Удаляем все HTML теги

    # ЗАТЕМ очищаем от markdown символов
    # **жирный** → жирный
    cleaned_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned_text)
    cleaned_text = re.sub(r'\*([^*]+)\*', r'\1',
                          cleaned_text)  # *курсив* → курсив
    cleaned_text = re.sub(r'`([^`]+)`', r'\1', cleaned_text)  # `код` → код

    cleaned_text = cleaned_text.strip()
    escaped_text = html.escape(cleaned_text)
    message_text = f"<b>{reference}</b>\n\n<b>{type_name}</b>\n\n<blockquote>{escaped_text}</blockquote>"

    await callback.message.edit_text(
        message_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.regexp(r'^delete_bookmark_(bible|commentaries)_(\d+)$'))
async def delete_bookmark(callback: CallbackQuery, state: FSMContext):
    """Удаляет закладку"""
    import re
    match = re.match(
        r'^delete_bookmark_(bible|commentaries)_(\d+)$', callback.data)
    if not match:
        await callback.answer("Ошибка в данных закладки")
        return

    bookmark_type = match.group(1)
    bookmark_index = int(match.group(2))
    user_id = callback.from_user.id

    try:
        if bookmark_type == "bible":
            # Удаляем библейскую закладку
            raw_bookmarks = await db_manager.get_bookmarks(user_id)
            if bookmark_index < len(raw_bookmarks):
                bookmark = raw_bookmarks[bookmark_index]

                if isinstance(bookmark, dict):
                    # Supabase/PostgreSQL формат - словарь
                    book_id = bookmark.get('book_id')
                    chapter_start = bookmark.get('chapter_start')
                    chapter_end = bookmark.get('chapter_end')
                    verse_start = bookmark.get('verse_start')
                    verse_end = bookmark.get('verse_end')
                else:
                    # SQLite формат - кортеж
                    book_id = bookmark[0]
                    chapter_start = bookmark[1]
                    chapter_end = bookmark[2] if len(bookmark) > 2 else None
                    verse_start = bookmark[4] if len(bookmark) > 4 else None
                    verse_end = bookmark[5] if len(bookmark) > 5 else None

                await db_manager.remove_bookmark(user_id, book_id, chapter_start, chapter_end, verse_start, verse_end)
                await callback.answer("✅ Закладка удалена")
            else:
                await callback.answer("Закладка не найдена")

        elif bookmark_type == "commentaries":
            # Удаляем сохраненный разбор
            commentaries = await db_manager.get_saved_commentaries(user_id)
            if bookmark_index < len(commentaries):
                commentary = commentaries[bookmark_index]
                commentary_id = commentary.get('id')
                if commentary_id:
                    await db_manager.delete_saved_commentary(user_id, commentary_id=commentary_id)
                    await callback.answer("✅ Разбор удален")
                else:
                    await callback.answer("Не удалось найти ID разбора")
            else:
                await callback.answer("Разбор не найден")

        # Возвращаемся к списку закладок
        page = bookmark_index // BOOKMARKS_PER_PAGE
        await show_bookmarks_page(callback, bookmark_type, page)

    except Exception as e:
        logger.error(f"Ошибка при удалении закладки: {e}")
        await callback.answer("Произошла ошибка при удалении")


@router.callback_query(F.data == "back_to_main")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    from keyboards.main import get_main_keyboard

    # Удаляем сообщение с inline клавиатурой
    await callback.message.delete()

    # Отправляем новое сообщение с обычной клавиатурой
    await callback.message.answer(
        "🏠 Главное меню",
        reply_markup=await get_main_keyboard()
    )
    await callback.answer()
