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

        # Синонимы названий книг для нормализации пользовательского ввода
        self.book_synonyms = {
            # Евангелия и Новый Завет
            "мф": "Мф", "матфей": "Мф", "от матфея": "Мф", "евангелие от матфея": "Мф",
            "мк": "Мк", "марк": "Мк", "от марка": "Мк", "евангелие от марка": "Мк",
            "лк": "Лк", "лука": "Лк", "от луки": "Лк", "евангелие от луки": "Лк",
            "ин": "Ин", "иоанн": "Ин", "от иоанна": "Ин", "евангелие от иоанна": "Ин", "иоанна": "Ин",
            "деян": "Деян", "деяния": "Деян", "деяния апостолов": "Деян",
            "иак": "Иак", "иаков": "Иак", "послание иакова": "Иак", "яков": "Иак", "иакова": "Иак",
            "1пет": "1Пет", "1 петра": "1Пет", "первое послание петра": "1Пет", "1 послание петра": "1Пет",
            "2пет": "2Пет", "2 петра": "2Пет", "второе послание петра": "2Пет", "2 послание петра": "2Пет",
            "1ин": "1Ин", "1 иоанна": "1Ин", "первое послание иоанна": "1Ин",
            "2ин": "2Ин", "2 иоанна": "2Ин", "второе послание иоанна": "2Ин",
            "3ин": "3Ин", "3 иоанна": "3Ин", "третье послание иоанна": "3Ин",
            "иуд": "Иуд", "иуда": "Иуд", "послание иуды": "Иуд",
            "рим": "Рим", "римлянам": "Рим", "послание к римлянам": "Рим",
            "1кор": "1Кор", "1 коринфянам": "1Кор", "первое послание к коринфянам": "1Кор",
            "2кор": "2Кор", "2 коринфянам": "2Кор", "второе послание к коринфянам": "2Кор",
            "гал": "Гал", "галатам": "Гал", "послание к галатам": "Гал",
            "еф": "Еф", "ефесянам": "Еф", "послание к ефесянам": "Еф",
            "флп": "Флп", "филиппийцам": "Флп", "послание к филиппийцам": "Флп",
            "кол": "Кол", "колоссянам": "Кол", "послание к колоссянам": "Кол",
            "1фес": "1Фес", "1 фессалоникийцам": "1Фес", "первое послание к фессалоникийцам": "1Фес",
            "2фес": "2Фес", "2 фессалоникийцам": "2Фес", "второе послание к фессалоникийцам": "2Фес",
            "1тим": "1Тим", "1 тимофею": "1Тим", "первое послание к тимофею": "1Тим",
            "2тим": "2Тим", "2 тимофею": "2Тим", "второе послание к тимофею": "2Тим",
            "тит": "Тит", "титу": "Тит", "послание к титулу": "Тит",
            "флм": "Флм", "филимону": "Флм", "послание к филимону": "Флм",
            "евр": "Евр", "евреям": "Евр", "послание к евреям": "Евр",
            "откр": "Откр", "откровение": "Откр", "откровение иоанна": "Откр", "апокалипсис": "Откр",
            # Ветхий Завет
            "быт": "Быт", "бытие": "Быт",
            "исх": "Исх", "исход": "Исх",
            "лев": "Лев", "левит": "Лев",
            "чис": "Чис", "числа": "Чис",
            "втор": "Втор", "второзаконие": "Втор",
            "нав": "Нав", "иисус навин": "Нав", "навин": "Нав",
            "суд": "Суд", "судей": "Суд",
            "руф": "Руф", "руфь": "Руф",
            "1цар": "1Цар", "1 царств": "1Цар", "первая царств": "1Цар",
            "2цар": "2Цар", "2 царств": "2Цар", "вторая царств": "2Цар",
            "3цар": "3Цар", "3 царств": "3Цар", "третья царств": "3Цар",
            "4цар": "4Цар", "4 царств": "4Цар", "четвертая царств": "4Цар",
            "1пар": "1Пар", "1 паралипоменон": "1Пар", "первая паралипоменон": "1Пар",
            "2пар": "2Пар", "2 паралипоменон": "2Пар", "вторая паралипоменон": "2Пар",
            "езд": "Езд", "ездра": "Езд",
            "неем": "Неем", "неемия": "Неем",
            "есф": "Есф", "естер": "Есф", "естирь": "Есф",
            "иов": "Иов", "йов": "Иов", "книга иова": "Иов",
            "пс": "Пс", "псалтирь": "Пс", "псалмы": "Пс", "псалом": "Пс", "псалм": "Пс",
            "притч": "Прит", "притчи": "Прит", "книга притч": "Прит", "притчи соломона": "Прит", "притчи соломоновы": "Прит",
            "еккл": "Еккл", "екклесиаст": "Еккл",
            "песн": "Песн", "песнь песней": "Песн",
            "ис": "Ис", "исаия": "Ис",
            "иер": "Иер", "иеремия": "Иер",
            "плач": "Плач", "плач иеремии": "Плач",
            "иез": "Иез", "иезекииль": "Иез",
            "дан": "Дан", "даниил": "Дан",
            "ос": "Ос", "осия": "Ос",
            "иоил": "Иоил",
            "ам": "Ам", "амос": "Ам",
            "авд": "Авд", "авдий": "Авд",
            "ион": "Ион", "иона": "Ион",
            "мих": "Мих", "михей": "Мих",
            "наум": "Наум",
            "авв": "Авв", "аввакум": "Авв",
            "соф": "Соф", "софония": "Соф",
            "агг": "Агг", "аггей": "Агг",
            "зах": "Зах", "захария": "Зах",
            "мал": "Мал", "малахия": "Мал"
        }

        # Дополнительные варианты для тем и ссылок
        self.book_synonyms.update({
            "второзаконие": "Втор", "второзакония": "Втор",
            "псалтирь": "Пс", "псалом": "Пс", "псалмы": "Пс", "пс": "Пс",
            "песни песней": "Песн", "песнь песней": "Песн", "песн": "Песн",
            "паралипоменон": "Пар", "паралипоменон 1": "1Пар", "паралипоменон 2": "2Пар",
            "царств": "Цар", "царств 1": "1Цар", "царств 2": "2Цар", "царств 3": "3Цар", "царств 4": "4Цар",
            "матфея": "Мф", "матфей": "Мф", "от матфея": "Мф",
            "марка": "Мк", "марк": "Мк", "от марка": "Мк",
            "луки": "Лк", "лука": "Лк", "от луки": "Лк",
            "иоанна": "Ин", "иоанн": "Ин", "от иоанна": "Ин",
            "петра": "1Пет", "петр": "1Пет", "петра 1": "1Пет", "петра 2": "2Пет",
            "тимофею": "Тим", "тимофей": "Тим", "тимофею 1": "1Тим", "тимофею 2": "2Тим",
            "коринфянам": "Кор", "коринфянам 1": "1Кор", "коринфянам 2": "2Кор",
            "фессалоникийцам": "Фес", "фессалоникийцам 1": "1Фес", "фессалоникийцам 2": "2Фес",
            "филиппийцам": "Флп", "филиппийцы": "Флп",
            "колоссянам": "Кол",
            "евреям": "Евр",
            "иакова": "Иак", "иаков": "Иак",
            "иуды": "Иуд", "иуда": "Иуд",
            "откровение": "Откр", "откровения": "Откр", "апокалипсис": "Откр",
            # Краткие формы для удобства
            "бытие": "Быт", "исход": "Исх", "левит": "Лев", "числа": "Чис", "навин": "Нав", "судей": "Суд", "руфь": "Руф",
            "естер": "Есф", "естирь": "Есф", "йов": "Иов", "притчи": "Прит", "екклесиаст": "Еккл",
            "исаия": "Ис", "иеремия": "Иер", "плач иеремии": "Плач", "иезекииль": "Иез", "даниил": "Дан",
            "осия": "Ос", "иоиль": "Иоил", "амос": "Ам", "авдий": "Авд", "иона": "Ион", "михей": "Мих", "наум": "Наум",
            "аввакум": "Авв", "софония": "Соф", "аггей": "Агг", "захария": "Зах", "малахия": "Мал"
        })

        # Добавляем английские сокращения из book_names.csv как синонимы
        en_to_ru = {
            "Gen": "Быт", "Exod": "Исх", "Lev": "Лев", "Num": "Чис", "Deut": "Втор", "Josh": "Нав", "Judg": "Суд", "Ruth": "Руф",
            "1Sam": "1Цар", "2Sam": "2Цар", "1Kgs": "3Цар", "2Kgs": "4Цар", "1Chr": "1Пар", "2Chr": "2Пар", "Ezra": "Езд", "Neh": "Неем",
            "Esth": "Есф", "Job": "Иов", "Ps": "Пс", "Prov": "Прит", "Eccl": "Еккл", "Song": "Песн", "Isa": "Ис", "Jer": "Иер",
            "Lam": "Плач", "Ezek": "Иез", "Dan": "Дан", "Hos": "Ос", "Joel": "Иоил", "Amos": "Ам", "Obad": "Авд", "Jonah": "Ион",
            "Mic": "Мих", "Nah": "Наум", "Hab": "Авв", "Zeph": "Соф", "Hag": "Агг", "Zech": "Зах", "Mal": "Мал",
            "Matt": "Мф", "Mark": "Мк", "Luke": "Лк", "John": "Ин", "Acts": "Деян", "Jas": "Иак", "1Pet": "1Пет", "2Pet": "2Пет",
            "1John": "1Ин", "2John": "2Ин", "3John": "3Ин", "Jude": "Иуд", "Rom": "Рим", "1Cor": "1Кор", "2Cor": "2Кор",
            "Gal": "Гал", "Eph": "Еф", "Phil": "Флп", "Col": "Кол", "1Thess": "1Фес", "2Thess": "2Фес", "1Tim": "1Тим",
            "2Tim": "2Тим", "Titus": "Тит", "Phlm": "Флм", "Heb": "Евр", "Rev": "Откр"
        }
        for en, ru in en_to_ru.items():
            self.book_synonyms[en.lower()] = ru
            # чтобы normalize_book_name("быт") → "Быт"
            self.book_synonyms[ru.lower()] = ru

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
            logger.info("Правильные значения глав для книг:")
            # 1 Петра (46), 2 Петра (47), 1 Иоанна (48), 2 Фес (60), 1 Тим (61)
            for book_id in [46, 47, 48, 60, 61]:
                book_name = self.book_dict.get(book_id, f'ID {book_id}')
                chapters = correct_chapters.get(book_id)
                logger.info(f"  {book_name}: {chapters} глав")

            # Загружаем максимальное количество глав из Excel
            if "Главы" in self.books_df.columns:
                excel_chapters_count = {}
                for _, row in self.books_df.iterrows():
                    book_id = row["book"]
                    chapters = row["Главы"]
                    if pd.notnull(chapters) and isinstance(chapters, (int, float)):
                        excel_chapters_count[book_id] = int(chapters)

                # Логгируем значения из Excel для тех же книг
                logger.info("Значения глав из Excel:")
                # 1 Петра (46), 2 Петра (47), 1 Иоанна (48), 2 Фес (60), 1 Тим (61)
                for book_id in [46, 47, 48, 60, 61]:
                    book_name = self.book_dict.get(book_id, f'ID {book_id}')
                    chapters = excel_chapters_count.get(book_id)
                    logger.info(f"  {book_name}: {chapters} глав")

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

    def normalize_book_name(self, name: str) -> str:
        """
        Приводит название книги к стандартному сокращению (например, 'от иоанна' -> 'Ин').
        Возвращает сокращение или исходное значение, если не найдено.
        """
        name = name.strip().lower()
        return self.book_synonyms.get(name, name.capitalize())

    def parse_reference(self, reference: str) -> Optional[Tuple[int, int, Optional[int], Optional[int]]]:
        """
        Парсит библейскую ссылку и возвращает (book_id, chapter, start_verse, end_verse)

        Args:
            reference: Библейская ссылка (например, "Мф 5:3-12", "Ин 3:16", "Быт 1")

        Returns:
            Кортеж (book_id, chapter, start_verse, end_verse) или None при ошибке
        """
        import re

        # Пример: Ин 3:16-18 или от иоанна 3:16
        match = re.match(
            r'^([а-яА-ЯёЁ0-9\s]+)\s+(\d+)(?::(\d+)(?:-(\d+))?)?$', reference.strip(), re.IGNORECASE)
        if not match:
            return None

        book_raw = match.group(1).strip()
        chapter = int(match.group(2))
        verse = match.group(3)
        verse_end = match.group(4)

        # Нормализация названия книги
        book_abbr = self.normalize_book_name(book_raw)
        if not book_abbr:
            return None

        # Получаем ID книги
        book_id = self.get_book_id(book_abbr)
        if not book_id:
            return None

        # Проверяем корректность главы
        if not self.is_valid_chapter(book_id, chapter):
            return None

        if verse and verse_end:
            return (book_id, chapter, int(verse), int(verse_end))
        elif verse:
            return (book_id, chapter, int(verse), None)
        else:
            return (book_id, chapter, None, None)


# Создаем глобальный экземпляр класса для использования в других модулях
bible_data = BibleData()


def get_english_book_abbreviation(book_id):
    """
    Получает английское сокращение книги по ID для использования в комментариях и ИИ.
    Возвращает английское сокращение или None, если не найдено.
    """
    en_to_ru = {
        "Gen": "Быт", "Exod": "Исх", "Lev": "Лев", "Num": "Чис", "Deut": "Втор",
        "Josh": "Нав", "Judg": "Суд", "Ruth": "Руф",
        "1Sam": "1Цар", "2Sam": "2Цар", "1Kgs": "3Цар", "2Kgs": "4Цар",
        "1Chr": "1Пар", "2Chr": "2Пар", "Ezra": "Езд", "Neh": "Неем",
        "Esth": "Есф", "Job": "Иов", "Ps": "Пс", "Prov": "Прит",
        "Eccl": "Еккл", "Song": "Песн", "Isa": "Ис", "Jer": "Иер",
        "Lam": "Плач", "Ezek": "Иез", "Dan": "Дан", "Hos": "Ос",
        "Joel": "Иоил", "Amos": "Ам", "Obad": "Авд", "Jonah": "Ион",
        "Mic": "Мих", "Nah": "Наум", "Hab": "Авв", "Zeph": "Соф",
        "Hag": "Агг", "Zech": "Зах", "Mal": "Мал",
        "Matt": "Мф", "Mark": "Мк", "Luke": "Лк", "John": "Ин",
        "Acts": "Деян", "Jas": "Иак", "1Pet": "1Пет", "2Pet": "2Пет",
        "1John": "1Ин", "2John": "2Ин", "3John": "3Ин", "Jude": "Иуд",
        "Rom": "Рим", "1Cor": "1Кор", "2Cor": "2Кор",
        "Gal": "Гал", "Eph": "Еф", "Phil": "Флп", "Col": "Кол",
        "1Thess": "1Фес", "2Thess": "2Фес", "1Tim": "1Тим",
        "2Tim": "2Тим", "Titus": "Тит", "Phlm": "Флм", "Heb": "Евр", "Rev": "Откр"
    }

    # Получаем русское сокращение книги
    book_abbr = None
    for abbr, b_id in bible_data.book_abbr_dict.items():
        if b_id == book_id:
            book_abbr = abbr
            break

    if not book_abbr:
        return None

    # Ищем соответствующее английское сокращение
    for en, ru in en_to_ru.items():
        if ru == book_abbr:
            return en

    return None


async def create_chapter_action_buttons(book_id, chapter, en_book=None, exclude_ai=False, user_id=None):
    """
    Создает кнопки действий для главы (Толкование Лопухина и Разбор от ИИ).
    Учитывает сохраненные толкования пользователя.

    Args:
        book_id: ID книги
        chapter: номер главы
        en_book: английское сокращение книги (если None, будет определено автоматически)
        exclude_ai: если True, исключает кнопку AI разбора
        user_id: ID пользователя для проверки сохраненных толкований

    Returns:
        list: Список кнопок для использования в клавиатуре
    """
    from aiogram.types import InlineKeyboardButton
    from config.settings import ENABLE_LOPUKHIN_COMMENTARY
    from config.ai_settings import ENABLE_GPT_EXPLAIN

    if en_book is None:
        en_book = get_english_book_abbreviation(book_id)

    buttons = []

    # Проверяем сохраненные толкования если user_id передан
    saved_ai_commentary = None
    saved_lopukhin_commentary = None

    if user_id:
        try:
            from database.universal_manager import universal_db_manager

            # Проверяем ИИ толкования (для всей главы - verse 0)
            saved_ai_commentary = await universal_db_manager.get_saved_commentary(
                user_id, book_id, chapter, chapter, 0, 0, "ai"
            )

            # Проверяем толкования Лопухина (для всей главы - verse 0)
            saved_lopukhin_commentary = await universal_db_manager.get_saved_commentary(
                user_id, book_id, chapter, chapter, 0, 0, "lopukhin"
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Ошибка при проверке сохраненных толкований: {e}")

    # Кнопка толкования Лопухина (только если есть en_book)
    if ENABLE_LOPUKHIN_COMMENTARY and en_book:
        # Определяем текст кнопки в зависимости от наличия сохраненного толкования
        lopukhin_text = "📚 Обновить толкование Лопухина" if saved_lopukhin_commentary else "Толкование проф. Лопухина"

        buttons.append([
            InlineKeyboardButton(
                text=lopukhin_text,
                callback_data=f"open_commentary_{en_book}_{chapter}_0"
            )
        ])

    # Кнопка ИИ разбора (только если включена функция и не исключена)
    if ENABLE_GPT_EXPLAIN and not exclude_ai:
        # Используем en_book если есть, иначе UNKNOWN
        book_param = en_book if en_book else "UNKNOWN"

        # Определяем текст кнопки в зависимости от наличия сохраненного толкования
        ai_text = "🔄 Обновить толкование ИИ" if saved_ai_commentary else "🤖 Разбор от ИИ"

        buttons.append([
            InlineKeyboardButton(
                text=ai_text,
                callback_data=f"gpt_explain_{book_param}_{chapter}_0"
            )
        ])

    return buttons
