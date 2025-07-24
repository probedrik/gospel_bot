"""
Служба для работы с планами чтения Библии из Supabase.
Альтернатива CSV-загрузке для случаев, когда данные хранятся в Supabase.
"""
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


class SupabaseReadingPlansService:
    """Служба для работы с планами чтения из Supabase"""

    def __init__(self, db_manager=None):
        """
        Инициализирует службу планов чтения с Supabase

        Args:
            db_manager: менеджер базы данных (должен поддерживать методы планов чтения)
        """
        self.db_manager = db_manager
        self.plans: Dict[str, ReadingPlan] = {}
        self._plans_loaded = False

    async def _load_plans(self) -> None:
        """Загружает все планы из Supabase"""
        if not self.db_manager:
            logger.error("Менеджер базы данных не инициализирован")
            return

        if self._plans_loaded:
            return  # Уже загружены

        try:
            # Получаем все планы из базы данных
            plans_data = await self.db_manager.get_reading_plans()
            logger.info(f"Получено {len(plans_data)} планов из Supabase")
            logger.debug(f"Данные планов: {plans_data}")

            for plan_data in plans_data:
                logger.info(f"🔄 Обрабатываем план: {plan_data}")

                plan_id = plan_data.get('plan_id', plan_data.get('id'))
                title = plan_data.get(
                    'title', plan_data.get('name', f'План {plan_id}'))

                logger.info(f"📋 План: ID='{plan_id}', title='{title}'")

                # Получаем дни плана
                days_data = await self.db_manager.get_reading_plan_days(plan_id)
                logger.info(
                    f"📅 Получено {len(days_data)} дней для плана {plan_id}")
                logger.debug(
                    f"Первые 3 дня: {days_data[:3] if days_data else 'нет данных'}")

                days = []
                for day_data in days_data:
                    logger.debug(f"🔍 Обрабатываем день: {day_data}")

                    # Проверяем разные возможные названия полей
                    day_number = day_data.get(
                        'day_number', day_data.get('day'))
                    reading = day_data.get('reading', day_data.get(
                        'reading_text', day_data.get('text', '')))

                    logger.debug(
                        f"   день: {day_number}, чтение: '{reading[:50]}...' (длина: {len(reading) if reading else 0})")

                    if day_number and reading:
                        days.append((day_number, reading))
                        logger.debug(f"   ✅ День {day_number} добавлен")
                    else:
                        logger.warning(
                            f"   ❌ День пропущен: day_number={day_number}, reading='{reading[:20]}...'")

                logger.info(
                    f"📊 Всего дней обработано для плана {plan_id}: {len(days)}")

                if days:
                    # Сортируем дни по номеру
                    days.sort(key=lambda x: x[0])

                    plan = ReadingPlan(
                        plan_id=plan_id,
                        title=title,
                        days=days,
                        total_days=len(days)
                    )

                    self.plans[plan_id] = plan
                    logger.info(
                        f"✅ Загружен план из Supabase: {title} ({len(days)} дней)")
                else:
                    logger.warning(
                        f"⚠️ План {plan_id} пропущен - нет валидных дней")

            self._plans_loaded = True
            logger.info(
                f"📈 Всего загружено планов из Supabase: {len(self.plans)}")
            logger.info(f"📋 Планы в памяти: {list(self.plans.keys())}")

        except Exception as e:
            logger.error(f"Ошибка при загрузке планов из Supabase: {e}")
            import traceback
            logger.error(f"Трассировка: {traceback.format_exc()}")

    async def get_all_plans(self) -> List[ReadingPlan]:
        """Возвращает список всех доступных планов"""
        await self._load_plans()
        return list(self.plans.values())

    async def get_plan(self, plan_id: str) -> Optional[ReadingPlan]:
        """
        Возвращает план по ID

        Args:
            plan_id: идентификатор плана

        Returns:
            Объект ReadingPlan или None если план не найден
        """
        await self._load_plans()
        return self.plans.get(plan_id)

    async def get_plan_day(self, plan_id: str, day: int) -> Optional[str]:
        """
        Возвращает чтение для конкретного дня плана

        Args:
            plan_id: идентификатор плана
            day: номер дня

        Returns:
            Строка с чтением или None если не найдено
        """
        plan = await self.get_plan(plan_id)
        if not plan:
            return None

        for plan_day, reading in plan.days:
            if plan_day == day:
                return reading

        return None

    async def get_next_day(self, plan_id: str, current_day: int) -> Optional[int]:
        """
        Возвращает номер следующего дня в плане

        Args:
            plan_id: идентификатор плана
            current_day: текущий день

        Returns:
            Номер следующего дня или None если это последний день
        """
        plan = await self.get_plan(plan_id)
        if not plan:
            return None

        # Находим текущий день в списке и возвращаем следующий
        for i, (day, _) in enumerate(plan.days):
            if day == current_day and i + 1 < len(plan.days):
                return plan.days[i + 1][0]

        return None

    async def get_previous_day(self, plan_id: str, current_day: int) -> Optional[int]:
        """
        Возвращает номер предыдущего дня в плане

        Args:
            plan_id: идентификатор плана
            current_day: текущий день

        Returns:
            Номер предыдущего дня или None если это первый день
        """
        plan = await self.get_plan(plan_id)
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

    async def reload_plans(self):
        """Принудительно перезагружает планы из Supabase"""
        self._plans_loaded = False
        self.plans.clear()
        await self._load_plans()

    def get_all_plans_sync(self) -> List[dict]:
        """Синхронный метод для получения всех планов (для совместимости)"""
        import asyncio

        # Инициализируем менеджер БД если нужно
        if not self.db_manager:
            try:
                from database.universal_manager import universal_db_manager
                self.db_manager = universal_db_manager
                logger.info(
                    "🔧 Инициализирован universal_db_manager для Supabase сервиса")
            except ImportError as e:
                logger.error(f"Не удалось импортировать менеджер БД: {e}")
                return []

        try:
            # Запускаем асинхронную загрузку планов
            if asyncio.get_event_loop().is_running():
                # Если мы уже в асинхронном контексте
                logger.warning(
                    "Попытка синхронного вызова в асинхронном контексте")
                if not self._plans_loaded:
                    logger.warning(
                        "Планы не загружены, возвращаем пустой список")
                    return []
            else:
                # Создаем новый event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(self._load_plans())
                finally:
                    loop.close()

            # Возвращаем планы в формате dict
            plans_list = []
            for plan in self.plans.values():
                plans_list.append({
                    'plan_id': plan.plan_id,
                    'title': plan.title,
                    'total_days': plan.total_days
                })

            logger.info(
                f"🔄 Возвращено {len(plans_list)} планов из Supabase (синхронный метод)")
            return plans_list

        except Exception as e:
            logger.error(f"Ошибка получения планов из Supabase: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []

    def get_plan_days_sync(self, plan_id: str) -> List[dict]:
        """Синхронный метод для получения дней плана (для совместимости)"""
        plan = self.plans.get(plan_id)
        if not plan:
            return []

        days_list = []
        for day_num, reading_text in plan.days:
            days_list.append({
                'day': day_num,
                'reading_text': reading_text
            })

        return days_list


# Функция для создания экземпляра службы
async def create_supabase_reading_plans_service(db_manager):
    """
    Создает и инициализирует службу планов чтения из Supabase

    Args:
        db_manager: менеджер базы данных

    Returns:
        Инициализированный SupabaseReadingPlansService
    """
    service = SupabaseReadingPlansService(db_manager)
    await service._load_plans()
    return service
