from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from utils.api_client import ask_gpt_bible_verses
from handlers.ai_assistant import parse_ai_response
from services.ai_quota_manager import ai_quota_manager

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])


class SuggestRequest(BaseModel):
    user_id: int
    problem_text: str


class SuggestResponse(BaseModel):
    text: str
    verse_refs: List[str]
    model: str


@router.post("/suggest-verses", response_model=SuggestResponse)
async def suggest_verses(req: SuggestRequest):
    can_use, ai_type = await ai_quota_manager.check_and_increment_usage(req.user_id)
    if not can_use:
        # Не даём доступ при исчерпании квоты
        info = await ai_quota_manager.get_user_quota_info(req.user_id)
        remaining = info.get("remaining", 0)
        raise Exception(f"AI limit exceeded: remaining={remaining}")

    text = await ask_gpt_bible_verses(req.problem_text)
    refs = parse_ai_response(text)
    return SuggestResponse(text=text, verse_refs=refs, model=ai_type or "regular")
