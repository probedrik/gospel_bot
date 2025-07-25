"""
Обработчики для кнопок закладок
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from database.universal_manager import universal_db_manager as db_manager
from utils.bookmark_utils import parse_bookmark_callback, format_bookmark_reference
from utils.bible_data import bible_data

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data.regexp(r'^bookmark_(add|remove)_\d+_\d+_\d+_\d+(_\d+)?$'))
async def handle_bookmark_action(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик добавления/удаления закладок
    
    Формат callback_data: bookmark_{action}_{book_id}_{chapter_start}_{chapter_end}_{verse_start}_{verse_end}
    где 0 означает отсутствие значения
    """
    user_id = callback.from_user.id
    
    # Парсим callback_data
    bookmark_data = parse_bookmark_callback(callback.data)
    if not bookmark_data:
        await callback.answer("Ошибка в данных закладки")
        return
    
    action = bookmark_data['action']
    book_id = bookmark_data['book_id']
    chapter_start = bookmark_data['chapter_start']
    chapter_end = bookmark_data['chapter_end']
    verse_start = bookmark_data['verse_start']
    verse_end = bookmark_data['verse_end']
    
    try:
        # Получаем название книги
        book_name = bible_data.get_book_name_by_id(book_id)
        if not book_name:
            await callback.answer("Книга не найдена")
            return
        
        # Формируем отображаемую ссылку
        display_text = format_bookmark_reference(
            book_name, chapter_start, chapter_end, verse_start, verse_end
        )
        
        if action == "add":
            # Добавляем закладку
            success = await db_manager.add_bookmark(
                user_id=user_id,
                book_id=book_id,
                chapter_start=chapter_start,
                chapter_end=chapter_end,
                verse_start=verse_start,
                verse_end=verse_end,
                display_text=display_text
            )
            
            if success:
                await callback.answer(f"✅ Добавлено в закладки: {display_text}")
                
                # Обновляем кнопку в сообщении
                await update_bookmark_button_in_message(
                    callback, book_id, chapter_start, chapter_end, 
                    verse_start, verse_end, is_bookmarked=True
                )
            else:
                await callback.answer("❌ Ошибка при добавлении закладки")
        
        elif action == "remove":
            # Удаляем закладку
            success = await db_manager.remove_bookmark(
                user_id, book_id, chapter_start, chapter_end, verse_start, verse_end
            )
            
            if success:
                await callback.answer(f"🗑️ Удалено из закладок: {display_text}")
                
                # Обновляем кнопку в сообщении
                await update_bookmark_button_in_message(
                    callback, book_id, chapter_start, chapter_end, 
                    verse_start, verse_end, is_bookmarked=False
                )
            else:
                await callback.answer("❌ Ошибка при удалении закладки")
    
    except Exception as e:
        logger.error(f"Ошибка при обработке закладки: {e}")
        await callback.answer("Произошла ошибка при обработке закладки")


async def update_bookmark_button_in_message(callback: CallbackQuery, book_id: int, 
                                          chapter_start: int, chapter_end: int = None,
                                          verse_start: int = None, verse_end: int = None,
                                          is_bookmarked: bool = False):
    """
    Обновляет кнопку закладки в сообщении
    
    Args:
        callback: CallbackQuery для обновления сообщения
        book_id: ID книги
        chapter_start: Начальная глава
        chapter_end: Конечная глава
        verse_start: Начальный стих
        verse_end: Конечный стих
        is_bookmarked: Новое состояние закладки
    """
    try:
        from utils.bookmark_utils import create_bookmark_button
        
        # Получаем текущую клавиатуру
        current_markup = callback.message.reply_markup
        if not current_markup or not current_markup.inline_keyboard:
            return
        
        # Создаем новую кнопку закладки
        new_bookmark_button = create_bookmark_button(
            book_id, chapter_start, chapter_end, verse_start, verse_end, is_bookmarked
        )
        
        # Обновляем клавиатуру
        new_buttons = []
        for row in current_markup.inline_keyboard:
            new_row = []
            for button in row:
                if button.callback_data and button.callback_data.startswith("bookmark_"):
                    # Заменяем кнопку закладки
                    new_row.append(new_bookmark_button)
                else:
                    new_row.append(button)
            new_buttons.append(new_row)
        
        from aiogram.types import InlineKeyboardMarkup
        new_markup = InlineKeyboardMarkup(inline_keyboard=new_buttons)
        
        # Обновляем сообщение
        await callback.message.edit_reply_markup(reply_markup=new_markup)
        
    except Exception as e:
        logger.error(f"Ошибка при обновлении кнопки закладки: {e}")


async def check_if_bookmarked(user_id: int, book_id: int, chapter_start: int,
                             chapter_end: int = None, verse_start: int = None, 
                             verse_end: int = None) -> bool:
    """
    Проверяет, добавлена ли ссылка в закладки
    
    Args:
        user_id: ID пользователя
        book_id: ID книги
        chapter_start: Начальная глава
        chapter_end: Конечная глава
        verse_start: Начальный стих
        verse_end: Конечный стих
    
    Returns:
        bool: True если в закладках, False если нет
    """
    try:
        return await db_manager.is_bookmarked(
            user_id, book_id, chapter_start, chapter_end, verse_start, verse_end
        )
    except Exception as e:
        logger.error(f"Ошибка при проверке закладки: {e}")
        return False