#!/usr/bin/env python3
"""
Скрипт для создания таблиц Telegram Stars в базе данных
"""
import asyncio
import logging
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def setup_star_tables():
    """Создает таблицы для Telegram Stars платежей"""
    
    # Импортируем менеджер базы данных
    from database.universal_manager import universal_db_manager as db_manager
    
    try:
        # Инициализируем базу данных
        await db_manager.initialize()
        
        # Читаем SQL скрипт
        with open('create_star_tables.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # Выполняем SQL скрипт
        if db_manager.is_supabase:
            # Для Supabase используем клиент
            logger.info("🌟 Создание таблиц в Supabase...")
            
            # Разбиваем скрипт на отдельные команды
            sql_commands = [cmd.strip() for cmd in sql_script.split(';') if cmd.strip()]
            
            for i, command in enumerate(sql_commands):
                if command:
                    try:
                        logger.info(f"Выполняем команду {i+1}/{len(sql_commands)}")
                        result = db_manager.manager.client.rpc('exec_sql', {'sql': command}).execute()
                        logger.info(f"✅ Команда {i+1} выполнена успешно")
                    except Exception as e:
                        logger.warning(f"⚠️ Команда {i+1} пропущена (возможно, уже существует): {e}")
                        
        elif db_manager.is_postgres:
            # Для PostgreSQL используем asyncpg
            logger.info("🐘 Создание таблиц в PostgreSQL...")
            
            # Выполняем весь скрипт
            await db_manager.manager.execute_script(sql_script)
            
        else:
            # Для SQLite адаптируем скрипт
            logger.info("🗃️ Создание таблиц в SQLite...")
            
            # Заменяем PostgreSQL специфичные типы на SQLite
            sqlite_script = sql_script.replace('SERIAL PRIMARY KEY', 'INTEGER PRIMARY KEY AUTOINCREMENT')
            sqlite_script = sqlite_script.replace('BIGINT', 'INTEGER')
            sqlite_script = sqlite_script.replace('VARCHAR(255)', 'TEXT')
            sqlite_script = sqlite_script.replace('VARCHAR(50)', 'TEXT')
            sqlite_script = sqlite_script.replace('VARCHAR(20)', 'TEXT')
            sqlite_script = sqlite_script.replace('DECIMAL(10,2)', 'REAL')
            sqlite_script = sqlite_script.replace('TIMESTAMP', 'DATETIME')
            sqlite_script = sqlite_script.replace('CURRENT_TIMESTAMP', "datetime('now')")
            
            # Убираем PostgreSQL специфичные функции и триггеры
            lines = sqlite_script.split('\n')
            filtered_lines = []
            skip_until_semicolon = False
            
            for line in lines:
                if 'CREATE OR REPLACE FUNCTION' in line or 'CREATE TRIGGER' in line:
                    skip_until_semicolon = True
                    continue
                if skip_until_semicolon:
                    if ';' in line:
                        skip_until_semicolon = False
                    continue
                if 'COMMENT ON' in line:
                    continue
                filtered_lines.append(line)
            
            sqlite_script = '\n'.join(filtered_lines)
            
            # Выполняем адаптированный скрипт
            db_manager.manager.execute_script(sqlite_script)
        
        logger.info("✅ Таблицы для Telegram Stars успешно созданы!")
        
        # Проверяем созданные таблицы
        await check_tables(db_manager)
        
    except Exception as e:
        logger.error(f"❌ Ошибка при создании таблиц: {e}")
        raise
    finally:
        # Закрываем соединение
        await db_manager.close()

async def check_tables(db_manager):
    """Проверяет созданные таблицы"""
    try:
        logger.info("🔍 Проверка созданных таблиц...")
        
        tables_to_check = [
            'star_transactions',
            'premium_requests', 
            'premium_purchases',
            'donations'
        ]
        
        for table_name in tables_to_check:
            try:
                if db_manager.is_supabase:
                    # Для Supabase проверяем через select
                    result = db_manager.manager.client.table(table_name).select('*').limit(1).execute()
                    logger.info(f"✅ Таблица {table_name} существует")
                elif db_manager.is_postgres:
                    # Для PostgreSQL проверяем через информационную схему
                    query = """
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_name = $1 AND table_schema = 'public'
                    """
                    result = await db_manager.manager.fetch_one(query, (table_name,))
                    if result:
                        logger.info(f"✅ Таблица {table_name} существует")
                    else:
                        logger.warning(f"⚠️ Таблица {table_name} не найдена")
                else:
                    # Для SQLite проверяем через sqlite_master
                    query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
                    result = db_manager.manager.fetch_one(query, (table_name,))
                    if result:
                        logger.info(f"✅ Таблица {table_name} существует")
                    else:
                        logger.warning(f"⚠️ Таблица {table_name} не найдена")
                        
            except Exception as e:
                logger.warning(f"⚠️ Не удалось проверить таблицу {table_name}: {e}")
        
        logger.info("🎉 Проверка таблиц завершена!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке таблиц: {e}")

if __name__ == "__main__":
    asyncio.run(setup_star_tables())