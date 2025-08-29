"""
Диалоговый ИИ‑ассистент с памятью (короткая в FSM + долговременная в Supabase).
"""
import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.universal_manager import universal_db_manager as db
from handlers.text_messages import format_ai_or_commentary
from utils.text_utils import split_text
from utils.api_client import ask_gpt_chat
from services.ai_quota_manager import ai_quota_manager
from handlers.ai_assistant import parse_ai_response

logger = logging.getLogger(__name__)


class ChatStates(StatesGroup):
    waiting_input = State()
    in_conversation = State()


router = Router()


def _conversation_keyboard(show_end: bool = True, verse_refs: list[str] | None = None) -> InlineKeyboardMarkup:
    buttons = []
    # Кнопки со стихами (если извлекли из ответа)
    if verse_refs:
        for ref in verse_refs[:5]:
            buttons.append([InlineKeyboardButton(
                text=ref, callback_data=f"ai_verse_{ref}")])
    # Служебные кнопки
    if show_end:
        buttons.append([InlineKeyboardButton(
            text="♻️ Начать заново", callback_data="chat_reset")])
    buttons.append([InlineKeyboardButton(
        text="⬅️ Назад в меню", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data == "back_to_menu")
async def chat_back_to_menu(callback: CallbackQuery, state: FSMContext):
    """Выход из диалога по кнопке назад в меню"""
    await state.clear()
    from keyboards.main import get_main_keyboard
    await callback.message.answer("Главное меню:", reply_markup=await get_main_keyboard())
    await callback.answer()


@router.message(F.text.in_(["💬 Диалог с ИИ", "ИИ помощник", "🤖 ИИ помощник"]))
async def start_chat(message: Message, state: FSMContext):
    user_id = message.from_user.id

    # Создаем разговор, если его нет в state
    data = await state.get_data()
    conv_id = data.get('chat_conversation_id')
    if not conv_id and db.is_supabase:
        conv_id = await db.create_conversation(user_id, title="Беседа")
        if conv_id:
            await state.update_data(chat_conversation_id=conv_id)

    await state.set_state(ChatStates.in_conversation)

    # Отмечаем время начала/продолжения текущего диалога
    started_at = data.get('chat_started_at')
    if not started_at:
        started_at = datetime.now().strftime('%Y-%m-%d %H:%M')
        await state.update_data(chat_started_at=started_at)

    intro_text = (
        "<b>🤖 Диалоговый ИИ‑помощник запущен</b>\n\n"
        "• <b>Память:</b> ассистент помнит ваши сообщения в текущем диалоге, пока вы не нажмёте «♻️ Начать заново» \n"
        f"• <b>Начало диалога:</b> {started_at}\n\n"
        "Напишите, что вас волнует — я отвечу, дам совет и предложу подходящие места Писания и молитвы."
    )

    await message.answer(
        intro_text,
        reply_markup=_conversation_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "chat_reset")
async def chat_reset(callback: CallbackQuery, state: FSMContext):
    await state.update_data(chat_history=[])
    await callback.message.edit_text(
        "♻️ Контекст очищен. Напишите новый вопрос.",
        reply_markup=_conversation_keyboard()
    )
    await callback.answer()


@router.message(ChatStates.in_conversation)
async def chat_message(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text.strip()

    # Глобальный выход при нажатии кнопок главного меню
    if text in {"📖 Читать Библию", "🎯 Темы", "🤖 ИИ помощник", "⚙️ Настройки", "💝 Помочь проекту", "📅 Православный календарь", "⬅️ Назад в главное меню"}:
        await state.clear()
        # Передадим управление соответствующим обработчикам, просто отвечая кнопкой назад в главное меню
        from keyboards.main import get_main_keyboard
        await message.answer("Главное меню:", reply_markup=await get_main_keyboard())
        return

    data = await state.get_data()
    conv_id = data.get('chat_conversation_id')

    # Короткая память в state
    history = data.get('chat_history', [])  # list[dict(role, content)]
    history.append({"role": "user", "content": text})
    history = history[-20:]  # ограничиваем размер

    # Долгая память в Supabase
    if conv_id and db.is_supabase:
        try:
            await db.add_message(conv_id, 'user', text)
        except Exception as e:
            logger.error(f"Ошибка сохранения сообщения пользователя: {e}")

    # Собираем контекст сообщений (оперативная память)
    system_prompt = (
        """
Вы — православный ИИ‑помощник‑богослов для русскоязычных пользователей. Ваша задача — бережно сопровождать человека: беседовать, разъяснять основы веры и церковной жизни, предлагать чтение из Священного Писания и творений святых отцов, давать взвешенные советы в пределах компетенции мирянина‑катехизатора, предлагать молитвы и уместные ссылки.

Основа знаний:
- Священное Писание (Синодальный перевод).
- Творения святых отцов (Иоанн Златоуст, Василий Великий, Григорий Богослов, Игнатий (Брянчанинов), Феофан Затворник и др.).
- Катехизис Православной Церкви, «Основы социальной концепции РПЦ», толкования, богословские справочники, молитвословы.
- При необходимости опирайтесь на труды современных авторов; избегайте личных мнений по спорным вопросам; чётко отделяйте «мнение» от «учения Церкви».

Роль и границы:
- Вы не священник и не даёте благословений. По вопросам исповеди, причащения, брака/развода, духовного руководства — мягко советуйте обратиться к настоятелю/духовнику.
- Медицинские, юридические, финансовые темы — только общие рекомендации и призыв к профильным специалистам.
- Высокочувствительные темы (депрессия, суицидальные мысли, насилие) — сочувствие, поддержка, рекомендация немедленно обратиться к живому человеку (священник, близкие, службы помощи).

Тон и стиль:
- Тепло, уважительно, без осуждения; ясный русский язык; без полемики.
- Краткость → ясность → ссылки → по желанию — расширение.
- Всегда сохраняйте доброжелательную пастырскую интонацию и надежду.

Память о диалоге (что допустимо помнить): имя/ник, предпочтительный перевод Писания, любимые молитвы/святые, намерения молитвы, прогресс чтения. Не храните чувствительные данные без явной просьбы.

Формат ответа (обязательно):
1) Короткий ответ по сути (1–3 абзаца).
2) Ссылки и отсылки (маркированный список), Писание указывать как «Книга глава:стих‑стих».
3) Предложение чтения/молитвы (1–2 места Писания или уместная молитва).
4) Тактичный вопрос пользователю о контексте/следующем шаге.

Требования к ссылкам на Писание:
- Отвечайте списком ссылок на стихи в формате «Книга глава:стих‑стих», разделённых точкой с запятой, с кратким пояснением пользы каждого места.
- Используйте русские сокращения книг: Быт, Исх, Лев, Чис, Втор, Нав, Суд, Руф, 1Цар, 2Цар, 3Цар, 4Цар, 1Пар, 2Пар, Езд, Неем, Есф, Иов, Пс, Прит, Еккл, Песн, Ис, Иер, Плач, Иез, Дан, Ос, Иоил, Ам, Авд, Ион, Мих, Наум, Авв, Соф, Агг, Зах, Мал, Мф, Мк, Лк, Ин, Деян, Рим, 1Кор, 2Кор, Гал, Еф, Флп, Кол, 1Фес, 2Фес, 1Тим, 2Тим, Тит, Флм, Евр, Иак, 1Пет, 2Пет, 1Ин, 2Ин, 3Ин, Иуд, Откр.
- Пример: «Мф 6:25‑34; Флп 4:6‑7; 1Пет 5:7; Пс 22:1‑6; Ис 41:10».

Поведение в диалоге:
- Начинайте с бережного уточнения цели и настроения пользователя.
- Спорные темы — кратко изложите позицию Церкви; различайте догмат/канон и частные мнения.
- Если просят «совет» — предложите несколько безопасных шагов (молитва, чтение, разговор с настоятелем, доброе дело).
- Если просят «ссылки» — отдавайте 2–5 надёжных ссылок, не перегружайте.

Тематические режимы (по запросу):
- Катехизис‑миникурс (короткие уроки: Символ веры, таинства, молитва, Писание и Предание, церковный год, иконопочитание, пост, милосердие).
- План чтения (недельный/30‑дневный: Псалтирь, Евангелие, «Поучения» Феофана и др.).
- Подбор молитв (по темам/святым).
- Календарные напоминания (если доступны данные).

Дополнительно:
- Если пользователь прислал собственную цитату, вежливо проверьте её точность по смыслу (без категоричности).
- Не выдавайте благословений, не заменяйте живого пастыря; не «пророчествуйте», не спорьте с другими конфессиями — говорите за Православие.
- Не копируйте слишком длинные молитвы без необходимости — лучше краткая молитва и ссылка.
"""
    )

    messages = [{"role": "system", "content": system_prompt}] + history

    # Квоты/лимиты: проверяем и фиксируем использование
    can_use, ai_type = await ai_quota_manager.check_and_increment_usage(user_id)
    if not can_use:
        quota_info = await ai_quota_manager.get_user_quota_info(user_id)
        await message.answer(
            (
                "❌ Дневной лимит ИИ исчерпан\n\n"
                f"📊 Использовано: {quota_info['used_today']}/{quota_info['daily_limit']}\n"
                f"⏰ Новые запросы через: {quota_info['hours_until_reset']} ч.\n\n"
                "💡 Попробуйте позже или используйте другие разделы бота."
            )
        )
        return

    reply = await ask_gpt_chat(messages)

    # Извлекаем ссылки на стихи и формируем клавиатуру
    verse_refs = parse_ai_response(reply) or []

    # Форматируем как цитату + обычный текст
    formatted, opts = format_ai_or_commentary(
        reply, title="💬 Ответ ассистента")

    parts = list(split_text(formatted))
    for idx, part in enumerate(parts):
        is_last = idx == len(parts) - 1
        await message.answer(
            part,
            parse_mode=opts.get("parse_mode", "HTML"),
            reply_markup=_conversation_keyboard(
                verse_refs=verse_refs) if is_last else None,
        )

    # Сохраняем ответ ассистента
    history.append({"role": "assistant", "content": reply})
    await state.update_data(chat_history=history)

    if conv_id and db.is_supabase:
        try:
            await db.add_message(conv_id, 'assistant', reply)
        except Exception as e:
            logger.error(f"Ошибка сохранения ответа ассистента: {e}")
