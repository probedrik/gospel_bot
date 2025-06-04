# coding: utf-8
"""
Модуль для хранения и парсинга планов чтения Библии из текстовых файлов.
"""
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import csv
import os


class ReadingPlan:
    """Класс для работы с планами чтения Библии."""

    def __init__(self, csv_file_path: str):
        """
        Инициализация плана чтения из CSV файла.

        Args:
            csv_file_path: Путь к CSV файлу с планом
        """
        self.csv_file_path = csv_file_path
        self.title = ""
        self.days = {}
        self._load_plan()

    def _load_plan(self):
        """Загружает план чтения из CSV файла."""
        try:
            with open(self.csv_file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)

                # Читаем заголовок
                header_row = next(reader)
                if len(header_row) >= 2 and header_row[0] == 'plan_title':
                    self.title = header_row[1]

                # Пропускаем строку с названиями колонок
                next(reader)

                # Читаем дни
                for row in reader:
                    if len(row) >= 2:
                        try:
                            day = int(row[0])
                            reading = row[1]
                            self.days[day] = reading
                        except ValueError:
                            continue

        except Exception as e:
            print(f"Ошибка при загрузке плана {self.csv_file_path}: {e}")

    def get_day_reading(self, day: int) -> Optional[str]:
        """
        Получает чтение для указанного дня.

        Args:
            day: Номер дня

        Returns:
            Строка с чтением или None, если день не найден
        """
        return self.days.get(day)

    def get_total_days(self) -> int:
        """Возвращает общее количество дней в плане."""
        return len(self.days)

    def get_title(self) -> str:
        """Возвращает название плана."""
        return self.title


class ReadingPlansManager:
    """Менеджер для работы с планами чтения."""

    def __init__(self, plans_directory: str = "data/plans_csv_final"):
        """
        Инициализация менеджера планов.

        Args:
            plans_directory: Директория с CSV файлами планов
        """
        self.plans_directory = Path(plans_directory)
        self.plans = {}
        self.short_id_to_full_id = {}  # Маппинг коротких ID к полным
        self.full_id_to_short_id = {}  # Маппинг полных ID к коротким
        self._load_all_plans()

    def _load_all_plans(self):
        """Загружает все планы из директории."""
        if not self.plans_directory.exists():
            print(f"Директория планов {self.plans_directory} не найдена")
            return

        csv_files = list(self.plans_directory.glob("*.csv"))

        for i, csv_file in enumerate(csv_files):
            full_plan_id = csv_file.stem
            short_plan_id = f"plan_{i+1}"  # Короткий ID: plan_1, plan_2, etc.

            plan = ReadingPlan(str(csv_file))

            if plan.title:  # Если план успешно загружен
                self.plans[short_plan_id] = plan
                self.short_id_to_full_id[short_plan_id] = full_plan_id
                self.full_id_to_short_id[full_plan_id] = short_plan_id
                print(
                    f"Загружен план: {plan.title} ({plan.get_total_days()} дней) [ID: {short_plan_id}]")

    def get_plan(self, plan_id: str) -> Optional[ReadingPlan]:
        """
        Получает план по ID (поддерживает как короткие, так и полные ID).

        Args:
            plan_id: Идентификатор плана (короткий или полный)

        Returns:
            Объект ReadingPlan или None
        """
        # Сначала пробуем как короткий ID
        if plan_id in self.plans:
            return self.plans[plan_id]

        # Если не найден, пробуем как полный ID
        short_id = self.full_id_to_short_id.get(plan_id)
        if short_id:
            return self.plans.get(short_id)

        return None

    def get_all_plans(self) -> Dict[str, ReadingPlan]:
        """Возвращает все доступные планы."""
        return self.plans

    def get_plans_list(self) -> List[Dict[str, str]]:
        """
        Возвращает список планов для отображения в меню.

        Returns:
            Список словарей с информацией о планах (с короткими ID)
        """
        plans_list = []
        for short_id, plan in self.plans.items():
            plans_list.append({
                'id': short_id,  # Используем короткий ID
                'title': plan.title,
                'days': plan.get_total_days()
            })
        return plans_list


# Глобальный экземпляр менеджера планов
reading_plans_manager = ReadingPlansManager()


def get_reading_plans():
    """Возвращает список всех планов чтения."""
    return reading_plans_manager.get_plans_list()


def get_plan_reading(plan_id: str, day: int) -> Optional[str]:
    """
    Получает чтение для указанного дня из плана.

    Args:
        plan_id: Идентификатор плана
        day: Номер дня

    Returns:
        Строка с чтением или None
    """
    plan = reading_plans_manager.get_plan(plan_id)
    if plan:
        return plan.get_day_reading(day)
    return None


def get_plan_title(plan_id: str) -> Optional[str]:
    """
    Получает название плана.

    Args:
        plan_id: Идентификатор плана

    Returns:
        Название плана или None
    """
    plan = reading_plans_manager.get_plan(plan_id)
    if plan:
        return plan.get_title()
    return None


def get_plan_total_days(plan_id: str) -> int:
    """
    Получает общее количество дней в плане.

    Args:
        plan_id: Идентификатор плана

    Returns:
        Количество дней или 0
    """
    plan = reading_plans_manager.get_plan(plan_id)
    if plan:
        return plan.get_total_days()
    return 0
