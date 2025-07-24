"""
Модуль для управления базой данных через Supabase Python SDK.
Отвечает за хранение информации о пользователях, закладках и планах чтения.
"""
import logging
from datetime import datetime, date
from typing import List, Tuple, Optional, Dict, Any
import os
from supabase import create_client, Client

# Инициализация логгера
logger = logging.getLogger(__name__)


class SupabaseManager:
    """Класс для управления базой данных через Supabase SDK"""

    def __init__(self, url: str = None, key: str = None):
        """
        Инициализирует менеджер базы данных Supabase.

        Args:
            url: URL Supabase проекта
            key: API ключ Supabase
        """
        # Получаем параметры подключения из переменных окружения
        self.url = url or os.getenv('SUPABASE_URL')
        self.key = key or os.getenv('SUPABASE_KEY')

        if not self.url or not self.key:
            raise ValueError(
                "SUPABASE_URL и SUPABASE_KEY должны быть установлены")

        # Создаем клиент Supabase
        self.client: Client = create_client(self.url, self.key)

        logger.info(f"Инициализация Supabase: {self.url}")

    async def initialize(self):
        """Инициализирует подключение (для совместимости с интерфейсом)"""
        try:
            # Проверяем подключение простым запросом
            result = self.client.table('users').select(
                'count', count='exact').execute()
            logger.info("Supabase подключение успешно инициализировано")
        except Exception as e:
            logger.error(f"Ошибка инициализации Supabase: {e}", exc_info=True)
            raise

    async def close(self):
        """Закрывает соединение (для совместимости с интерфейсом)"""
        # Supabase SDK не требует явного закрытия соединений
        logger.info("Supabase соединение закрыто")

    # === МЕТОДЫ ДЛЯ РАБОТЫ С ПОЛЬЗОВАТЕЛЯМИ ===

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получает пользователя из базы данных"""
        try:
            result = self.client.table('users').select(
                '*').eq('user_id', user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Ошибка получения пользователя {user_id}: {e}")
            return None

    async def add_user(self, user_id: int, username: str, first_name: str) -> bool:
        """Добавляет пользователя в базу данных"""
        try:
            data = {
                'user_id': user_id,
                'username': username or '',
                'first_name': first_name or '',
                'translation': 'rst',
                'created_at': datetime.now().isoformat(),
                'last_activity': datetime.now().isoformat()
            }

            # Используем upsert для избежания конфликтов
            result = self.client.table('users').upsert(data).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Ошибка добавления пользователя {user_id}: {e}")
            return False

    async def update_user_translation(self, user_id: int, translation: str) -> bool:
        """Обновляет перевод пользователя"""
        try:
            result = self.client.table('users').update({
                'translation': translation
            }).eq('user_id', user_id).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(
                f"Ошибка обновления перевода для пользователя {user_id}: {e}")
            return False

    async def update_user_activity(self, user_id: int) -> bool:
        """Обновляет время последней активности пользователя"""
        try:
            result = self.client.table('users').update({
                'last_activity': datetime.now().isoformat()
            }).eq('user_id', user_id).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(
                f"Ошибка обновления активности для пользователя {user_id}: {e}")
            return False

    # === МЕТОДЫ ДЛЯ РАБОТЫ С ЗАКЛАДКАМИ ===

    async def get_bookmarks(self, user_id: int) -> List[Dict[str, Any]]:
        """Получает закладки пользователя"""
        try:
            result = self.client.table('bookmarks').select(
                '*').eq('user_id', user_id).order('created_at', desc=True).execute()
            return result.data
        except Exception as e:
            logger.error(
                f"Ошибка получения закладок для пользователя {user_id}: {e}")
            return []

    async def add_bookmark(self, user_id: int, book_id: int, chapter: int,
                           display_text: str, verse_start: int = None,
                           verse_end: int = None, note: str = None) -> bool:
        """Добавляет закладку"""
        try:
            data = {
                'user_id': user_id,
                'book_id': book_id,
                'chapter': chapter,
                'verse_start': verse_start,
                'verse_end': verse_end,
                'display_text': display_text,
                'note': note,
                'created_at': datetime.now().isoformat()
            }

            result = self.client.table('bookmarks').insert(data).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(
                f"Ошибка добавления закладки для пользователя {user_id}: {e}")
            return False

    async def remove_bookmark(self, user_id: int, book_id: int, chapter: int) -> bool:
        """Удаляет закладку"""
        try:
            result = self.client.table('bookmarks').delete().eq('user_id', user_id).eq(
                'book_id', book_id).eq('chapter', chapter).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(
                f"Ошибка удаления закладки для пользователя {user_id}: {e}")
            return False

    async def is_bookmarked(self, user_id: int, book_id: int, chapter: int) -> bool:
        """Проверяет, есть ли закладка"""
        try:
            result = self.client.table('bookmarks').select('id').eq(
                'user_id', user_id).eq('book_id', book_id).eq('chapter', chapter).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(
                f"Ошибка проверки закладки для пользователя {user_id}: {e}")
            return False

    async def is_bookmark_exists(self, user_id: int, reference: str) -> bool:
        """Проверяет существование закладки по ссылке"""
        try:
            result = self.client.table('bookmarks').select('id').eq(
                'user_id', user_id).eq('display_text', reference).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(
                f"Ошибка проверки закладки по ссылке для пользователя {user_id}: {e}")
            return False

    # === МЕТОДЫ ДЛЯ РАБОТЫ С AI ЛИМИТАМИ ===

    async def increment_ai_usage(self, user_id: int) -> bool:
        """Увеличивает счетчик использования ИИ"""
        try:
            today = date.today().isoformat()

            # Проверяем, есть ли запись на сегодня
            result = self.client.table('ai_usage').select(
                '*').eq('user_id', user_id).eq('date', today).execute()

            if result.data:
                # Увеличиваем счетчик
                new_count = result.data[0]['count'] + 1
                update_result = self.client.table('ai_usage').update({
                    'count': new_count
                }).eq('user_id', user_id).eq('date', today).execute()
                return len(update_result.data) > 0
            else:
                # Создаем новую запись
                insert_result = self.client.table('ai_usage').insert({
                    'user_id': user_id,
                    'date': today,
                    'count': 1
                }).execute()
                return len(insert_result.data) > 0
        except Exception as e:
            logger.error(
                f"Ошибка увеличения счетчика AI для пользователя {user_id}: {e}")
            return False

    async def get_ai_usage(self, user_id: int, date_param: date = None) -> int:
        """Получает количество использований ИИ"""
        try:
            target_date = (date_param or date.today()).isoformat()
            result = self.client.table('ai_usage').select('count').eq(
                'user_id', user_id).eq('date', target_date).execute()
            return result.data[0]['count'] if result.data else 0
        except Exception as e:
            logger.error(
                f"Ошибка получения счетчика AI для пользователя {user_id}: {e}")
            return 0

    # === МЕТОДЫ ДЛЯ РАБОТЫ С ПЛАНАМИ ЧТЕНИЯ ===

    async def get_user_reading_plan(self, user_id: int, plan_id: str) -> Optional[Dict[str, Any]]:
        """Получает план чтения пользователя"""
        try:
            result = self.client.table('user_reading_plans').select(
                '*').eq('user_id', user_id).eq('plan_id', plan_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(
                f"Ошибка получения плана чтения для пользователя {user_id}: {e}")
            return None

    async def set_user_reading_plan(self, user_id: int, plan_id: str, day: int = 1) -> bool:
        """Устанавливает план чтения для пользователя"""
        try:
            data = {
                'user_id': user_id,
                'plan_id': plan_id,
                'current_day': day,
                'started_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }

            result = self.client.table(
                'user_reading_plans').upsert(data).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(
                f"Ошибка установки плана чтения для пользователя {user_id}: {e}")
            return False

    async def get_user_reading_plans(self, user_id: int) -> List[Dict[str, Any]]:
        """Получает все планы чтения пользователя"""
        try:
            result = self.client.table('user_reading_plans').select(
                '*').eq('user_id', user_id).execute()
            return result.data
        except Exception as e:
            logger.error(
                f"Ошибка получения планов чтения для пользователя {user_id}: {e}")
            return []

    async def update_reading_plan_day(self, user_id: int, plan_id: str, day: int) -> bool:
        """Обновляет текущий день плана чтения"""
        try:
            result = self.client.table('user_reading_plans').update({
                'current_day': day,
                'updated_at': datetime.now().isoformat()
            }).eq('user_id', user_id).eq('plan_id', plan_id).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(
                f"Ошибка обновления дня плана чтения для пользователя {user_id}: {e}")
            return False

    # === МЕТОДЫ ДЛЯ РАБОТЫ С ПРОГРЕССОМ ЧТЕНИЯ ===

    async def mark_reading_day_completed(self, user_id: int, plan_id: str, day: int) -> bool:
        """Отмечает день как прочитанный"""
        try:
            data = {
                'user_id': user_id,
                'plan_id': plan_id,
                'day': day,
                'completed_at': datetime.now().isoformat()
            }

            result = self.client.table(
                'reading_progress').upsert(data).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(
                f"Ошибка отметки дня как завершенного для пользователя {user_id}: {e}")
            return False

    async def mark_reading_part_completed(self, user_id: int, plan_id: str, day: int, part_idx: int) -> bool:
        """Отмечает часть дня как прочитанную"""
        try:
            logger.info(
                f"[DB_SUPABASE] Сохраняем прогресс: user_id={user_id}, plan_id={plan_id}, day={day}, part_idx={part_idx}")
            data = {
                'user_id': user_id,
                'plan_id': plan_id,
                'day': day,
                'part_idx': part_idx,
                'completed_at': datetime.now().isoformat()
            }

            result = self.client.table(
                'reading_parts_progress').upsert(data).execute()
            success = len(result.data) > 0
            logger.info(
                f"[DB_SUPABASE] Результат сохранения: {success}, данные: {result.data}")
            return success
        except Exception as e:
            logger.error(
                f"[DB_SUPABASE] Ошибка отметки части дня как завершенной для пользователя {user_id}: {e}")
            return False

    async def get_reading_progress(self, user_id: int, plan_id: str) -> List[int]:
        """Получает прогресс чтения по плану"""
        try:
            result = self.client.table('reading_progress').select('day').eq(
                'user_id', user_id).eq('plan_id', plan_id).execute()
            return [item['day'] for item in result.data]
        except Exception as e:
            logger.error(
                f"Ошибка получения прогресса чтения для пользователя {user_id}: {e}")
            return []

    async def get_reading_part_progress(self, user_id: int, plan_id: str, day: int) -> List[int]:
        """Получает прогресс частей дня"""
        try:
            logger.info(
                f"[DB_SUPABASE] Читаем прогресс: user_id={user_id}, plan_id={plan_id}, day={day}")
            result = self.client.table('reading_parts_progress').select('part_idx').eq(
                'user_id', user_id).eq('plan_id', plan_id).eq('day', day).execute()
            parts = [item['part_idx'] for item in result.data]
            logger.info(f"[DB_SUPABASE] Найдено завершенных частей: {parts}")
            return parts
        except Exception as e:
            logger.error(
                f"[DB_SUPABASE] Ошибка получения прогресса частей дня для пользователя {user_id}: {e}")
            return []

    async def is_reading_day_completed(self, user_id: int, plan_id: str, day: int) -> bool:
        """Проверяет, завершен ли день плана чтения"""
        try:
            result = self.client.table('reading_progress').select('user_id').eq(
                'user_id', user_id).eq('plan_id', plan_id).eq('day', day).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(
                f"Ошибка проверки завершения дня для пользователя {user_id}: {e}")
            return False

    async def is_reading_part_completed(self, user_id: int, plan_id: str, day: int, part_idx: int) -> bool:
        """Проверяет, отмечена ли часть дня как прочитанная"""
        try:
            logger.info(
                f"[DB_SUPABASE] Проверяем статус части: user_id={user_id}, plan_id={plan_id}, day={day}, part_idx={part_idx}")
            result = self.client.table('reading_parts_progress').select('user_id').eq(
                'user_id', user_id).eq('plan_id', plan_id).eq('day', day).eq('part_idx', part_idx).execute()
            status = len(result.data) > 0
            logger.info(
                f"[DB_SUPABASE] Статус части: {status}, данные: {result.data}")
            return status
        except Exception as e:
            logger.error(
                f"[DB_SUPABASE] Ошибка проверки завершения части дня для пользователя {user_id}: {e}")
            return False

    # === МЕТОДЫ ДЛЯ РАБОТЫ С ПЛАНАМИ ЧТЕНИЯ ===

    async def get_reading_plans(self) -> List[Dict[str, Any]]:
        """Получает все планы чтения"""
        try:
            result = self.client.table('reading_plans').select('*').execute()
            return result.data
        except Exception as e:
            logger.error(f"Ошибка получения планов чтения: {e}")
            return []

    async def get_reading_plan_days(self, plan_id: str) -> List[Dict[str, Any]]:
        """Получает дни плана чтения"""
        try:
            result = self.client.table('reading_plan_days').select(
                '*').eq('plan_id', plan_id).order('day').execute()
            return result.data
        except Exception as e:
            logger.error(f"Ошибка получения дней плана чтения {plan_id}: {e}")
            return []

    async def get_reading_plan_by_id(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Получает план чтения по ID"""
        try:
            result = self.client.table('reading_plans').select(
                '*').eq('plan_id', plan_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Ошибка получения плана чтения {plan_id}: {e}")
            return None
