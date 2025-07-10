"""
Обработчики для планов чтения Библии.
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from keyboards.main import (
    create_reading_plans_keyboard,
    create_plan_overview_keyboard,
    create_plan_day_keyboard,
    create_user_plans_keyboard,
    create_reading_navigation_keyboard,
    get_main_keyboard
)
from services.reading_plans import reading_plans_service
from database.db_manager import db_manager
from utils.api_client import bible_api
from utils.bible_data import bible_data
from middleware.state import get_current_translation

logger = logging.getLogger(__name__)

# Создаем роутер для планов чтения
router = Router()


@router.message(F.text == "📅 План чтения")
async def show_reading_plans(message: Message, state: FSMContext):
    """Показывает список доступных планов чтения"""
    try:
        await message.answer(
            "📅 <b>Планы чтения Библии</b>\n\n"
            "Выберите план чтения или посмотрите свои активные планы:",
            reply_markup=create_reading_plans_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка при показе планов чтения: {e}")
        await message.answer("Произошла ошибка при загрузке планов чтения.")


@router.callback_query(F.data == "reading_plans")
async def callback_reading_plans(callback: CallbackQuery, state: FSMContext):
    """Callback для показа планов чтения"""
    try:
        await callback.message.edit_text(
            "📅 <b>Планы чтения Библии</b>\n\n"
            "Выберите план чтения или посмотрите свои активные планы:",
            reply_markup=create_reading_plans_keyboard()
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка в callback планов чтения: {e}")
        await callback.answer("Произошла ошибка при загрузке планов чтения.")


@router.callback_query(F.data.startswith("select_plan_"))
async def select_reading_plan(callback: CallbackQuery, state: FSMContext):
    """Выбор плана чтения"""
    try:
        plan_id = callback.data.replace("select_plan_", "")
        user_id = callback.from_user.id

        # Получаем информацию о плане
        plan = reading_plans_service.get_plan(plan_id)
        if not plan:
            await callback.answer("План не найден.")
            return

        # Проверяем, есть ли уже этот план у пользователя
        existing_plan = await db_manager.get_user_reading_plan(user_id, plan_id)

        if existing_plan:
            # План уже есть, показываем его
            current_day = existing_plan['current_day']
            await callback.message.edit_text(
                f"📋 <b>{plan.title}</b>\n\n"
                f"📊 Прогресс: день {current_day} из {plan.total_days}\n"
                f"📅 Всего дней: {plan.total_days}\n\n"
                "Этот план уже добавлен в ваши активные планы.",
                reply_markup=create_plan_overview_keyboard(
                    plan_id, current_day)
            )
        else:
            # Добавляем новый план
            await db_manager.set_user_reading_plan(user_id, plan_id, 1)

            await callback.message.edit_text(
                f"✅ <b>План добавлен!</b>\n\n"
                f"📋 {plan.title}\n"
                f"📅 Всего дней: {plan.total_days}\n\n"
                "Вы можете начать чтение с первого дня.",
                reply_markup=create_plan_overview_keyboard(plan_id, 1)
            )

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при выборе плана чтения: {e}")
        await callback.answer("Произошла ошибка при добавлении плана.")


@router.callback_query(F.data == "my_reading_plans")
async def show_user_plans(callback: CallbackQuery, state: FSMContext):
    """Показывает активные планы пользователя"""
    try:
        user_id = callback.from_user.id
        user_plans = await db_manager.get_user_reading_plans(user_id)

        if user_plans:
            text = f"📋 <b>Ваши активные планы ({len(user_plans)})</b>\n\n"
            text += "Выберите план для продолжения чтения:"
        else:
            text = "📋 <b>Ваши активные планы</b>\n\nУ вас пока нет активных планов чтения."

        await callback.message.edit_text(
            text,
            reply_markup=create_user_plans_keyboard(user_plans)
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при показе планов пользователя: {e}")
        await callback.answer("Произошла ошибка при загрузке ваших планов.")


@router.callback_query(F.data.startswith("view_plan_"))
async def view_plan(callback: CallbackQuery, state: FSMContext):
    """Просмотр конкретного плана"""
    try:
        plan_id = callback.data.replace("view_plan_", "")
        user_id = callback.from_user.id

        # Получаем информацию о плане
        plan = reading_plans_service.get_plan(plan_id)
        user_plan = await db_manager.get_user_reading_plan(user_id, plan_id)

        if not plan or not user_plan:
            await callback.answer("План не найден.")
            return

        current_day = user_plan['current_day']

        # Получаем прогресс
        completed_days = await db_manager.get_reading_progress_async(user_id, plan_id)
        progress_percent = round(
            (len(completed_days) / plan.total_days) * 100, 1)

        text = (
            f"📋 <b>{plan.title}</b>\n\n"
            f"📊 Прогресс: {len(completed_days)}/{plan.total_days} дней ({progress_percent}%)\n"
            f"📅 Текущий день: {current_day}\n"
            f"📖 Всего дней: {plan.total_days}\n\n"
        )

        if completed_days:
            text += f"✅ Прочитано дней: {len(completed_days)}\n"

        await callback.message.edit_text(
            text,
            reply_markup=create_plan_overview_keyboard(plan_id, current_day)
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при просмотре плана: {e}")
        await callback.answer("Произошла ошибка при загрузке плана.")


@router.callback_query(F.data.startswith("plan_day_"))
async def show_plan_day(callback: CallbackQuery, state: FSMContext):
    """Показывает чтение для конкретного дня плана"""
    try:
        # Парсим callback_data: plan_day_{plan_id}_{day}
        # plan_id может содержать подчеркивания, поэтому берем все кроме последней части как plan_id
        parts = callback.data.split("_")
        day = int(parts[-1])  # Последняя часть - всегда день
        # Все между "plan_day" и днем - это plan_id
        plan_id = "_".join(parts[2:-1])
        user_id = callback.from_user.id

        # Получаем информацию о плане и дне
        plan = reading_plans_service.get_plan(plan_id)
        if not plan:
            await callback.answer("План не найден.")
            return

        reading = reading_plans_service.get_plan_day(plan_id, day)
        if not reading:
            await callback.answer("День не найден.")
            return

        # Проверяем, прочитан ли день
        is_completed = await db_manager.is_reading_day_completed_async(user_id, plan_id, day)

        # Проверяем навигацию
        has_previous = reading_plans_service.get_previous_day(
            plan_id, day) is not None
        has_next = reading_plans_service.get_next_day(plan_id, day) is not None

        # Парсим ссылки для чтения
        references = reading_plans_service.parse_reading_references(reading)

        # Формируем текст
        status_icon = "✅" if is_completed else "📖"
        text = (
            f"{status_icon} <b>День {day}</b> - {plan.title}\n\n"
            f"📖 <b>Чтение на сегодня ({len(references)} отрывков):</b>\n"
        )

        # Добавляем ссылки как текст
        for i, ref in enumerate(references, 1):
            text += f"{i}. {ref}\n"

        if is_completed:
            text += f"\n✅ <i>Отмечено как прочитанное</i>"

        text += f"\n💡 <i>Нажмите на отрывок ниже для чтения</i>"

        # Обновляем текущий день пользователя
        await db_manager.update_reading_plan_day(user_id, plan_id, day)

        await callback.message.edit_text(
            text,
            reply_markup=create_plan_day_keyboard(
                plan_id, day, is_completed, has_previous, has_next, references
            )
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при показе дня плана: {e}")
        await callback.answer("Произошла ошибка при загрузке дня.")


@router.callback_query(F.data.startswith("mark_day_"))
async def mark_day_completed(callback: CallbackQuery, state: FSMContext):
    """Отмечает день как прочитанный"""
    try:
        parts = callback.data.split("_")
        day = int(parts[-1])  # Последняя часть - всегда день
        # Все между "mark_day" и днем - это plan_id
        plan_id = "_".join(parts[2:-1])
        user_id = callback.from_user.id

        # Отмечаем день как прочитанный
        await db_manager.mark_reading_day_completed_async(user_id, plan_id, day)

        # Обновляем сообщение
        await show_plan_day(callback, state)

    except Exception as e:
        logger.error(f"Ошибка при отметке дня: {e}")
        await callback.answer("Произошла ошибка при отметке дня.")


@router.callback_query(F.data.startswith("unmark_day_"))
async def unmark_day_completed(callback: CallbackQuery, state: FSMContext):
    """Снимает отметку с дня"""
    try:
        parts = callback.data.split("_")
        day = int(parts[-1])  # Последняя часть - всегда день
        # Все между "unmark_day" и днем - это plan_id
        plan_id = "_".join(parts[2:-1])
        user_id = callback.from_user.id

        # Удаляем отметку (устанавливаем completed = 0)
        def _execute():
            import sqlite3
            conn = sqlite3.connect(db_manager.db_file)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE reading_progress 
                SET completed = 0 
                WHERE user_id=? AND plan_id=? AND day=?
            ''', (user_id, plan_id, day))
            conn.commit()
            conn.close()

        import asyncio
        await asyncio.to_thread(_execute)

        # Обновляем сообщение
        await show_plan_day(callback, state)

    except Exception as e:
        logger.error(f"Ошибка при снятии отметки дня: {e}")
        await callback.answer("Произошла ошибка при снятии отметки.")


@router.callback_query(F.data.startswith("clear_progress_"))
async def clear_plan_progress(callback: CallbackQuery, state: FSMContext):
    """Очищает прогресс по плану"""
    try:
        plan_id = callback.data.replace("clear_progress_", "")
        user_id = callback.from_user.id

        # Получаем название плана для подтверждения
        plan = reading_plans_service.get_plan(plan_id)
        if not plan:
            await callback.answer("План не найден.")
            return

        # Очищаем прогресс (удаляем все отметки о прочитанных днях)
        def _execute():
            import sqlite3
            conn = sqlite3.connect(db_manager.db_file)
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM reading_progress 
                WHERE user_id=? AND plan_id=?
            ''', (user_id, plan_id))
            conn.commit()
            conn.close()

        import asyncio
        await asyncio.to_thread(_execute)

        # Сбрасываем текущий день на 1
        await db_manager.update_reading_plan_day(user_id, plan_id, 1)

        await callback.message.edit_text(
            f"🗑️ <b>Прогресс очищен</b>\n\n"
            f"Весь прогресс по плану \"{plan.title}\" был очищен.\n"
            f"Вы можете начать чтение заново с первого дня.",
            reply_markup=create_plan_overview_keyboard(plan_id, 1)
        )
        await callback.answer("Прогресс очищен.")

    except Exception as e:
        logger.error(f"Ошибка при очистке прогресса: {e}")
        await callback.answer("Произошла ошибка при очистке прогресса.")


@router.callback_query(F.data.startswith("plan_progress_"))
async def show_plan_progress(callback: CallbackQuery, state: FSMContext):
    """Показывает прогресс по плану"""
    try:
        plan_id = callback.data.replace("plan_progress_", "")
        user_id = callback.from_user.id

        # Получаем информацию о плане
        plan = reading_plans_service.get_plan(plan_id)
        if not plan:
            await callback.answer("План не найден.")
            return

        # Получаем прогресс
        completed_days = await db_manager.get_reading_progress_async(user_id, plan_id)
        progress_percent = round(
            (len(completed_days) / plan.total_days) * 100, 1)

        # Формируем текст прогресса
        text = (
            f"📊 <b>Прогресс по плану</b>\n"
            f"📋 {plan.title}\n\n"
            f"✅ Прочитано: {len(completed_days)} из {plan.total_days} дней\n"
            f"📈 Прогресс: {progress_percent}%\n\n"
        )

        if completed_days:
            # Показываем последние прочитанные дни
            recent_days = sorted(completed_days, reverse=True)[:10]
            text += "📖 <b>Последние прочитанные дни:</b>\n"
            for day in recent_days:
                text += f"• День {day}\n"

            if len(completed_days) > 10:
                text += f"... и еще {len(completed_days) - 10} дней\n"
        else:
            text += "Пока не прочитано ни одного дня."

        # Получаем текущий день
        user_plan = await db_manager.get_user_reading_plan(user_id, plan_id)
        current_day = user_plan['current_day'] if user_plan else 1

        await callback.message.edit_text(
            text,
            reply_markup=create_plan_overview_keyboard(plan_id, current_day)
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при показе прогресса: {e}")
        await callback.answer("Произошла ошибка при загрузке прогресса.")


# Обработчики для чтения отдельных ссылок из плана
@router.callback_query(F.data.startswith("plan_select_day_"))
async def select_plan_day(callback: CallbackQuery, state: FSMContext):
    """Показывает интерфейс для выбора дня плана"""
    try:
        plan_id = callback.data.replace("plan_select_day_", "")
        user_id = callback.from_user.id

        # Получаем информацию о плане
        plan = reading_plans_service.get_plan(plan_id)
        if not plan:
            await callback.answer("План не найден.")
            return

        # Получаем текущий день пользователя
        user_plan = await db_manager.get_user_reading_plan(user_id, plan_id)
        current_day = user_plan['current_day'] if user_plan else 1

        # Получаем прогресс
        completed_days = await db_manager.get_reading_progress_async(user_id, plan_id)

        # Формируем текст с выбором дня
        text = (
            f"📅 <b>Выбор дня плана</b>\n"
            f"📋 {plan.title}\n\n"
            f"📖 Текущий день: {current_day}\n"
            f"📊 Всего дней: {plan.total_days}\n"
            f"✅ Прочитано: {len(completed_days)} дней\n\n"
            "Введите номер дня (от 1 до {}) для перехода:".format(
                plan.total_days)
        )

        # Сохраняем план в состоянии для последующего использования
        await state.update_data(selecting_day_for_plan=plan_id)

        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data=f"view_plan_{plan_id}"
                )]
            ])
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при выборе дня плана: {e}")
        await callback.answer("Произошла ошибка при выборе дня.")


@router.message(F.text.regexp(r'^\d+$'))
async def handle_day_selection(message: Message, state: FSMContext):
    """Обрабатывает ввод номера дня для плана"""
    try:
        data = await state.get_data()
        plan_id = data.get('selecting_day_for_plan')

        if not plan_id:
            return  # Не обрабатываем, если не в режиме выбора дня

        day = int(message.text)
        user_id = message.from_user.id

        # Получаем информацию о плане
        plan = reading_plans_service.get_plan(plan_id)
        if not plan:
            await message.answer("План не найден.")
            return

        # Проверяем корректность дня
        if day < 1 or day > plan.total_days:
            await message.answer(
                f"❌ Некорректный день. Введите число от 1 до {plan.total_days}."
            )
            return

        # Очищаем состояние
        await state.update_data(selecting_day_for_plan=None)

        # Обновляем текущий день пользователя
        await db_manager.update_reading_plan_day(user_id, plan_id, day)

        # Показываем выбранный день
        reading = reading_plans_service.get_plan_day(plan_id, day)
        if not reading:
            await message.answer("День не найден.")
            return

        # Проверяем, прочитан ли день
        is_completed = await db_manager.is_reading_day_completed_async(user_id, plan_id, day)

        # Проверяем навигацию
        has_previous = reading_plans_service.get_previous_day(
            plan_id, day) is not None
        has_next = reading_plans_service.get_next_day(plan_id, day) is not None

        # Парсим ссылки для чтения
        references = reading_plans_service.parse_reading_references(reading)

        # Формируем текст
        status_icon = "✅" if is_completed else "📖"
        text = (
            f"{status_icon} <b>День {day}</b> - {plan.title}\n\n"
            f"📖 <b>Чтение на сегодня ({len(references)} отрывков):</b>\n"
        )

        # Добавляем ссылки как текст
        for i, ref in enumerate(references, 1):
            text += f"{i}. {ref}\n"

        if is_completed:
            text += f"\n✅ <i>Отмечено как прочитанное</i>"

        text += f"\n💡 <i>Нажмите на отрывок ниже для чтения</i>"

        await message.answer(
            text,
            reply_markup=create_plan_day_keyboard(
                plan_id, day, is_completed, has_previous, has_next, references
            )
        )

    except ValueError:
        # Не число - игнорируем
        pass
    except Exception as e:
        logger.error(f"Ошибка при обработке выбора дня: {e}")
        await message.answer("Произошла ошибка при выборе дня.")


@router.callback_query(F.data.startswith("reading_ref_"))
async def show_reading_reference(callback: CallbackQuery, state: FSMContext):
    """Показывает конкретную ссылку из дня плана"""
    try:
        # Парсим callback_data: reading_ref_{plan_id}_{day}_{ref_index}
        parts = callback.data.split("_")
        ref_index = int(parts[-1])  # Последняя часть - индекс ссылки
        day = int(parts[-2])  # Предпоследняя часть - день
        # Все между "reading_ref" и последними двумя частями
        plan_id = "_".join(parts[2:-2])

        # Получаем чтение дня
        reading = reading_plans_service.get_plan_day(plan_id, day)
        if not reading:
            await callback.answer("Чтение не найдено.")
            return

        # Парсим ссылки
        references = reading_plans_service.parse_reading_references(reading)
        if ref_index >= len(references):
            await callback.answer("Ссылка не найдена.")
            return

        current_ref = references[ref_index]
        translation = await get_current_translation(state)

        # Получаем текст из API
        try:
            text = await bible_api.get_verse_by_reference(current_ref, translation)
            if not text:
                text = f"Не удалось найти текст для: {current_ref}"
        except Exception as e:
            logger.error(f"Ошибка при получении текста: {e}")
            text = f"Ошибка при загрузке: {current_ref}"

        # Проверяем, добавлена ли в закладки
        user_id = callback.from_user.id
        try:
            from utils.reference_parser import parse_reference
            parsed_ref = parse_reference(current_ref)
            is_bookmarked = False

            if parsed_ref:
                book_name = parsed_ref['book']
                chapter = parsed_ref['chapter']
                verse_start = parsed_ref.get('verse_start', 1)
                verse_end = parsed_ref.get('verse_end', verse_start)
                book_id = bible_data.get_book_id(book_name)

                if book_id:
                    is_bookmarked = await db_manager.is_bookmark_exists_detailed(
                        user_id, book_id, chapter, verse_start, verse_end
                    )
        except Exception as e:
            logger.error(f"Ошибка при проверке закладки: {e}")
            is_bookmarked = False

        # Формируем сообщение
        message_text = (
            f"📖 <b>День {day}</b> - Чтение {ref_index + 1}/{len(references)}\n"
            f"📝 <b>{current_ref}</b>\n\n"
            f"{text}"
        )

        await callback.message.edit_text(
            message_text,
            reply_markup=create_reading_navigation_keyboard(
                references, ref_index, plan_id, day, is_bookmarked
            )
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при показе ссылки: {e}")
        await callback.answer("Произошла ошибка при загрузке чтения.")


@router.callback_query(F.data.startswith("lopukhin_reading_"))
async def show_lopukhin_commentary_reading(callback: CallbackQuery, state: FSMContext):
    """Показывает толкование Лопухина для отрывка из плана"""
    try:
        # Парсим callback_data: lopukhin_reading_{plan_id}_{day}_{ref_index}
        parts = callback.data.split("_")
        ref_index = int(parts[-1])
        day = int(parts[-2])
        plan_id = "_".join(parts[2:-2])

        # Получаем чтение дня
        reading = reading_plans_service.get_plan_day(plan_id, day)
        if not reading:
            await callback.answer("Чтение не найдено.")
            return

        # Парсим ссылки
        references = reading_plans_service.parse_reading_references(reading)
        if ref_index >= len(references):
            await callback.answer("Ссылка не найдена.")
            return

        current_ref = references[ref_index]

        # Показываем индикатор загрузки
        await callback.answer("🔄 Загружаю толкование...")

        # Получаем толкование Лопухина через существующий API
        try:
            # Парсим ссылку для получения книги и главы
            from utils.reference_parser import parse_reference
            parsed_ref = parse_reference(current_ref)

            if parsed_ref:
                book_name = parsed_ref['book']
                chapter = parsed_ref['chapter']

                # Получаем толкование через API
                commentary = await bible_api.get_lopukhin_commentary(book_name, chapter)

                if commentary:
                    commentary_text = (
                        f"📝 <b>Толкование Лопухина</b>\n\n"
                        f"📖 <b>{current_ref}</b>\n\n"
                        f"{commentary}"
                    )
                else:
                    commentary_text = (
                        f"📝 <b>Толкование Лопухина</b>\n\n"
                        f"📖 <b>{current_ref}</b>\n\n"
                        "Толкование для данного отрывка не найдено."
                    )
            else:
                commentary_text = (
                    f"📝 <b>Толкование Лопухина</b>\n\n"
                    f"📖 <b>{current_ref}</b>\n\n"
                    "Не удалось распознать ссылку для получения толкования."
                )
        except Exception as e:
            logger.error(f"Ошибка при получении толкования Лопухина: {e}")
            commentary_text = (
                f"📝 <b>Толкование Лопухина</b>\n\n"
                f"📖 <b>{current_ref}</b>\n\n"
                "Произошла ошибка при загрузке толкования."
            )

        # Проверяем, добавлена ли в закладки
        user_id = callback.from_user.id
        is_bookmarked = await db_manager.is_bookmark_exists(user_id, current_ref)

        await callback.message.edit_text(
            commentary_text,
            reply_markup=create_reading_navigation_keyboard(
                references, ref_index, plan_id, day, is_bookmarked
            )
        )

    except Exception as e:
        logger.error(f"Ошибка при показе толкования: {e}")
        await callback.answer("Произошла ошибка при загрузке толкования.")


@router.callback_query(F.data.startswith("ai_reading_"))
async def show_ai_analysis_reading(callback: CallbackQuery, state: FSMContext):
    """Показывает ИИ-разбор для отрывка из плана"""
    try:
        # Парсим callback_data: ai_reading_{plan_id}_{day}_{ref_index}
        parts = callback.data.split("_")
        ref_index = int(parts[-1])
        day = int(parts[-2])
        plan_id = "_".join(parts[2:-2])

        # Получаем чтение дня
        reading = reading_plans_service.get_plan_day(plan_id, day)
        if not reading:
            await callback.answer("Чтение не найдено.")
            return

        # Парсим ссылки
        references = reading_plans_service.parse_reading_references(reading)
        if ref_index >= len(references):
            await callback.answer("Ссылка не найдена.")
            return

        current_ref = references[ref_index]

        # Показываем индикатор загрузки
        await callback.answer("🤖 Генерирую ИИ-анализ...")

        # Получаем ИИ-анализ через существующий сервис
        try:
            # Сначала получаем текст отрывка
            translation = await get_current_translation(state)
            verse_text = await bible_api.get_verse_by_reference(current_ref, translation)

            if verse_text:
                # Получаем ИИ-анализ через существующий сервис
                from services.ai_service import ai_service
                analysis = await ai_service.analyze_verse(verse_text, current_ref)

                if analysis:
                    ai_text = (
                        f"🤖 <b>ИИ-разбор</b>\n\n"
                        f"📖 <b>{current_ref}</b>\n\n"
                        f"{analysis}"
                    )
                else:
                    ai_text = (
                        f"🤖 <b>ИИ-разбор</b>\n\n"
                        f"📖 <b>{current_ref}</b>\n\n"
                        "Не удалось сгенерировать ИИ-анализ для данного отрывка."
                    )
            else:
                ai_text = (
                    f"🤖 <b>ИИ-разбор</b>\n\n"
                    f"📖 <b>{current_ref}</b>\n\n"
                    "Не удалось получить текст отрывка для анализа."
                )
        except Exception as e:
            logger.error(f"Ошибка при получении ИИ-анализа: {e}")
            ai_text = (
                f"🤖 <b>ИИ-разбор</b>\n\n"
                f"📖 <b>{current_ref}</b>\n\n"
                "Произошла ошибка при генерации ИИ-анализа."
            )

        # Проверяем, добавлена ли в закладки
        user_id = callback.from_user.id
        is_bookmarked = await db_manager.is_bookmark_exists(user_id, current_ref)

        await callback.message.edit_text(
            ai_text,
            reply_markup=create_reading_navigation_keyboard(
                references, ref_index, plan_id, day, is_bookmarked
            )
        )

    except Exception as e:
        logger.error(f"Ошибка при показе ИИ-анализа: {e}")
        await callback.answer("Произошла ошибка при загрузке ИИ-анализа.")


@router.callback_query(F.data.startswith("add_bookmark_reading_"))
async def add_bookmark_reading(callback: CallbackQuery, state: FSMContext):
    """Добавляет отрывок из плана в закладки"""
    try:
        # Парсим callback_data: add_bookmark_reading_{plan_id}_{day}_{ref_index}
        parts = callback.data.split("_")
        ref_index = int(parts[-1])
        day = int(parts[-2])
        plan_id = "_".join(parts[3:-2])

        # Получаем чтение дня
        reading = reading_plans_service.get_plan_day(plan_id, day)
        if not reading:
            await callback.answer("Чтение не найдено.")
            return

        # Парсим ссылки
        references = reading_plans_service.parse_reading_references(reading)
        if ref_index >= len(references):
            await callback.answer("Ссылка не найдена.")
            return

        current_ref = references[ref_index]
        user_id = callback.from_user.id

        # Добавляем в закладки через существующий сервис
        try:
            # Парсим ссылку для получения данных
            from utils.reference_parser import parse_reference
            parsed_ref = parse_reference(current_ref)

            if parsed_ref:
                book_name = parsed_ref['book']
                chapter = parsed_ref['chapter']
                verse_start = parsed_ref.get('verse_start', 1)
                verse_end = parsed_ref.get('verse_end', verse_start)

                # Получаем book_id из bible_data
                book_id = bible_data.get_book_id(book_name)

                if book_id:
                    # Добавляем закладку
                    await db_manager.add_bookmark_detailed(
                        user_id=user_id,
                        book_id=book_id,
                        chapter=chapter,
                        verse_start=verse_start,
                        verse_end=verse_end,
                        note=f"Из плана чтения: {plan_id}, день {day}"
                    )
                    await callback.answer("📌 Закладка добавлена!")
                    is_bookmarked = True
                else:
                    await callback.answer("❌ Не удалось найти книгу для добавления закладки.")
                    is_bookmarked = False
            else:
                await callback.answer("❌ Не удалось распознать ссылку для закладки.")
                is_bookmarked = False

        except Exception as e:
            logger.error(f"Ошибка при добавлении закладки: {e}")
            await callback.answer("❌ Произошла ошибка при добавлении закладки.")
            is_bookmarked = False

        # Обновляем клавиатуру
        await callback.message.edit_reply_markup(
            reply_markup=create_reading_navigation_keyboard(
                references, ref_index, plan_id, day, is_bookmarked
            )
        )

    except Exception as e:
        logger.error(f"Ошибка при добавлении закладки: {e}")
        await callback.answer("Произошла ошибка при добавлении закладки.")


@router.callback_query(F.data.startswith("remove_bookmark_reading_"))
async def remove_bookmark_reading(callback: CallbackQuery, state: FSMContext):
    """Удаляет отрывок из плана из закладок"""
    try:
        # Парсим callback_data: remove_bookmark_reading_{plan_id}_{day}_{ref_index}
        parts = callback.data.split("_")
        ref_index = int(parts[-1])
        day = int(parts[-2])
        plan_id = "_".join(parts[3:-2])

        # Получаем чтение дня
        reading = reading_plans_service.get_plan_day(plan_id, day)
        if not reading:
            await callback.answer("Чтение не найдено.")
            return

        # Парсим ссылки
        references = reading_plans_service.parse_reading_references(reading)
        if ref_index >= len(references):
            await callback.answer("Ссылка не найдена.")
            return

        current_ref = references[ref_index]
        user_id = callback.from_user.id

        # Удаляем из закладок через существующий сервис
        try:
            # Парсим ссылку для получения данных
            from utils.reference_parser import parse_reference
            parsed_ref = parse_reference(current_ref)

            if parsed_ref:
                book_name = parsed_ref['book']
                chapter = parsed_ref['chapter']
                verse_start = parsed_ref.get('verse_start', 1)
                verse_end = parsed_ref.get('verse_end', verse_start)

                # Получаем book_id из bible_data
                book_id = bible_data.get_book_id(book_name)

                if book_id:
                    # Удаляем закладку
                    await db_manager.remove_bookmark_detailed(
                        user_id=user_id,
                        book_id=book_id,
                        chapter=chapter,
                        verse_start=verse_start,
                        verse_end=verse_end
                    )
                    await callback.answer("🗑️ Закладка удалена!")
                    is_bookmarked = False
                else:
                    await callback.answer("❌ Не удалось найти книгу для удаления закладки.")
                    is_bookmarked = True
            else:
                await callback.answer("❌ Не удалось распознать ссылку для удаления закладки.")
                is_bookmarked = True

        except Exception as e:
            logger.error(f"Ошибка при удалении закладки: {e}")
            await callback.answer("❌ Произошла ошибка при удалении закладки.")
            is_bookmarked = True

        # Обновляем клавиатуру
        await callback.message.edit_reply_markup(
            reply_markup=create_reading_navigation_keyboard(
                references, ref_index, plan_id, day, is_bookmarked
            )
        )

    except Exception as e:
        logger.error(f"Ошибка при удалении закладки: {e}")
        await callback.answer("Произошла ошибка при удалении закладки.")
