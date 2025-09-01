from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

from database.universal_manager import universal_db_manager as db
from services.ai_quota_manager import ai_quota_manager
from utils.api_client import ask_gpt_chat
from handlers.ai_assistant import parse_ai_response


router = APIRouter(prefix="/api/v1/ai/chat", tags=["ai-chat"])
# Совместимость с простыми путями: /api/conversations*
router_compat = APIRouter(prefix="/api", tags=["ai-chat"])


def _system_prompt() -> str:
    return (
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
    ).strip()


class StartRequest(BaseModel):
    user_id: int
    title: Optional[str] = None


class StartResponse(BaseModel):
    conversation_id: str
    limits: dict


@router.post("/start", response_model=StartResponse)
async def start_chat(req: StartRequest):
    conv_id = await db.create_conversation(req.user_id, title=req.title or "Беседа")
    info = await ai_quota_manager.get_user_quota_info(req.user_id)
    return StartResponse(conversation_id=conv_id, limits=info)


class ChatMessageRequest(BaseModel):
    user_id: int
    conversation_id: str
    message: str


class ChatMessageResponse(BaseModel):
    text: str
    verse_refs: List[str]
    model: str


@router.post("/message", response_model=ChatMessageResponse)
async def chat_message(req: ChatMessageRequest):
    # квоты
    can_use, ai_type = await ai_quota_manager.check_and_increment_usage(req.user_id)
    if not can_use:
        info = await ai_quota_manager.get_user_quota_info(req.user_id)
        raise Exception(
            f"AI limit exceeded: used={info['used_today']}/{info['daily_limit']}"
        )

    # сохранить пользовательское сообщение
    await db.add_message(req.conversation_id, 'user', req.message)

    # собрать контекст последних сообщений
    history = await db.list_messages(req.conversation_id, limit=20)
    messages = [{"role": "system", "content": _system_prompt()}]
    for m in history:
        messages.append({"role": m.get('role', 'user'),
                        "content": m.get('content', '')})

    # запрос к модели
    reply = await ask_gpt_chat(messages)

    # сохранить ответ ассистента
    await db.add_message(req.conversation_id, 'assistant', reply)

    # извлечь ссылки
    refs = parse_ai_response(reply) or []
    return ChatMessageResponse(text=reply, verse_refs=refs, model=ai_type or "regular")


@router.get("/history")
async def chat_history(conversation_id: str, limit: int = 20):
    items = await db.list_messages(conversation_id, limit=limit)
    return {"conversation_id": conversation_id, "messages": items}


# ===== Совместимые эндпоинты =====
@router_compat.post("/conversations")
async def compat_create_conversation(req: StartRequest):
    conv = await start_chat(req)
    return conv


@router_compat.get("/conversations/{conversation_id}")
async def compat_get_conversation(conversation_id: str, limit: int = 20):
    return await chat_history(conversation_id, limit)


class CompatMessage(BaseModel):
    user_id: int
    message: str


@router_compat.post("/conversations/{conversation_id}/messages")
async def compat_post_message(conversation_id: str, payload: CompatMessage):
    resp = await chat_message(ChatMessageRequest(
        user_id=payload.user_id,
        conversation_id=conversation_id,
        message=payload.message,
    ))
    return resp


class ResetRequest(BaseModel):
    user_id: int
    conversation_id: str


@router.post("/reset")
async def reset_chat(req: ResetRequest):
    try:
        await db.delete_conversation(req.conversation_id, req.user_id)
    except Exception:
        pass
    # создаём новую беседу
    conv_id = await db.create_conversation(req.user_id, title="Беседа")
    info = await ai_quota_manager.get_user_quota_info(req.user_id)
    return {"conversation_id": conv_id, "limits": info}


@router_compat.post("/conversations/{conversation_id}/reset")
async def compat_reset_conversation(conversation_id: str, user_id: int):
    return await reset_chat(ResetRequest(user_id=user_id, conversation_id=conversation_id))
