import sqlite3
from typing import Optional


class LopukhinCommentary:
    def __init__(self, db_path='data/lopukhin_commentary_rag.sqlite'):
        self.db_path = db_path

    def get_commentary(self, book: str, chapter: int, verse: int) -> Optional[str]:
        """
        Получить толкование по книге (англ. сокращение), главе и стиху.
        Если не найдено точное совпадение по стиху, ищет по главе (verse=0), иначе None.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Сначала ищем точное совпадение
        cursor.execute(
            "SELECT text FROM commentary WHERE book=? AND chapter=? AND verse=?",
            (book, chapter, verse)
        )
        row = cursor.fetchone()
        if row:
            conn.close()
            return row[0]
        # Если не найдено, ищем толкование на главу (verse=0)
        cursor.execute(
            "SELECT text FROM commentary WHERE book=? AND chapter=? AND verse=0",
            (book, chapter)
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return row[0]
        return None

    def get_all_commentaries_for_chapter(self, book: str, chapter: int) -> list:
        """
        Получить все толкования для главы (book, chapter) — список (verse, text).
        """
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT verse, text FROM commentary WHERE book=? AND chapter=? ORDER BY verse",
            (book, chapter)
        )
        rows = cursor.fetchall()
        conn.close()
        return rows


lopukhin_commentary = LopukhinCommentary()
