"""
Модуль для работы с православным календарем
Интеграция с Holy Trinity Orthodox Calendar API
"""
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import aiohttp
from utils.bible_data import bible_data

logger = logging.getLogger(__name__)


def get_last_verse_in_chapter(book_name: str, chapter: int) -> int:
    """
    Определяет последний стих в указанной главе книги Библии
    Возвращает приблизительное значение на основе средних показателей
    """
    # Стандартные данные о примерном количестве стихов в главах
    # Это приблизительные значения для основных книг
    verse_counts = {
        # Евангелия (обычно 20-50 стихов на главу)
        'Матфея': 35, 'Марка': 30, 'Луки': 35, 'Иоанна': 30,
        # Послания Павла
        '1 Коринфянам': 30, '2 Коринфянам': 25, 'Римлянам': 25,
        'Галатам': 25, 'Ефесянам': 25, 'Филиппийцам': 25,
        'Колоссянам': 25, '1 Фессалоникийцам': 25, '2 Фессалоникийцам': 15,
        '1 Тимофею': 20, '2 Тимофею': 20, 'Титу': 15, 'Филимону': 25,
        'Евреям': 25,
        # Соборные послания
        'Иакова': 25, '1 Петра': 25, '2 Петра': 20,
        '1 Иоанна': 25, '2 Иоанна': 15, '3 Иоанна': 15, 'Иуды': 25,
        # Деяния и Откровение
        'Деяния': 40, 'Откровение': 25,
        # ВЗ - основные книги
        'Бытие': 35, 'Исход': 35, 'Левит': 25, 'Числа': 35, 'Второзаконие': 35,
        'Псалтирь': 20, 'Притчи': 30, 'Исаия': 25, 'Иеремия': 25, 'Иезекииль': 30
    }

    # Получаем приблизительное количество стихов
    estimated_verses = verse_counts.get(
        book_name, 25)  # По умолчанию 25 стихов

    # Для некоторых конкретных случаев корректируем
    if book_name == 'Иоанна' and chapter == 15:
        return 27  # Точно знаем что в Ин 15 - 27 стихов
    elif book_name == 'Иоанна' and chapter == 16:
        return 33  # Точно знаем что в Ин 16 - 33 стиха
    elif book_name == '1 Коринфянам' and chapter == 13:
        return 13  # 1 Кор 13 - 13 стихов
    elif book_name == '1 Коринфянам' and chapter == 14:
        return 40  # 1 Кор 14 - 40 стихов

    return estimated_verses


# Базовый URL для православного календаря
CALENDAR_BASE_URL = "http://www.holytrinityorthodox.com/ru/calendar/calendar.php"

# Настройки по умолчанию для календаря (соответствуют Supabase)
DEFAULT_CALENDAR_SETTINGS = {
    'header': True,      # Показывать заголовок календаря
    'lives': False,      # Показывать жития святых (отключено)
    'tropars': False,    # Показывать тропари (отключено)
    'scripture': True,   # Показывать Евангельские чтения
    'date_format': True  # Показывать дату в формате григорианский/юлианский
}


class OrthodoxyCalendar:
    """Класс для работы с православным календарем"""

    def __init__(self):
        self._session = None
        self._cache = {}  # Простой кэш для календарных данных

    async def get_session(self) -> aiohttp.ClientSession:
        """Возвращает HTTP сессию"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        """Закрывает HTTP сессию"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def get_calendar_data(self,
                                date: datetime = None,
                                settings: Dict = None) -> Optional[str]:
        """
        Получает данные православного календаря на указанную дату

        Args:
            date: Дата для получения календаря (по умолчанию - сегодня)
            settings: Настройки отображения календаря

        Returns:
            HTML-содержимое календаря или None при ошибке
        """
        if date is None:
            date = datetime.now()

        if settings is None:
            settings = DEFAULT_CALENDAR_SETTINGS

        # Создаем ключ кэша
        cache_key = f"calendar_{date.strftime('%Y_%m_%d')}_{hash(str(settings))}"

        # Проверяем кэш
        if cache_key in self._cache:
            cached_data, cache_time = self._cache[cache_key]
            # Кэш действителен 1 час
            if (datetime.now() - cache_time).total_seconds() < 3600:
                logger.debug(f"Календарь получен из кэша: {cache_key}")
                return cached_data

        # Формируем параметры запроса
        params = {
            'month': date.month,
            'today': date.day,
            'year': date.year
        }

        # Добавляем настройки (всегда передаем все параметры)
        params['dt'] = 1 if settings.get('date_format', True) else 0
        params['header'] = 1 if settings.get('header', True) else 0

        # lives: 0=запретить, 1=отдельные строки, 2=один параграф, 3=основные отдельно, 4=основные параграф, 5=основные+новомученики отдельно, 6=основные+новомученики параграф
        lives_setting = settings.get('lives', 0)
        # Преобразуем в число
        if isinstance(lives_setting, bool):
            lives_setting = 0 if not lives_setting else 1
        elif isinstance(lives_setting, str):
            try:
                lives_setting = int(lives_setting)
            except ValueError:
                lives_setting = 0
        elif not isinstance(lives_setting, int):
            lives_setting = 0
        params['lives'] = lives_setting

        # trp: 0=запретить, 1=с заголовком, 2=без заголовка
        tropars_setting = settings.get('tropars', 0)
        if isinstance(tropars_setting, bool):
            # Для совместимости с старыми настройками
            params['trp'] = 1 if tropars_setting else 0
        else:
            params['trp'] = int(tropars_setting) if tropars_setting in [
                0, 1, 2] else 0

        # scripture: 0=запретить, 1=с заголовком, 2=без заголовка
        scripture_setting = settings.get('scripture', 1)
        if isinstance(scripture_setting, bool):
            # Для совместимости с старыми настройками
            params['scripture'] = 1 if scripture_setting else 0
        else:
            params['scripture'] = int(scripture_setting) if scripture_setting in [
                0, 1, 2] else 1

        # Отладочный вывод настроек и параметров
        logger.info(f"Настройки полученные в get_calendar_data: {settings}")
        logger.info(f"Параметры запроса к календарю: {params}")

        try:
            session = await self.get_session()
            async with session.get(CALENDAR_BASE_URL, params=params, timeout=10) as response:
                if response.status == 200:
                    html_content = await response.text(encoding='windows-1251')

                    # Сохраняем в кэш
                    self._cache[cache_key] = (html_content, datetime.now())

                    logger.info(
                        f"Календарь успешно получен для {date.strftime('%Y-%m-%d')}")
                    logger.info(
                        f"Первые 500 символов ответа: {html_content[:500]}")
                    return html_content
                else:
                    logger.error(
                        f"Ошибка HTTP {response.status} при запросе календаря")
                    return None

        except Exception as e:
            logger.error(f"Ошибка при получении календаря: {e}")
            return None

    def parse_calendar_content(self, html_content: str) -> Dict[str, Any]:
        """
        Парсит HTML-содержимое календаря и извлекает структурированные данные

        Args:
            html_content: HTML-содержимое календаря

        Returns:
            Словарь с разобранными данными календаря
        """
        if not html_content:
            return {}

        # Удаляем HTML теги, оставляя только <p>, </p> и <br>
        # Аналогично примеру из документации
        import re
        from html import unescape

        # Декодируем HTML entities
        clean_content = unescape(html_content)

        result = {
            'date': '',
            'header': '',
            'saints': [],
            'tropars': '',
            'scripture_readings': [],
            'raw_content': clean_content
        }

        # Ищем дату
        date_match = re.search(
            r'<p class="pdataheader"[^>]*>(.*?)</p>', clean_content, re.DOTALL)
        if date_match:
            result['date'] = re.sub(
                r'<[^>]+>', '', date_match.group(1)).strip()

        # Ищем заголовок
        header_match = re.search(
            r'<p class="pheaderheader"[^>]*>(.*?)</p>', clean_content, re.DOTALL)
        if header_match:
            result['header'] = re.sub(
                r'<[^>]+>', '', header_match.group(1)).strip()

            # Ищем жития святых (только текст святых, не заголовки)
        # Ищем между заголовком и чтениями дня
        saints_pattern = r'<span class="normaltext"[^>]*>(.*?)\s*<p class="pscriptureheader"'
        saints_match = re.search(saints_pattern, clean_content, re.DOTALL)

        if saints_match:
            saints_text = saints_match.group(1).strip()

            # Удаляем все HTML теги
            saints_clean = re.sub(r'<[^>]+>', '', saints_text)

            # Убираем переносы строк и лишние пробелы
            saints_clean = re.sub(r'\s+', ' ', saints_clean).strip()

            # Используем более умное разделение - ищем записи разделенные точкой + пробел + заглавная буква + характерное начало
            # Характерные начала записей о святых
            saint_patterns = [
                r'Славного', r'Святого', r'Святой', r'Святых',
                r'Преподобного', r'Преподобной', r'Преподобных',
                r'Мученика', r'Мученицы', r'Мучеников',
                r'Священномученика', r'Священномучеников',
                r'Преставление', r'Обретение', r'Перенесение',
                r'Память', r'Собор', r'Празднование',
                r'Блаженного', r'Блаженной', r'Блаженных',
                r'Праведного', r'Праведной', r'Праведных',
                r'Пророка', r'Пророков',
                r'Апостола', r'Апостолов',
                r'Великомученика', r'Великомучеников', r'Великомученицы',
                r'[А-ЯЁ][а-яё]*(\s+и\s+[А-ЯЁ][а-яё]*)*\s+(пресвитера|диакона|епископа|архиепископа|митрополита)'
            ]

            pattern = r'\.\s+(?=' + '|'.join(saint_patterns) + ')'
            saint_entries = re.split(pattern, saints_clean)

            for entry in saint_entries:
                # Проверяем что entry не None
                if entry is None:
                    continue

                clean_entry = entry.strip()

                # Убираем лишние символы в начале
                clean_entry = re.sub(r'^\s*[.\s]*', '', clean_entry)

                # Фильтруем записи
                if (clean_entry and
                    len(clean_entry) > 15 and  # Увеличили минимальную длину
                    not clean_entry.isspace() and
                    not clean_entry.startswith('Седмица') and
                        not clean_entry.startswith('Глас')):

                    # Добавляем точку в конце если её нет
                    if not clean_entry.endswith('.'):
                        clean_entry += '.'

                    logger.info(f"Добавляем в saints: {clean_entry}")
                    result['saints'].append(clean_entry)

        # Ищем чтения дня
        scripture_pattern = r'<p class="pscriptureheader"[^>]*>.*?</p>\s*(.*?)\s*(?:<p class="ptroparionheader"|$)'
        scripture_match = re.search(
            scripture_pattern, clean_content, re.DOTALL)
        if scripture_match:
            scripture_text = scripture_match.group(1).strip()
            # Разделяем по <br> и очищаем
            scripture_lines = scripture_text.split('<br>')
            for line in scripture_lines:
                clean_line = re.sub(r'<[^>]+>', '', line).strip()
                if clean_line and not clean_line.isspace():
                    result['scripture_readings'].append(clean_line)

        # Добавляем структурированные ссылки для кнопок
        result['scripture_references'] = self._parse_scripture_references(
            result['scripture_readings'])

        # Ищем тропари
        tropars_pattern = r'<p class="ptroparionheader"[^>]*>.*?</p>\s*(.*?)(?:</body>|$)'
        tropars_match = re.search(tropars_pattern, clean_content, re.DOTALL)
        if tropars_match:
            tropars_text = tropars_match.group(1).strip()
            # Очищаем от тегов, но оставляем структуру
            result['tropars'] = re.sub(
                r'</?p[^>]*>', '\n', tropars_text).strip()
            result['tropars'] = re.sub(
                r'<[^>]+>', '', result['tropars']).strip()
            result['tropars'] = re.sub(r'\n\s*\n', '\n\n', result['tropars'])

        logger.info(
            f"Результат парсинга календаря: saints={result['saints']}, scripture_readings={result['scripture_readings']}")
        return result

    def format_calendar_message(self, calendar_data: Dict[str, Any], settings: Dict = None) -> tuple[str, bool]:
        """
        Форматирует данные календаря для отправки в Telegram

        Args:
            calendar_data: Разобранные данные календаря
            settings: Настройки отображения

        Returns:
            Tuple: (отформатированное сообщение, флаг есть ли дополнительный контент)
        """
        if not calendar_data:
            return "❌ Не удалось получить данные календаря", False

        # Если настройки не переданы, используем базовые (все включено)
        if settings is None:
            settings = DEFAULT_CALENDAR_SETTINGS

        message_parts = []

        # Заголовок с иконкой
        message_parts.append("📅 **Православный календарь**")

        # Дата (если API вернул её)
        if calendar_data.get('date'):
            message_parts.append(f"📆 {calendar_data['date']}")

        # Заголовок календаря (если API вернул его)
        if calendar_data.get('header'):
            message_parts.append(f"✨ {calendar_data['header']}")

        # Добавляем жития святых если есть
        if calendar_data.get('saints'):
            message_parts.append("\n👼 **Память святых:**")
            for saint in calendar_data['saints']:
                if saint.strip():
                    message_parts.append(f"• {saint}")

        # Тропари (если API вернул их)
        if calendar_data.get('tropars'):
            message_parts.append("\n🎵 **Тропари:**")
            tropars = calendar_data['tropars']
            message_parts.append(tropars)

        # Евангельские чтения (если API вернул их)
        if calendar_data.get('scripture_readings'):
            message_parts.append("\n📖 **Евангельские чтения:**")
            for reading in calendar_data['scripture_readings']:
                if reading.strip():
                    message_parts.append(f"• {reading}")
            message_parts.append(
                "_Нажмите кнопки ниже для чтения полного текста_")

        result = "\n".join(message_parts)

        # Telegram ограничивает сообщения до 4096 символов
        # Если сообщение длинное, разбиваем на части
        if len(result) > 4000:  # Оставляем запас для клавиатуры
            return self._split_long_message(result), True

        return result, False  # Убираем дополнительные кнопки

    def _split_long_message(self, message: str) -> str:
        """
        Разбивает длинное сообщение на основную часть и создает кнопку 'Читать далее'

        Args:
            message: Полное сообщение

        Returns:
            Сокращенная версия сообщения
        """
        # Находим подходящее место для разрыва (по секциям)
        sections = message.split('\n\n')

        current_length = 0
        main_parts = []
        remaining_parts = []
        split_found = False

        for section in sections:
            # Запас для "... [Читать далее]"
            if not split_found and current_length + len(section) + 2 < 3500:
                main_parts.append(section)
                current_length += len(section) + 2
            else:
                if not split_found:
                    split_found = True
                remaining_parts.append(section)

        if remaining_parts:
            main_message = '\n\n'.join(main_parts)
            main_message += "\n\n... [Используйте кнопки навигации для полного просмотра]"
            return main_message

        return message

    def format_lives_message(self, calendar_data: Dict[str, Any]) -> str:
        """
        Форматирует только жития святых

        Args:
            calendar_data: Данные календаря

        Returns:
            Сообщение с житиями святых
        """
        if not calendar_data.get('saints'):
            return "👼 **Жития святых**\n\nНа сегодня нет информации о житиях святых."

        message_parts = ["👼 **Жития святых**"]

        for saint in calendar_data['saints']:
            if saint.strip():
                message_parts.append(f"• {saint}")

        return "\n".join(message_parts)

    def format_tropars_message(self, calendar_data: Dict[str, Any]) -> str:
        """
        Форматирует только тропари

        Args:
            calendar_data: Данные календаря

        Returns:
            Сообщение с тропарями
        """
        if not calendar_data.get('tropars'):
            return "🎵 **Тропари**\n\nНа сегодня нет тропарей."

        message_parts = ["🎵 **Тропари**"]
        message_parts.append(calendar_data['tropars'])

        return "\n".join(message_parts)

    def extract_scripture_references(self, calendar_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Извлекает ссылки на Евангельские чтения для создания кнопок

        Args:
            calendar_data: Данные календаря

        Returns:
            Список словарей с информацией о чтениях
        """
        references = []

        if not calendar_data.get('scripture_readings'):
            return references

        # Паттерн для поиска библейских ссылок
        # Например: "Матфея 11:27-30", "Галатам 5:22-6:2", "Луки 6:17-23"
        reference_pattern = r'([1-3]?\s*[А-Я][а-я]+[а-я]*)\s+(\d+):(\d+)(?:-(\d+))?'

        for reading in calendar_data['scripture_readings']:
            matches = re.finditer(reference_pattern, reading)
            for match in matches:
                book_name = match.group(1).strip()
                chapter = int(match.group(2))
                verse_start = int(match.group(3))
                verse_end = int(match.group(4)) if match.group(
                    4) else verse_start

                # Пытаемся найти соответствующую книгу в нашей базе
                book_id = self._find_book_id_by_full_name(book_name)

                if book_id:
                    references.append({
                        'book_name': book_name,
                        'book_id': book_id,
                        'chapter': chapter,
                        'verse_start': verse_start,
                        'verse_end': verse_end,
                        'display_text': f"{book_name} {chapter}:{verse_start}" +
                                      (f"-{verse_end}" if verse_end !=
                                       verse_start else ""),
                                      'original_text': reading
                                      })

        logger.info(
            f"Найдено {len(references)} Евангельских чтений: {[ref['display_text'] for ref in references]}")
        return references

    def _find_book_id_by_abbreviation(self, abbr: str) -> Optional[int]:
        """
        Находит ID книги по русскому сокращению

        Args:
            abbr: Сокращение книги (например, "Мф", "Лк")

        Returns:
            ID книги или None
        """
        # Словарь соответствий русских сокращений (совпадает с нумерацией bible_data.py)
        abbreviation_map = {
            'Быт': 1, 'Исх': 2, 'Лев': 3, 'Чис': 4, 'Втор': 5,
            'Нав': 6, 'Суд': 7, 'Руф': 8,
            '1Цар': 9, '2Цар': 10, '3Цар': 11, '4Цар': 12,
            '1Пар': 13, '2Пар': 14, 'Езд': 15, 'Неем': 16, 'Есф': 17,
            'Иов': 18, 'Пс': 19, 'Прит': 20, 'Еккл': 21, 'Песн': 22,
            'Ис': 23, 'Иер': 24, 'Плач': 25, 'Иез': 26, 'Дан': 27,
            'Ос': 28, 'Иоил': 29, 'Ам': 30, 'Авд': 31, 'Ион': 32,
            'Мих': 33, 'Наум': 34, 'Авв': 35, 'Соф': 36, 'Агг': 37,
            'Зах': 38, 'Мал': 39,
            # Новый Завет (порядок как в bible_data.py)
            'Мф': 40, 'Мк': 41, 'Лк': 42, 'Ин': 43, 'Деян': 44,
            'Иак': 45, '1Пет': 46, '2Пет': 47, '1Ин': 48, '2Ин': 49,
            '3Ин': 50, 'Иуд': 51, 'Рим': 52, '1Кор': 53, '2Кор': 54,
            'Гал': 55, 'Еф': 56, 'Флп': 57, 'Кол': 58, '1Фес': 59,
            '2Фес': 60, '1Тим': 61, '2Тим': 62, 'Тит': 63, 'Флм': 64,
            'Евр': 65, 'Откр': 66
        }

        return abbreviation_map.get(abbr)

    def _find_book_id_by_full_name(self, name: str) -> Optional[int]:
        """
        Находит ID книги по полному русскому названию

        Args:
            name: Полное название книги (например, "Матфея", "Галатам")

        Returns:
            ID книги или None
        """
        # Словарь соответствий полных названий (совпадает с нумерацией bible_data.py)
        full_name_map = {
            # Ветхий Завет
            'Бытие': 1, 'Исход': 2, 'Левит': 3, 'Числа': 4, 'Второзаконие': 5,
            'Иисуса Навина': 6, 'Судей': 7, 'Руфь': 8,
            '1 Царств': 9, '2 Царств': 10, '3 Царств': 11, '4 Царств': 12,
            '1 Паралипоменон': 13, '2 Паралипоменон': 14, 'Ездры': 15, 'Неемии': 16, 'Есфирь': 17,
            'Иова': 18, 'Псалтирь': 19, 'Притчи': 20, 'Екклесиаст': 21, 'Песнь Песней': 22,
            'Исаии': 23, 'Иеремии': 24, 'Плач Иеремии': 25, 'Иезекииля': 26, 'Даниила': 27,
            'Осии': 28, 'Иоиля': 29, 'Амоса': 30, 'Авдия': 31, 'Ионы': 32,
            'Михея': 33, 'Наума': 34, 'Аввакума': 35, 'Софонии': 36, 'Аггея': 37,
            'Захарии': 38, 'Малахии': 39,
            # Новый Завет (порядок как в bible_data.py)
            'Матфея': 40, 'Марка': 41, 'Луки': 42, 'Иоанна': 43, 'Деяния': 44,
            'Иакова': 45, '1 Петра': 46, '2 Петра': 47, '1 Иоанна': 48, '2 Иоанна': 49,
            '3 Иоанна': 50, 'Иуды': 51, 'Римлянам': 52, '1 Коринфянам': 53, '2 Коринфянам': 54,
            'Галатам': 55, 'Ефесянам': 56, 'Филиппийцам': 57, 'Колоссянам': 58, '1 Фессалоникийцам': 59,
            '2 Фессалоникийцам': 60, '1 Тимофею': 61, '2 Тимофею': 62, 'Титу': 63, 'Филимону': 64,
            'Евреям': 65, 'Откровение': 66
        }

        return full_name_map.get(name)

    def _parse_scripture_references(self, scripture_readings: List[str]) -> List[Dict[str, Any]]:
        """
        Парсит чтения и извлекает ссылки на книги Библии
        Поддерживает сложные ссылки вида "Матфея 18:18-22; 19:1-2, 13-15"

        Args:
            scripture_readings: Список строк с чтениями

        Returns:
            Список словарей с данными ссылок для кнопок
        """
        references = []

        # Импортируем bible_data для получения ID книг
        from utils.bible_data import bible_data

        for reading in scripture_readings:
            if not reading.strip():
                continue

            # Удаляем комментарии в скобках
            clean_reading = re.sub(r'\s*\([^)]*\)', '', reading.strip())

            logger.info(f"Парсинг сложного чтения: '{clean_reading}'")

            # Парсим сложные ссылки с точкой с запятой
            parts = self._parse_complex_scripture_reference(clean_reading)

            for part in parts:
                book_name = part['book_name']
                chapter = part['chapter']
                verse_start = part['verse_start']
                verse_end = part['verse_end']

                # Получаем ID книги через bible_data
                book_abbr = bible_data.normalize_book_name(book_name)
                book_id = bible_data.get_book_id(book_abbr)
                logger.info(
                    f"Парсинг части: '{book_name}' {chapter}:{verse_start}-{verse_end} -> '{book_abbr}' -> ID {book_id}")

                if book_id:
                    # Обычная логика отображения
                    if verse_start != verse_end:
                        display_text = f"{book_name} {chapter}:{verse_start}-{verse_end}"
                    else:
                        display_text = f"{book_name} {chapter}:{verse_start}"
                    references.append({
                        'book_id': book_id,
                        'book_name': book_name,
                        'chapter': chapter,
                        'verse_start': verse_start,
                        'verse_end': verse_end,
                        'display_text': display_text,
                        'full_text': reading,  # Сохраняем оригинальный текст с комментариями
                        'is_complex': len(parts) > 1  # Флаг сложной ссылки
                    })
                    logger.info(
                        f"Добавлена ссылка: {display_text} (ID: {book_id})")
                else:
                    logger.warning(f"Не найден ID для книги: {book_name}")

        return references

    def _parse_complex_scripture_reference(self, reference: str) -> List[Dict[str, Any]]:
        """
        Парсит сложную ссылку вида "Матфея 18:18-22; 19:1-2, 13-15"

        Returns:
            Список частей с book_name, chapter, verse_start, verse_end
        """
        parts = []

        # Сначала извлекаем название книги
        # Ищем номер главы, чтобы отделить название книги
        book_match = re.match(r'^(.+?)\s+(\d+[:\.]\d+.*)', reference)
        if not book_match:
            logger.warning(
                f"Не удалось извлечь название книги из: {reference}")
            return parts

        book_name = book_match.group(1).strip()
        rest = book_match.group(2).strip()

        logger.info(f"Книга: '{book_name}', остальная часть: '{rest}'")

        # Разделяем по точке с запятой (разные главы)
        chapter_parts = rest.split(';')

        for chapter_part in chapter_parts:
            chapter_part = chapter_part.strip()
            logger.info(f"Обрабатываем часть главы: '{chapter_part}'")

            # Парсим главу и стихи
            chapter_match = re.match(r'^(\d+):(.+)', chapter_part)
            if chapter_match:
                chapter = int(chapter_match.group(1))
                verses_part = chapter_match.group(2).strip()

                # Разделяем стихи по запятой
                verse_ranges = verses_part.split(',')

                for verse_range in verse_ranges:
                    verse_range = verse_range.strip()
                    logger.info(
                        f"Обрабатываем диапазон стихов: '{verse_range}'")

                    # Парсим диапазон стихов
                    try:
                        if '-' in verse_range:
                            verse_parts = verse_range.split('-')
                            if len(verse_parts) == 2:
                                # Проверяем формат глава:стих
                                start_part = verse_parts[0].strip()
                                end_part = verse_parts[1].strip()

                                if ':' in start_part:
                                    # Формат "глава:стих-стих" или "глава:стих-глава:стих"
                                    chapter_verse = start_part.split(':')
                                    chapter = int(chapter_verse[0])
                                    verse_start = int(chapter_verse[1])

                                    if ':' in end_part:
                                        # Переход между главами: "15:17-16:2"
                                        end_chapter_verse = end_part.split(':')
                                        end_chapter = int(end_chapter_verse[0])
                                        end_verse = int(end_chapter_verse[1])

                                        # Добавляем первую часть (15:17 до конца главы)
                                        last_verse = get_last_verse_in_chapter(
                                            book_name, chapter)
                                        parts.append({
                                            'book_name': book_name,
                                            'chapter': chapter,
                                            'verse_start': verse_start,
                                            'verse_end': last_verse  # До конца главы
                                        })

                                        # Добавляем вторую часть (начало новой главы до end_verse)
                                        parts.append({
                                            'book_name': book_name,
                                            'chapter': end_chapter,
                                            'verse_start': 1,
                                            'verse_end': end_verse
                                        })
                                        continue  # Пропускаем добавление в конце цикла
                                    else:
                                        # Обычный формат "глава:стих-стих"
                                        verse_end = int(end_part)
                                else:
                                    # Проверяем, есть ли в end_part двоеточие (межглавный переход)
                                    if ':' in end_part:
                                        # Формат "стих-глава:стих" (например "4-14:5")
                                        end_chapter_verse = end_part.split(':')
                                        end_chapter = int(end_chapter_verse[0])
                                        end_verse = int(end_chapter_verse[1])

                                        # Добавляем первую часть (от start_part до конца текущей главы)
                                        last_verse = get_last_verse_in_chapter(
                                            book_name, chapter)
                                        parts.append({
                                            'book_name': book_name,
                                            'chapter': chapter,
                                            'verse_start': int(start_part),
                                            'verse_end': last_verse  # До конца главы
                                        })

                                        # Добавляем вторую часть (начало новой главы до end_verse)
                                        parts.append({
                                            'book_name': book_name,
                                            'chapter': end_chapter,
                                            'verse_start': 1,
                                            'verse_end': end_verse
                                        })
                                        continue  # Пропускаем добавление в конце цикла
                                    else:
                                        # Обычный формат "стих-стих"
                                        verse_start = int(start_part)
                                        verse_end = int(end_part)
                            else:
                                verse_start = verse_end = int(verse_range)
                        else:
                            # Одиночный стих
                            if ':' in verse_range:
                                # Формат "глава:стих"
                                chapter_verse = verse_range.split(':')
                                chapter = int(chapter_verse[0])
                                verse_start = verse_end = int(chapter_verse[1])
                            else:
                                # Просто номер стиха
                                verse_start = verse_end = int(verse_range)
                    except ValueError as e:
                        logger.warning(
                            f"Не удалось распарсить диапазон стихов '{verse_range}': {e}")
                        continue

                    parts.append({
                        'book_name': book_name,
                        'chapter': chapter,
                        'verse_start': verse_start,
                        'verse_end': verse_end
                    })
                    logger.info(
                        f"Добавлена часть: {book_name} {chapter}:{verse_start}-{verse_end}")
            else:
                logger.warning(
                    f"Не удалось распарсить часть главы: {chapter_part}")

        return parts


# Глобальный экземпляр календаря
orthodox_calendar = OrthodoxyCalendar()
