from fastapi import APIRouter, Query
from typing import Optional, Tuple, Union
from utils.api_client import bible_api
from utils.bible_data import bible_data
from handlers.verse_reference import parse_reference, get_chapter_range, get_cross_chapter_range

router = APIRouter(prefix="/api/v1/bible", tags=["bible"])


@router.get("/chapter")
async def get_chapter(
    book_id: int = Query(..., ge=1, le=66),
    chapter: int = Query(..., ge=1),
    translation: Optional[str] = Query("rst"),
    v: Optional[int] = Query(None, description="Опционально: один стих"),
    v2: Optional[int] = Query(
        None, description="Опционально: конец диапазона стихов")
):
    """Возвращает главу целиком или выбранные стихи из главы."""
    if v is not None and v2 is not None:
        rng = (int(v), int(v2))
        text = await bible_api.get_verses(book_id, chapter, rng, translation or "rst")
        return {"book_id": book_id, "chapter": chapter, "translation": translation, "verse_start": rng[0], "verse_end": rng[1], "text": text}
    if v is not None:
        text = await bible_api.get_verses(book_id, chapter, int(v), translation or "rst")
        return {"book_id": book_id, "chapter": chapter, "translation": translation, "verse": int(v), "text": text}

    text = await bible_api.get_formatted_chapter(book_id, chapter, translation)
    return {
        "book_id": book_id,
        "chapter": chapter,
        "translation": translation,
        "text": text,
    }


@router.get("/reference")
async def get_by_reference(
    ref: str = Query(..., description="Ссылка вида 'Ин 3:16', 'Ин 3:16-18', 'Быт 1-3', 'Быт 1:1-2:25'"),
    translation: Optional[str] = Query("rst"),
    v: Optional[int] = Query(
        None, description="Принудительно открыть один стих (перезапишет ссылку)"),
    v2: Optional[int] = Query(
        None, description="Принудительно открыть диапазон стихов: конец (перезапишет ссылку)")
):
    """Возвращает текст по ссылке (стих, диапазон стихов, диапазон глав, кросс-главный диапазон)."""
    book_name, chapter, verse = parse_reference(ref)
    if not book_name:
        return {"error": "bad_reference", "detail": "Неверный формат ссылки"}

    book_id = bible_data.get_book_id(book_name)
    if not book_id:
        return {"error": "book_not_found", "detail": book_name}

    meta = {"book_id": book_id, "book_name": book_name,
            "translation": translation}

    if chapter == "chapter_range":
        start_ch, end_ch = verse  # type: ignore
        text = await get_chapter_range(book_id, start_ch, end_ch, translation or "rst")
        meta.update({"chapter_start": start_ch,
                    "chapter_end": end_ch, "is_range": True})
        return {"text": text, **meta}

    if chapter == "cross_chapter_range":
        start_ch, start_v, end_ch, end_v = verse  # type: ignore
        text = await get_cross_chapter_range(book_id, start_ch, start_v, end_ch, end_v, translation or "rst")
        meta.update({
            "chapter_start": start_ch,
            "verse_start": start_v,
            "chapter_end": end_ch,
            "verse_end": end_v,
            "is_range": True
        })
        return {"text": text, **meta}

    # Принудительный выбор стиха/диапазона, если задано v / v2
    if isinstance(chapter, int) and (v is not None or v2 is not None):
        if v is not None and v2 is not None:
            rng = (int(v), int(v2))
            # type: ignore
            text = await bible_api.get_verses(book_id, chapter, rng, translation or "rst")
            return {"text": text, **meta, "chapter": chapter, "verse_start": rng[0], "verse_end": rng[1]}
        elif v is not None:
            # type: ignore
            text = await bible_api.get_verses(book_id, chapter, int(v), translation or "rst")
            return {"text": text, **meta, "chapter": chapter, "verse": int(v)}

    if verse is not None:
        if isinstance(verse, tuple):
            # type: ignore
            text = await bible_api.get_verses(book_id, chapter, verse, translation or "rst")
            meta.update(
                {"chapter": chapter, "verse_start": verse[0], "verse_end": verse[1]})
        elif isinstance(verse, int):
            # type: ignore
            text = await bible_api.get_verses(book_id, chapter, verse, translation or "rst")
            meta.update({"chapter": chapter, "verse": verse})
        else:
            # type: ignore
            text = await bible_api.get_formatted_chapter(book_id, chapter, translation or "rst")
            meta.update({"chapter": chapter})
        return {"text": text, **meta}

    # Вся глава
    # type: ignore
    text = await bible_api.get_formatted_chapter(book_id, chapter, translation or "rst")
    meta.update({"chapter": chapter})
    return {"text": text, **meta}
