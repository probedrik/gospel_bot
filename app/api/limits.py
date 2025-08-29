from fastapi import APIRouter
from services.ai_quota_manager import ai_quota_manager

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])


@router.get("/limits")
async def get_limits(user_id: int):
    info = await ai_quota_manager.get_user_quota_info(user_id)
    return info
