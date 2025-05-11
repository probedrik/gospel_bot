"""
Утилиты для работы с данными Библии (загрузка из Excel, сопоставление сокращений).
"""
import logging
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime

from config.settings import EXCEL_FILES

# Инициализация логгера
logger = logging.getLogger(__name__)


class BibleData:
    """Класс для работы с данными Библии."""

    def __init__(self):
        self.books_df = None
        self.plan_df = None
        self.book_names = []
        self.book_values = []
        self.book_dict = {}
        self.books = {}  # Атрибут для обратной совместимости

        # Словарь соответствия сокращений книг и их ID
        self.book_abbr_dict = {
            "Быт": 1, "Исх": 2, "Лев": 3, "Чис": 4, "Втор": 5, "Нав": 6, "Суд": 7, "Руф": 8,
            "1Цар": 9, "2Цар": 10, "3Цар": 11, "4Цар": 12, "1Пар": 13, "2Пар": 14, "Езд": 15,
            "Неем": 16, "Есф": 17, "Иов": 18, "Пс": 19, "Прит": 20, "Еккл": 21, "Песн": 22,
            "Ис": 23, "Иер": 24, "Плач": 25, "Иез": 26, "Дан": 27, "Ос": 28, "Иоил": 29,
            "Ам": 30, "Авд": 31, "Ион": 32, "Мих": 33, "Наум": 34, "Авв": 35, "Соф": 36,
            "Агг": 37, "Зах": 38, "Мал": 39, "Мф": 40, "Мк": 41, "Лк": 42, "Ин": 43,
            "Деян": 44, "Иак": 45, "1Пет": 46, "2Пет": 47, "1Ин": 48, "2Ин": 49, "3Ин": 50,
            "Иуд": 51, "Рим": 52, "1Кор": 53, "2Кор": 54, "Гал": 55, "Еф": 56, "Флп": 57,
            "Кол": 58, "1Фес": 59, "2Фес": 60, "1Тим": 61, "2Тим": 62, "Тит": 63, "Флм": 64,
            "Евр": 65, "Откр": 66
        }

        # Максимальное количество глав в каждой книге
        self.max_chapters = {
            # Ветхий Завет
            1: 50, 2: 40, 3: 27, 4: 36, 5: 34, 6: 24, 7: 21, 8: 4,
            9: 31, 10: 24, 11: 22, 12: 25, 13: 29, 14: 36, 15: 10,
            16: 13, 17: 10, 18: 42, 19: 150, 20: 31, 21: 12, 22: 8,
            23: 66, 24: 52, 25: 5, 26: 48, 27: 12, 28: 14, 29: 3,
            30: 9, 31: 1, 32: 4, 33: 7, 34: 3, 35: 3, 36: 3,
            37: 2, 38: 14, 39: 4,
            # Новый Завет
            40: 28, 41: 16, 42: 24, 43: 21, 44: 28, 45: 5, 46: 5,
            47: 3, 48: 5, 49: 1, 50: 1, 51: 1, 52: 16, 53: 16,
            54: 13, 55: 6, 56: 6, 57: 4, 58: 4, 59: 5, 60: 3,
            61: 6, 62: 4, 63: 3, 64: 1, 65: 13, 66: 22
        }

        self.load_data()

    def load_data(self) -> None:
        """Загружает данные из Excel файлов."""
        try:
            # Загрузка списка книг
            self.books_df = pd.read_excel(EXCEL_FILES["books"])
            self.book_names = self.books_df["Книга Библии"].tolist()
            self.book_values = self.books_df["book"].tolist()
            self.book_dict = dict(zip(self.book_values, self.book_names))

            # Обновляем атрибут books для обратной совместимости
            self.books = self.book_dict

            # Сохраняем правильные значения для количества глав
            # Эти значения заданы изначально в self.max_chapters и являются правильными
            correct_chapters = self.max_chapters.copy()

            # Логгируем исходные значения для важных книг
            logger.info(f"Правильные значения глав для книг:")
            # 1 Петра (46), 2 Петра (47), 1 Иоанна (48), 2 Фес (60), 1 Тим (61)
            for book_id in [46, 47, 48, 60, 61]:
                logger.info(f"  {self.book_dict.get(book_id, f'ID {book_id}')}: {
                            correct_chapters.get(book_id)} глав")

            # Загружаем максимальное количество глав из Excel
            if "Главы" in self.books_df.columns:
                excel_chapters_count = {}
                for _, row in self.books_df.iterrows():
                    book_id = row["book"]
                    chapters = row["Главы"]
                    if pd.notnull(chapters) and isinstance(chapters, (int, float)):
                        excel_chapters_count[book_id] = int(chapters)

                # Логгируем значения из Excel для тех же книг
                logger.info(f"Значения глав из Excel:")
                # 1 Петра (46), 2 Петра (47), 1 Иоанна (48), 2 Фес (60), 1 Тим (61)
                for book_id in [46, 47, 48, 60, 61]:
                    logger.info(f"  {self.book_dict.get(book_id, f'ID {book_id}')}: {
                                excel_chapters_count.get(book_id)} глав")

                # Проверяем на расхождения
                discrepancies = []
                for book_id, correct_value in correct_chapters.items():
                    if book_id in excel_chapters_count and excel_chapters_count[book_id] != correct_value:
                        discrepancies.append(
                            (book_id, correct_value, excel_chapters_count[book_id]))

                if discrepancies:
                    logger.warning(
                        f"Обнаружены расхождения в количестве глав:")
                    for book_id, correct_value, excel_value in discrepancies:
                        book_name = self.book_dict.get(
                            book_id, f'ID {book_id}')
                        logger.warning(
                            f"  {book_name}: Excel={excel_value}, Правильно={correct_value}")

                # Используем правильные значения
                self.max_chapters = correct_chapters

                # ВАЖНО: Второе послание Петра (ID 47) должно иметь 3 главы
                if 47 in self.max_chapters:
                    self.max_chapters[47] = 3
                    logger.info(
                        f"Принудительно установлено 3 главы для 2 Петра (ID 47)")

                logger.info("Установлены правильные значения количества глав")

            # Загрузка плана чтения
            self.plan_df = pd.read_excel(EXCEL_FILES["reading_plan"])
            self.plan_df["day"] = self.plan_df["day"].dt.strftime("%Y-%m-%d")

            logger.info("Данные успешно загружены из Excel файлов")
        except FileNotFoundError as e:
            logger.error(f"Ошибка: файл {e.filename} не найден")
            raise
        except KeyError as e:
            logger.error(f"Ошибка в структуре Excel: {e}")
            raise

    def get_book_name(self, book_id: int) -> str:
        """Возвращает название книги по её ID."""
        return self.book_dict.get(book_id, f"Книга {book_id}")

    def get_book_id(self, abbr: str) -> Optional[int]:
        """Возвращает ID книги по её сокращению."""
        return self.book_abbr_dict.get(abbr)

    def is_valid_chapter(self, book_id: int, chapter: int) -> bool:
        """Проверяет, существует ли указанная глава в книге."""
        if book_id not in self.max_chapters:
            return False
        return 1 <= chapter <= self.max_chapters[book_id]

    def get_daily_reading(self, date: Optional[datetime] = None) -> Optional[dict]:
        """
        Возвращает план чтения на указанную дату.

        Args:
            date: Дата, на которую нужно получить план чтения.
                 Если не указана, используется текущая дата.

        Returns:
            Словарь с данными плана чтения или None, если на указанную дату нет плана.
        """
        if date is None:
            date = datetime.now()

        date_str = date.strftime("%Y-%m-%d")
        plan_rows = self.plan_df[self.plan_df["day"] == date_str]

        if plan_rows.empty:
            return None

        return plan_rows.iloc[0].to_dict()


# Создаем глобальный экземпляр класса для использования в других модулях
bible_data = BibleData()
