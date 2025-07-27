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

    async def add_bookmark(self, user_id: int, book_id: int, chapter_start: int,
                           chapter_end: int = None, display_text: str = None, 
                           verse_start: int = None, verse_end: int = None, note: str = None) -> bool:
        """Добавляет закладку"""
        try:
            data = {
                'user_id': user_id,
                'book_id': book_id,
                'chapter': chapter_start,  # Для совместимости со старым полем
                'chapter_start': chapter_start,
                'chapter_end': chapter_end,
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

    async def remove_bookmark(self, user_id: int, book_id: int, chapter_start: int,
                             chapter_end: int = None, verse_start: int = None, verse_end: int = None) -> bool:
        """Удаляет закладку"""
        try:
            query = self.client.table('bookmarks').delete().eq('user_id', user_id).eq('book_id', book_id).eq('chapter_start', chapter_start)
            
            if chapter_end is not None:
                query = query.eq('chapter_end', chapter_end)
            else:
                query = query.is_('chapter_end', 'null')
                
            if verse_start is not None:
                query = query.eq('verse_start', verse_start)
            else:
                query = query.is_('verse_start', 'null')
                
            if verse_end is not None:
                query = query.eq('verse_end', verse_end)
            else:
                query = query.is_('verse_end', 'null')
            
            result = query.execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(
                f"Ошибка удаления закладки для пользователя {user_id}: {e}")
            return False

    async def is_bookmarked(self, user_id: int, book_id: int, chapter_start: int,
                           chapter_end: int = None, verse_start: int = None, verse_end: int = None) -> bool:
        """Проверяет, есть ли закладка"""
        try:
            query = self.client.table('bookmarks').select('id').eq('user_id', user_id).eq('book_id', book_id).eq('chapter_start', chapter_start)
            
            if chapter_end is not None:
                query = query.eq('chapter_end', chapter_end)
            else:
                query = query.is_('chapter_end', 'null')
                
            if verse_start is not None:
                query = query.eq('verse_start', verse_start)
            else:
                query = query.is_('verse_start', 'null')
                
            if verse_end is not None:
                query = query.eq('verse_end', verse_end)
            else:
                query = query.is_('verse_end', 'null')
            
            result = query.execute()
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

    # AI Limits методы
    async def get_ai_limit(self, user_id: int, date: str) -> int:
        """Возвращает количество ИИ-запросов пользователя за дату (строка YYYY-MM-DD)"""
        try:
            result = self.client.table('ai_limits').select('count').eq(
                'user_id', user_id).eq('date', date).execute()
            return result.data[0]['count'] if result.data else 0
        except Exception as e:
            logger.error(f"Ошибка получения AI лимита: {e}")
            return 0

    async def increment_ai_limit(self, user_id: int, date: str) -> int:
        """Увеличивает счетчик ИИ-запросов пользователя за дату, возвращает новое значение"""
        try:
            # Проверяем существующий лимит
            result = self.client.table('ai_limits').select('count').eq(
                'user_id', user_id).eq('date', date).execute()

            if result.data:
                # Обновляем существующий
                new_count = result.data[0]['count'] + 1
                self.client.table('ai_limits').update({'count': new_count}).eq(
                    'user_id', user_id).eq('date', date).execute()
            else:
                # Создаем новый
                new_count = 1
                self.client.table('ai_limits').insert({
                    'user_id': user_id,
                    'date': date,
                    'count': new_count
                }).execute()

            return new_count
        except Exception as e:
            logger.error(f"Ошибка увеличения AI лимита: {e}")
            return 0

    async def reset_ai_limit(self, user_id: int, date: str) -> None:
        """Сбросить лимит ИИ-запросов пользователя за дату (удаляет запись)"""
        try:
            self.client.table('ai_limits').delete().eq(
                'user_id', user_id).eq('date', date).execute()
        except Exception as e:
            logger.error(f"Ошибка сброса AI лимита: {e}")

    async def get_ai_stats(self, date: str, limit: int = 10) -> list:
        """Топ пользователей по ИИ-запросам за дату (user_id, count)"""
        try:
            result = self.client.table('ai_limits').select('user_id, count').eq(
                'date', date).order('count', desc=True).limit(limit).execute()
            return [(row['user_id'], row['count']) for row in result.data]
        except Exception as e:
            logger.error(f"Ошибка получения AI статистики: {e}")
            return []

    async def get_ai_stats_alltime(self, limit: int = 10) -> list:
        """Топ пользователей по ИИ-запросам за всё время (user_id, total_count)"""
        try:
            # В Supabase используем агрегацию через RPC функцию или простой запрос
            # Для простоты используем Python агрегацию
            result = self.client.table('ai_limits').select(
                'user_id, count').execute()

            # Агрегируем данные по пользователям
            user_totals = {}
            for row in result.data:
                user_id = row['user_id']
                count = row['count']
                user_totals[user_id] = user_totals.get(user_id, 0) + count

            # Сортируем и возвращаем топ
            sorted_users = sorted(user_totals.items(),
                                  key=lambda x: x[1], reverse=True)
            return sorted_users[:limit]
        except Exception as e:
            logger.error(f"Ошибка получения общей AI статистики: {e}")
            return []

    # Методы для сохраненных толкований
    async def save_commentary(self, user_id: int, book_id: int, chapter_start: int,
                              chapter_end: int = None, verse_start: int = None, verse_end: int = None,
                              reference_text: str = "", commentary_text: str = "",
                              commentary_type: str = "ai") -> bool:
        """Сохраняет толкование для пользователя"""
        try:
            # Проверяем, есть ли уже толкование для этой ссылки
            query = self.client.table('saved_commentaries').select('id').eq(
                'user_id', user_id).eq('book_id', book_id).eq('chapter_start', chapter_start).eq(
                'commentary_type', commentary_type)

            # Правильно обрабатываем NULL значения для chapter_end
            if chapter_end is None:
                query = query.is_('chapter_end', 'null')
            else:
                query = query.eq('chapter_end', chapter_end)

            # Правильно обрабатываем NULL значения для verse_start
            if verse_start is None:
                query = query.is_('verse_start', 'null')
            else:
                query = query.eq('verse_start', verse_start)

            # Правильно обрабатываем NULL значения для verse_end
            if verse_end is None:
                query = query.is_('verse_end', 'null')
            else:
                query = query.eq('verse_end', verse_end)

            existing = query.execute()

            data = {
                'user_id': user_id,
                'book_id': book_id,
                'chapter_start': chapter_start,
                'chapter_end': chapter_end,
                'verse_start': verse_start,
                'verse_end': verse_end,
                'reference_text': reference_text,
                'commentary_text': commentary_text,
                'commentary_type': commentary_type,
                'updated_at': datetime.now().isoformat()
            }

            if existing.data:
                # Обновляем существующее
                self.client.table('saved_commentaries').update(data).eq(
                    'id', existing.data[0]['id']).execute()
            else:
                # Создаем новое
                self.client.table('saved_commentaries').insert(data).execute()

            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения толкования: {e}")
            return False

    async def get_saved_commentary(self, user_id: int, book_id: int, chapter_start: int,
                                   chapter_end: int = None, verse_start: int = None, verse_end: int = None,
                                   commentary_type: str = "ai") -> Optional[str]:
        """Получает сохраненное толкование"""
        try:
            query = self.client.table('saved_commentaries').select(
                'commentary_text').eq('user_id', user_id).eq('book_id', book_id).eq(
                'chapter_start', chapter_start).eq('commentary_type', commentary_type)

            # Правильно обрабатываем NULL значения для chapter_end
            if chapter_end is None:
                query = query.is_('chapter_end', 'null')
            else:
                query = query.eq('chapter_end', chapter_end)

            # Правильно обрабатываем NULL значения для verse_start
            if verse_start is None:
                query = query.is_('verse_start', 'null')
            else:
                query = query.eq('verse_start', verse_start)

            # Правильно обрабатываем NULL значения для verse_end
            if verse_end is None:
                query = query.is_('verse_end', 'null')
            else:
                query = query.eq('verse_end', verse_end)

            result = query.execute()
            return result.data[0]['commentary_text'] if result.data else None
        except Exception as e:
            logger.error(f"Ошибка получения сохраненного толкования: {e}")
            return None

    async def delete_saved_commentary(self, user_id: int, book_id: int, chapter_start: int,
                                      chapter_end: int = None, verse_start: int = None, verse_end: int = None,
                                      commentary_type: str = "ai") -> bool:
        """Удаляет сохраненное толкование"""
        try:
            query = self.client.table('saved_commentaries').delete().eq(
                'user_id', user_id).eq('book_id', book_id).eq('chapter_start', chapter_start).eq(
                'commentary_type', commentary_type)

            # Правильно обрабатываем NULL значения для chapter_end
            if chapter_end is None:
                query = query.is_('chapter_end', 'null')
            else:
                query = query.eq('chapter_end', chapter_end)

            # Правильно обрабатываем NULL значения для verse_start
            if verse_start is None:
                query = query.is_('verse_start', 'null')
            else:
                query = query.eq('verse_start', verse_start)

            # Правильно обрабатываем NULL значения для verse_end
            if verse_end is None:
                query = query.is_('verse_end', 'null')
            else:
                query = query.eq('verse_end', verse_end)

            query.execute()
            return True
        except Exception as e:
            logger.error(f"Ошибка удаления толкования: {e}")
            return False

    async def delete_commentary_by_id(self, user_id: int, commentary_id: int) -> bool:
        """Удаляет сохраненное толкование по ID"""
        try:
            self.client.table('saved_commentaries').delete().eq(
                'user_id', user_id).eq('id', commentary_id).execute()
            return True
        except Exception as e:
            logger.error(f"Ошибка удаления толкования по ID: {e}")
            return False

    async def get_user_commentaries(self, user_id: int, limit: int = 50) -> list:
        """Получает последние сохраненные толкования пользователя"""
        try:
            result = self.client.table('saved_commentaries').select(
                'id, book_id, chapter_start, chapter_end, verse_start, verse_end, reference_text, commentary_text, commentary_type, created_at'
            ).eq('user_id', user_id).order(
                'created_at', desc=True
            ).limit(limit).execute()

            return [dict(row) for row in result.data]
        except Exception as e:
            logger.error(f"Ошибка получения толкований пользователя: {e}")
            return []

    # Методы для библейских тем
    async def get_bible_topics(self, search_query: str = "", limit: int = 50) -> list:
        """Получает список библейских тем с возможностью поиска"""
        try:
            query = self.client.table('bible_topics').select(
                'id, topic_name, verses')

            if search_query:
                # Поиск по названию темы (регистронезависимый)
                query = query.ilike('topic_name', f'%{search_query}%')

            result = query.order('topic_name').limit(limit).execute()
            return [dict(row) for row in result.data]

        except Exception as e:
            logger.error(f"Ошибка получения тем: {e}")
            return []

    async def get_topic_by_name(self, topic_name: str) -> dict:
        """Получает тему по точному названию"""
        try:
            result = self.client.table('bible_topics').select(
                'id, topic_name, verses'
            ).eq('topic_name', topic_name).execute()

            if result.data:
                return dict(result.data[0])
            return {}

        except Exception as e:
            logger.error(f"Ошибка получения темы '{topic_name}': {e}")
            return {}

    async def get_topic_by_id(self, topic_id: int) -> dict:
        """Получает тему по ID"""
        try:
            result = self.client.table('bible_topics').select(
                'id, topic_name, verses'
            ).eq('id', topic_id).execute()

            if result.data:
                return dict(result.data[0])
            return {}

        except Exception as e:
            logger.error(f"Ошибка получения темы по ID {topic_id}: {e}")
            return {}

    async def search_topics_fulltext(self, search_query: str, limit: int = 20) -> list:
        """Полнотекстовый поиск по темам (использует PostgreSQL FTS)"""
        try:
            # Используем PostgreSQL полнотекстовый поиск
            result = self.client.table('bible_topics').select(
                'id, topic_name, verses'
            ).text_search(
                'topic_name', search_query, type='websearch', config='russian'
            ).order('topic_name').limit(limit).execute()

            return [dict(row) for row in result.data]

        except Exception as e:
            logger.warning(f"Ошибка FTS поиска, переходим к обычному: {e}")
            # Fallback к обычному поиску
            return await self.get_bible_topics(search_query, limit)

    async def get_topics_count(self) -> int:
        """Получает общее количество тем"""
        try:
            result = self.client.table('bible_topics').select(
                'id', count='exact').execute()
            return result.count or 0
        except Exception as e:
            logger.error(f"Ошибка получения количества тем: {e}")
            return 0

    async def add_bible_topic(self, topic_name: str, verses: str) -> bool:
        """Добавляет новую библейскую тему"""
        try:
            data = {
                'topic_name': topic_name,
                'verses': verses
            }

            result = self.client.table('bible_topics').insert(data).execute()
            return bool(result.data)

        except Exception as e:
            logger.error(f"Ошибка добавления темы '{topic_name}': {e}")
            return False

    async def update_bible_topic(self, topic_id: int, topic_name: str = None, verses: str = None) -> bool:
        """Обновляет существующую библейскую тему"""
        try:
            data = {}
            if topic_name is not None:
                data['topic_name'] = topic_name
            if verses is not None:
                data['verses'] = verses

            if not data:
                return False

            data['updated_at'] = datetime.now().isoformat()

            result = self.client.table('bible_topics').update(
                data).eq('id', topic_id).execute()
            return bool(result.data)

        except Exception as e:
            logger.error(f"Ошибка обновления темы ID {topic_id}: {e}")
            return False

    async def delete_bible_topic(self, topic_id: int) -> bool:
        """Удаляет библейскую тему"""
        try:
            result = self.client.table('bible_topics').delete().eq(
                'id', topic_id).execute()
            return bool(result.data)

        except Exception as e:
            logger.error(f"Ошибка удаления темы ID {topic_id}: {e}")
            return False
