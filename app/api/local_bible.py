from fastapi import APIRouter, Query
from typing import Optional
from services.local_bible import local_bible_service
from utils.bible_data import bible_data

router = APIRouter(prefix="/api/v1/local-bible", tags=["local-bible"])


def _title_html(book_id: int, chapter: int, ref_text: str) -> str:
    testament = "Ветхий завет" if book_id < 40 else "Новый завет"
    book_name = bible_data.get_book_name(book_id)
    return f"<b>{testament}. {book_name} {chapter}:{ref_text}</b>\n\n"


@router.get("/chapter")
async def local_chapter(
    translation: str = Query("rst", description="rst или rbo"),
    book_id: int = Query(..., ge=1, le=66),
    chapter: int = Query(..., ge=1),
    v: Optional[int] = Query(None),
    v2: Optional[int] = Query(None),
    header: bool = Query(
        False, description="Добавить HTML-заголовок с жирным шрифтом"),
):
    """Глава целиком или выбранные стихи из локальных JSON."""
    if v is not None and v2 is not None:
        text = await local_bible_service.get_verses(book_id, chapter, (int(v), int(v2)), translation)
        if header:
            text = _title_html(book_id, chapter, f"{int(v)}-{int(v2)}") + text
        return {"translation": translation, "book_id": book_id, "chapter": chapter, "verse_start": int(v), "verse_end": int(v2), "text": text}
    if v is not None:
        text = await local_bible_service.get_verses(book_id, chapter, int(v), translation)
        if header:
            text = _title_html(book_id, chapter, f"{int(v)}") + text
        return {"translation": translation, "book_id": book_id, "chapter": chapter, "verse": int(v), "text": text}

    text = await local_bible_service.get_formatted_chapter(book_id, chapter, translation)
    return {"translation": translation, "book_id": book_id, "chapter": chapter, "text": text}


@router.get("/reference")
async def local_reference(
    ref: str = Query(..., description="Полная библейская ссылка: 'Ин 3:16', 'Ин 3:16-18', 'Быт 1-3', 'Быт 1:1-2:25'"),
    translation: str = Query("rst", description="rst или rbo"),
    header: bool = Query(
        False, description="Добавить HTML-заголовок с жирным шрифтом"),
):
    """Возвращает текст по ссылке из локальных JSON (как в основном API)."""
    text = await local_bible_service.get_verse_by_reference(ref, translation)

    if header:
        # Пытаемся распарсить книгу/главу/стихи из ссылки, чтобы сформировать заголовок
        parsed = bible_data.parse_reference(ref)
        if parsed:
            book_id, ch, v1, v2 = parsed
            ref_text = f"{v1}-{v2}" if (v1 and v2) else (str(v1) if v1 else "")
            if ref_text:
                text = _title_html(book_id, ch, ref_text) + text
            else:
                # Вся глава
                testament = "Ветхий завет" if book_id < 40 else "Новый завет"
                book_name = bible_data.get_book_name(book_id)
                text = f"<b>{testament}. {book_name} {ch}:</b>\n\n" + text

    return {"translation": translation, "reference": ref, "text": text}


@router.get("/search")
async def local_search(
    q: str = Query(..., description="строка поиска"),
    translation: str = Query("rst", description="rst или rbo"),
    limit: int = Query(20, ge=1, le=100),
):
    items = await local_bible_service.search_bible_text(q, translation)
    return {"translation": translation, "query": q, "results": items[:limit]}
