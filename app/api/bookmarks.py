from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

from database.universal_manager import universal_db_manager as db

router = APIRouter(prefix="/api/v1/bookmarks", tags=["bookmarks"])


class BookmarkIn(BaseModel):
    user_id: int
    book_id: int
    chapter_start: int
    chapter_end: Optional[int] = None
    verse_start: Optional[int] = None
    verse_end: Optional[int] = None
    display_text: Optional[str] = None
    note: Optional[str] = None


class BookmarkOut(BaseModel):
    id: Optional[int] = None
    user_id: int
    book_id: int
    chapter_start: int
    chapter_end: Optional[int] = None
    verse_start: Optional[int] = None
    verse_end: Optional[int] = None
    display_text: Optional[str] = None
    note: Optional[str] = None


@router.get("", response_model=List[BookmarkOut])
async def list_bookmarks(user_id: int):
    items = await db.get_bookmarks(user_id)
    return items


@router.post("", response_model=bool)
async def add_bookmark(payload: BookmarkIn):
    return await db.add_bookmark(
        user_id=payload.user_id,
        book_id=payload.book_id,
        chapter_start=payload.chapter_start,
        chapter_end=payload.chapter_end,
        display_text=payload.display_text,
        verse_start=payload.verse_start,
        verse_end=payload.verse_end,
        note=payload.note,
    )


@router.delete("")
async def delete_bookmark(
    user_id: int,
    book_id: int,
    chapter_start: int,
    chapter_end: Optional[int] = None,
    verse_start: Optional[int] = None,
    verse_end: Optional[int] = None,
):
    ok = await db.remove_bookmark(user_id, book_id, chapter_start, chapter_end, verse_start, verse_end)
    return {"success": bool(ok)}
