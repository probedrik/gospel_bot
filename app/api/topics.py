from fastapi import APIRouter, Query
from typing import Optional
from database.universal_manager import universal_db_manager as db

router = APIRouter(prefix="/api/v1/topics", tags=["topics"])


@router.get("")
async def list_topics(query: Optional[str] = Query(""), limit: int = 50):
    items = await db.get_bible_topics(query or "", limit)
    return items


@router.get("/{topic_id}")
async def get_topic(topic_id: int):
    item = await db.get_topic_by_id(topic_id)
    if not item:
        return {"error": "not_found"}
    return item
