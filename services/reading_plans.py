"""
Служба для работы с планами чтения Библии.
Загружает планы из CSV файлов и предоставляет API для работы с ними.
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


class ReadingPlansService:
    """Служба для работы с планами чтения"""

    def __init__(self, plans_directory: str = "data/plans_csv_final"):
        """
        Инициализирует службу планов чтения

        Args:
            plans_directory: путь к папке с CSV файлами планов
        """
        self.plans_directory = plans_directory
        self.plans: Dict[str, ReadingPlan] = {}
        self._load_plans()

    def _load_plans(self) -> None:
        """Загружает все планы из CSV файлов"""
        if not os.path.exists(self.plans_directory):
            logger.error(f"Папка с планами не найдена: {self.plans_directory}")
            logger.info("💡 Попробуйте переключиться на планы из Supabase:")
            logger.info("   python switch_to_supabase_plans.py")
            logger.info("💡 Или восстановите CSV планы:")
            logger.info(
                "   mv data/plans_csv_final_disabled data/plans_csv_final")

            # Пытаемся загрузить планы из резервной копии
            backup_dir = "data/plans_csv_backup"
            if os.path.exists(backup_dir):
                logger.info(
                    f"🔄 Пытаемся загрузить планы из резервной копии: {backup_dir}")
                self._load_from_directory(backup_dir)
            return

        self._load_from_directory(self.plans_directory)

    def _load_from_directory(self, directory: str) -> None:
        """Загружает планы из указанной директории"""
        for filename in os.listdir(directory):
            if filename.endswith('.csv'):
                plan_path = os.path.join(directory, filename)
                try:
                    plan = self._load_plan_from_csv(plan_path, filename)
                    if plan:
                        self.plans[plan.plan_id] = plan
                        logger.info(
                            f"Загружен план: {plan.title} ({plan.total_days} дней)")
                except Exception as e:
                    logger.error(f"Ошибка при загрузке плана {filename}: {e}")

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


# Создаем глобальный экземпляр службы
# ПРИМЕЧАНИЕ: Теперь используется универсальная служба с fallback логикой
try:
    from services.universal_reading_plans import universal_reading_plans_service
    reading_plans_service = universal_reading_plans_service
    logger.info(
        "🔄 Используется универсальная служба планов чтения с fallback логикой")
except ImportError:
    # Fallback на обычную службу
    reading_plans_service = ReadingPlansService()
    logger.warning("⚠️ Используется обычная служба планов чтения")
