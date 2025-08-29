from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

from database.universal_manager import universal_db_manager as db
from services.universal_reading_plans import universal_reading_plans_service as plans_service

router = APIRouter(prefix="/api/v1/plans", tags=["plans"])


class SetPlanRequest(BaseModel):
    user_id: int
    plan_id: str
    day: Optional[int] = 1


@router.get("")
async def list_plans():
    """Список планов чтения. Для Supabase читаем напрямую из БД."""
    if db.is_supabase or db.is_postgres:
        return await db.get_reading_plans()
    # fallback к локальным/заглушкам
    items = plans_service.get_all_plans()
    # Преобразуем объекты в словари (минимально нужные поля)
    result = []
    for p in items:
        result.append({
            "plan_id": getattr(p, "plan_id", None),
            "title": getattr(p, "title", None),
            "description": getattr(p, "description", None),
            "days": getattr(p, "days", []),
        })
    return result


@router.get("/{plan_id}")
async def get_plan(plan_id: str):
    """Детали плана: для Supabase возвращаем план и дни из БД."""
    if db.is_supabase or db.is_postgres:
        plan = await db.get_reading_plan_by_id(plan_id)
        if not plan:
            return {"error": "not_found"}
        days = await db.get_reading_plan_days(plan_id)
        plan["days"] = days
        return plan
    # fallback
    plan = plans_service.get_plan(plan_id)
    if not plan:
        return {"error": "not_found"}
    return {
        "plan_id": getattr(plan, "plan_id", None),
        "title": getattr(plan, "title", None),
        "description": getattr(plan, "description", None),
        "days": getattr(plan, "days", []),
    }


@router.post("/set")
async def set_user_plan(payload: SetPlanRequest):
    ok = await db.set_user_reading_plan(payload.user_id, payload.plan_id, payload.day or 1)
    return {"success": bool(ok)}


@router.post("/{plan_id}/day/{day}/complete")
async def mark_day_completed(user_id: int, plan_id: str, day: int):
    ok = await db.mark_reading_day_completed(user_id, plan_id, day)
    return {"success": bool(ok)}
