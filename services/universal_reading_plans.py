"""
Универсальная служба для работы с планами чтения Библии.
Автоматически определяет доступный источник данных (CSV или Supabase).
"""
import csv
import os
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ReadingPlan:
    """Класс для представления плана чтения"""
    plan_id: str
    title: str
    days: List[Tuple[int, str]]  # (день, чтение)
    total_days: int


class UniversalReadingPlansService:
    """Универсальная служба для работы с планами чтения"""

    def __init__(self, plans_directory: str = "data/plans_csv_final"):
        """
        Инициализирует службу планов чтения

        Args:
            plans_directory: путь к папке с CSV файлами планов
        """
        self.plans_directory = plans_directory
        self.plans: Dict[str, ReadingPlan] = {}
        self.supabase_service = None
        self.db_manager = None
        self._load_plans()

    def _load_plans(self) -> None:
        """Загружает планы из доступных источников"""

        # Проверяем конфигурацию Supabase планов
        config_file = "data/supabase_plans.conf"
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if "USE_SUPABASE_PLANS=true" in content:
                        logger.info(
                            "🔄 Конфигурация указывает использовать Supabase планы")
                        if self._load_from_supabase():
                            logger.info("✅ Планы загружены из Supabase")
                            return
                        else:
                            logger.warning(
                                "⚠️ Не удалось загрузить из Supabase, переходим к fallback")
            except Exception as e:
                logger.error(f"Ошибка чтения конфигурации: {e}")

        # Сначала пытаемся загрузить из CSV
        if self._load_from_csv():
            logger.info("✅ Планы загружены из CSV файлов")
            return

        # Если CSV нет, пытаемся загрузить из резервной копии
        backup_dir = "data/plans_csv_backup"
        if os.path.exists(backup_dir):
            logger.info(f"🔄 Загружаем планы из резервной копии: {backup_dir}")
            if self._load_from_csv_directory(backup_dir):
                logger.info("✅ Планы загружены из резервной копии")
                return

        # Если ничего не помогло, пытаемся Supabase
        if self._load_from_supabase():
            logger.info("✅ Планы загружены из Supabase (fallback)")
            return

        # Если и резервная копия недоступна, создаем минимальные планы-заглушки
        logger.warning("⚠️ Все источники планов недоступны, создаем заглушки")
        self._create_fallback_plans()

    def _load_from_csv(self) -> bool:
        """Загружает планы из основной CSV директории"""
        if not os.path.exists(self.plans_directory):
            logger.error(f"Папка с планами не найдена: {self.plans_directory}")
            return False

        return self._load_from_csv_directory(self.plans_directory)

    def _load_from_csv_directory(self, directory: str) -> bool:
        """Загружает планы из указанной CSV директории"""
        plans_loaded = 0

        for filename in os.listdir(directory):
            if filename.endswith('.csv'):
                plan_path = os.path.join(directory, filename)
                try:
                    plan = self._load_plan_from_csv(plan_path, filename)
                    if plan:
                        self.plans[plan.plan_id] = plan
                        logger.info(
                            f"Загружен план: {plan.title} ({plan.total_days} дней)")
                        plans_loaded += 1
                except Exception as e:
                    logger.error(f"Ошибка при загрузке плана {filename}: {e}")

        return plans_loaded > 0

    def _load_plan_from_csv(self, file_path: str, filename: str) -> Optional[ReadingPlan]:
        """
        Загружает план чтения из CSV файла

        Args:
            file_path: путь к CSV файлу
            filename: имя файла для создания ID

        Returns:
            Объект ReadingPlan или None при ошибке
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()

                if len(lines) < 3:  # Минимум: название, заголовки, одна строка данных
                    logger.warning(
                        f"Файл {filename} содержит слишком мало строк")
                    return None

                # Первая строка: plan_title,Название плана
                first_line = lines[0].strip()
                if ',' in first_line:
                    plan_title = first_line.split(',', 1)[1].strip()
                else:
                    plan_title = filename.replace('.csv', '')

                # Создаем короткий ID плана (обратная совместимость со старыми ID)
                if 'Евангелие' in filename:
                    plan_id = 'plan1'  # gospel_daily
                elif 'Классический' in filename:
                    plan_id = 'plan2'  # classic_year
                elif 'ВЗ-и-НЗ' in filename or 'ВЗ_и_НЗ' in filename:
                    plan_id = 'plan3'  # ot_nt_plan
                else:
                    # Fallback для других файлов
                    plan_id = filename.replace('.csv', '').replace(
                        ' ', '_').replace('-', '_')[:20]

                # Вторая строка должна быть заголовками: day,reading
                headers_line = lines[1].strip()
                if not headers_line.startswith('day,reading'):
                    logger.warning(
                        f"Неожиданные заголовки в файле {filename}: {headers_line}")

                days = []

                # Читаем остальные строки с данными
                for i, line in enumerate(lines[2:], start=3):
                    line = line.strip()
                    if not line:  # Пропускаем пустые строки
                        continue

                    if ',' in line:
                        parts = line.split(',', 1)
                        if len(parts) == 2:
                            try:
                                day = int(parts[0].strip())
                                reading = parts[1].strip()
                                if reading:  # Пропускаем строки с пустым чтением
                                    days.append((day, reading))
                            except ValueError as e:
                                logger.warning(
                                    f"Некорректный номер дня в строке {i} файла {filename}: {parts[0]}")

                if not days:
                    logger.warning(
                        f"Не найдено дней чтения в файле {filename}")
                    return None

                logger.info(
                    f"Загружен план '{plan_title}' с {len(days)} днями из файла {filename}")

                return ReadingPlan(
                    plan_id=plan_id,
                    title=plan_title,
                    days=days,
                    total_days=len(days)
                )

        except Exception as e:
            logger.error(f"Ошибка при чтении файла {file_path}: {e}")
            return None

    def _create_fallback_plans(self) -> None:
        """Создает минимальные планы-заглушки когда основные источники недоступны"""
        fallback_plans = [
            {
                'plan_id': 'plan1',
                'title': '📖 Евангелие на каждый день (недоступно)',
                'days': [(1, "Мф 1"), (2, "Мф 2")]  # Минимальные данные
            },
            {
                'plan_id': 'plan2',
                'title': '📚 Классический план за 1 год (недоступно)',
                'days': [(1, "Быт 1; Мф 1"), (2, "Быт 2; Мф 2")]
            },
            {
                'plan_id': 'plan3',
                'title': '📜 План ВЗ и НЗ (недоступно)',
                'days': [(1, "Быт 1; Мф 1"), (2, "Быт 2; Мф 2")]
            }
        ]

        for plan_data in fallback_plans:
            plan = ReadingPlan(
                plan_id=plan_data['plan_id'],
                title=plan_data['title'],
                days=plan_data['days'],
                total_days=len(plan_data['days'])
            )
            self.plans[plan.plan_id] = plan
            logger.info(f"Создан план-заглушка: {plan.title}")

    def get_all_plans(self) -> List[ReadingPlan]:
        """Возвращает список всех доступных планов"""
        return list(self.plans.values())

    def get_plan(self, plan_id: str) -> Optional[ReadingPlan]:
        """
        Возвращает план по ID

        Args:
            plan_id: идентификатор плана

        Returns:
            Объект ReadingPlan или None если план не найден
        """
        return self.plans.get(plan_id)

    def get_plan_day(self, plan_id: str, day: int) -> Optional[str]:
        """
        Возвращает чтение для конкретного дня плана

        Args:
            plan_id: идентификатор плана
            day: номер дня

        Returns:
            Строка с чтением или None если не найдено
        """
        plan = self.get_plan(plan_id)
        if not plan:
            return None

        for plan_day, reading in plan.days:
            if plan_day == day:
                return reading

        return None

    def get_next_day(self, plan_id: str, current_day: int) -> Optional[int]:
        """
        Возвращает номер следующего дня в плане

        Args:
            plan_id: идентификатор плана
            current_day: текущий день

        Returns:
            Номер следующего дня или None если это последний день
        """
        plan = self.get_plan(plan_id)
        if not plan:
            return None

        # Находим текущий день в списке и возвращаем следующий
        for i, (day, _) in enumerate(plan.days):
            if day == current_day and i + 1 < len(plan.days):
                return plan.days[i + 1][0]

        return None

    def get_previous_day(self, plan_id: str, current_day: int) -> Optional[int]:
        """
        Возвращает номер предыдущего дня в плане

        Args:
            plan_id: идентификатор плана
            current_day: текущий день

        Returns:
            Номер предыдущего дня или None если это первый день
        """
        plan = self.get_plan(plan_id)
        if not plan:
            return None

        # Находим текущий день в списке и возвращаем предыдущий
        for i, (day, _) in enumerate(plan.days):
            if day == current_day and i > 0:
                return plan.days[i - 1][0]

        return None

    def parse_reading_references(self, reading: str) -> List[str]:
        """
        Парсит строку чтения и возвращает список отдельных ссылок

        Args:
            reading: строка чтения (например, "Мф 1; Мф 2")

        Returns:
            Список ссылок
        """
        # Разделяем по точке с запятой и очищаем пробелы
        references = [ref.strip() for ref in reading.split(';') if ref.strip()]
        return references

    def _load_from_supabase(self) -> bool:
        """Загружает планы из Supabase"""
        try:
            # Инициализируем Supabase сервис если нужно
            if not self.supabase_service:
                try:
                    from services.supabase_reading_plans import SupabaseReadingPlansService
                    self.supabase_service = SupabaseReadingPlansService()
                except ImportError as e:
                    logger.error(
                        f"Не удалось импортировать Supabase сервис: {e}")
                    return False

            # Получаем планы из Supabase
            supabase_plans = self.supabase_service.get_all_plans_sync()
            if not supabase_plans:
                logger.warning("Планы из Supabase не найдены")
                return False

            # Конвертируем в формат ReadingPlan
            plans_loaded = 0
            for plan_data in supabase_plans:
                try:
                    plan = self._convert_supabase_plan(plan_data)
                    if plan:
                        self.plans[plan.plan_id] = plan
                        logger.info(
                            f"Загружен план из Supabase: {plan.title} ({plan.total_days} дней)")
                        plans_loaded += 1
                except Exception as e:
                    logger.error(f"Ошибка конвертации плана из Supabase: {e}")

            return plans_loaded > 0

        except Exception as e:
            logger.error(f"Ошибка загрузки планов из Supabase: {e}")
            return False

    def _convert_supabase_plan(self, plan_data: dict) -> Optional[ReadingPlan]:
        """Конвертирует план из Supabase в ReadingPlan"""
        try:
            plan_id = plan_data.get('plan_id')
            title = plan_data.get('title', 'Неизвестный план')
            total_days = plan_data.get('total_days', 0)

            # Получаем дни плана
            days_data = self.supabase_service.get_plan_days_sync(plan_id)
            days = []

            for day_data in days_data:
                day_num = day_data.get('day')
                reading_text = day_data.get('reading_text', '')
                if day_num and reading_text:
                    days.append((day_num, reading_text))

            # Сортируем дни по порядку
            days.sort(key=lambda x: x[0])

            return ReadingPlan(
                plan_id=plan_id,
                title=title,
                days=days,
                total_days=len(days)  # Используем реальное количество дней
            )

        except Exception as e:
            logger.error(f"Ошибка конвертации плана {plan_data}: {e}")
            return None

    def _init_db_manager(self):
        """Инициализирует менеджер БД если нужно"""
        if not self.db_manager:
            try:
                from database.universal_manager import universal_db_manager
                self.db_manager = universal_db_manager
            except ImportError as e:
                logger.error(f"Не удалось импортировать менеджер БД: {e}")


# Создаем глобальный экземпляр универсальной службы
universal_reading_plans_service = UniversalReadingPlansService()
