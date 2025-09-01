import json
import os
from typing import Dict, Any, Optional, Tuple, List, Union


class LocalBibleService:
    """Чтение Библии из локальных JSON файлов (local/rst.json, local/rbo.json).

    Ожидаемый формат JSON (упрощённо):
    {
      "books": {
        "1": { "chapters": { "1": ["стих1", "стих2", ...], "2": [...] } },
        "2": { ... }
      }
    }
    или
    {
      "1": { "1": ["стих1", ...], "2": [...] },
      "2": { ... }
    }
    Сервис пытается понять оба варианта.
    """

    def __init__(self, base_path: str = "local"):
        self.base_path = base_path
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _load(self, translation: str) -> Dict[str, Any]:
        tr = translation.lower()
        if tr in self._cache:
            return self._cache[tr]

        filename = f"{tr}.json"
        path = os.path.join(self.base_path, filename)
        if not os.path.exists(path):
            # пустая структура
            data: Dict[str, Any] = {}
            self._cache[tr] = data
            return data

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self._cache[tr] = data
            return data

    @staticmethod
    def _extract_books_struct(data: Dict[str, Any]) -> Dict[str, Any]:
        # поддержка двух форматов корневой структуры
        if isinstance(data, dict):
            if "books" in data and isinstance(data["books"], dict):
                return data["books"]
            return data
        return {}

    def get_chapter(self, translation: str, book_id: int, chapter: int) -> str:
        data = self._load(translation)
        books = self._extract_books_struct(data)
        book = books.get(str(book_id))
        if not book:
            return "Книга не найдена"

        # Возможные ключи: book["chapters"][str(chapter)] или book[str(chapter)]
        chapters = book.get("chapters") if isinstance(book, dict) else None
        verses: Optional[List[str]] = None
        if isinstance(chapters, dict):
            verses = chapters.get(str(chapter))
        if verses is None and isinstance(book, dict):
            verses = book.get(str(chapter))

        if not verses:
            return "Глава не найдена"

        # Склеиваем стихи с номерами
        lines = []
        for i, v in enumerate(verses, start=1):
            lines.append(f"{i}. {v}")
        return "\n".join(lines)

    def get_verses(self, translation: str, book_id: int, chapter: int, verse: Union[int, Tuple[int, int]]) -> str:
        data = self._load(translation)
        books = self._extract_books_struct(data)
        book = books.get(str(book_id))
        if not book:
            return "Книга не найдена"

        chapters = book.get("chapters") if isinstance(book, dict) else None
        verses_list: Optional[List[str]] = None
        if isinstance(chapters, dict):
            verses_list = chapters.get(str(chapter))
        if verses_list is None and isinstance(book, dict):
            verses_list = book.get(str(chapter))

        if not verses_list:
            return "Глава не найдена"

        if isinstance(verse, tuple):
            start, end = verse
            start = max(1, int(start))
            end = min(len(verses_list), int(end))
            if start > end:
                return "Неверный диапазон стихов"
            parts = [f"{i}. {verses_list[i-1]}" for i in range(start, end+1)]
            return "\n".join(parts)
        else:
            v = int(verse)
            if v < 1 or v > len(verses_list):
                return "Стих не найден"
            return f"{v}. {verses_list[v-1]}"

    def search(self, translation: str, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        data = self._load(translation)
        books = self._extract_books_struct(data)
        results: List[Dict[str, Any]] = []
        q = (query or "").strip().lower()
        if not q:
            return results
        for book_id, book in books.items():
            chapters = None
            if isinstance(book, dict) and isinstance(book.get("chapters"), dict):
                chapters = book["chapters"]
            elif isinstance(book, dict):
                chapters = {k: v for k,
                            v in book.items() if isinstance(v, list)}
            if not isinstance(chapters, dict):
                continue
            for ch_str, verses in chapters.items():
                if not isinstance(verses, list):
                    continue
                for idx, text in enumerate(verses, start=1):
                    if q in str(text).lower():
                        results.append({
                            "book_id": int(book_id),
                            "chapter": int(ch_str),
                            "verse": idx,
                            "text": text,
                        })
                        if len(results) >= limit:
                            return results
        return results


local_bible_service = LocalBibleService()
