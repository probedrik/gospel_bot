#!/usr/bin/env python3
"""
Скрипт для конвертации планов чтения из txt файлов в CSV формат
с нормализованными сокращениями книг.
"""
import re
import csv
import os
from pathlib import Path
from typing import List, Dict, Tuple

# Словарь для нормализации названий книг
BOOK_NORMALIZATIONS = {
    # Полные названия -> сокращения
    "Евангелие от Матфея": "Мф",
    "Евангелие от Марка": "Мк",
    "Евангелие от Луки": "Лк",
    "Евангелие от Иоанна": "Ин",
    "Деяния апостолов": "Деян",
    "Послание к Римлянам": "Рим",
    "Первое послание к Коринфянам": "1Кор",
    "Второе послание к Коринфянам": "2Кор",
    "Послание к Галатам": "Гал",
    "Послание к Ефесянам": "Еф",
    "Послание к Филиппийцам": "Флп",
    "Послание к Колоссянам": "Кол",
    "Первое послание к Фессалоникийцам": "1Фес",
    "Второе послание к Фессалоникийцам": "2Фес",
    "Первое послание к Тимофею": "1Тим",
    "Второе послание к Тимофею": "2Тим",
    "Послание к Титу": "Тит",
    "Послание к Филимону": "Флм",
    "Послание к Евреям": "Евр",
    "Послание Иакова": "Иак",
    "Первое послание Петра": "1Пет",
    "Второе послание Петра": "2Пет",
    "Первое послание Иоанна": "1Ин",
    "Второе послание Иоанна": "2Ин",
    "Третье послание Иоанна": "3Ин",
    "Послание Иуды": "Иуд",
    "Откровение Иоанна": "Откр",

    # Ветхий Завет
    "Бытие": "Быт",
    "Исход": "Исх",
    "Левит": "Лев",
    "Книга Чисел": "Чис",
    "Числа": "Чис",
    "Второзаконие": "Втор",
    "Книга Иисуса Навина": "Нав",
    "Иисус Навин": "Нав",
    "Книга Судей": "Суд",
    "Судей": "Суд",
    "Руфь": "Руф",
    "Первая Книга Царств": "1Цар",
    "Вторая Книга Царств": "2Цар",
    "Третья Книга Царств": "3Цар",
    "Четвертая Книга Царств": "4Цар",
    "Первая Книга Паралипоменон": "1Пар",
    "Вторая Книга Паралипоменон": "2Пар",
    "Книга Ездры": "Езд",
    "Ездра": "Езд",
    "Книга Неемии": "Неем",
    "Неемия": "Неем",
    "Книга Есфири": "Есф",
    "Есфирь": "Есф",
    "Книга Иова": "Иов",
    "Иов": "Иов",
    "Псалтырь": "Пс",
    "Псалтирь": "Пс",
    "Притчи Соломоновы": "Прит",
    "Притчи Соломона": "Прит",
    "Притчи": "Прит",
    "Книга Екклесиаста": "Еккл",
    "Екклесиаст": "Еккл",
    "Книга Песни Песней Соломона": "Песн",
    "Песнь Песней": "Песн",
    "Песни Песней": "Песн",
    "Книга Пророка Исаии": "Ис",
    "Исаия": "Ис",
    "Книга Пророка Иеремии": "Иер",
    "Иеремия": "Иер",
    "Плач Иеремии": "Плач",
    "Книга Пророка Иезекииля": "Иез",
    "Иезекииль": "Иез",
    "Книга Пророка Даниила": "Дан",
    "Даниил": "Дан",
    "Книга Пророка Осии": "Ос",
    "Осия": "Ос",
    "Книга Пророка Иоиля": "Иоил",
    "Иоиль": "Иоил",
    "Книга Пророка Амоса": "Ам",
    "Амос": "Ам",
    "Книга Пророка Авдия": "Авд",
    "Авдий": "Авд",
    "Книга Пророка Ионы": "Ион",
    "Иона": "Ион",
    "Книга Пророка Михея": "Мих",
    "Михей": "Мих",
    "Книга Пророка Наума": "Наум",
    "Наум": "Наум",
    "Книга Пророка Аввакума": "Авв",
    "Аввакум": "Авв",
    "Книга Пророка Софонии": "Соф",
    "Софония": "Соф",
    "Книга Пророка Аггея": "Агг",
    "Аггей": "Агг",
    "Книга Пророка Захарии": "Зах",
    "Захария": "Зах",
    "Книга Пророка Малахии": "Мал",
    "Малахия": "Мал"
}


def normalize_book_reference(text: str) -> str:
    """
    Нормализует ссылки на книги Библии, заменяя полные названия на сокращения.

    Args:
        text: Исходный текст с ссылками

    Returns:
        Нормализованный текст с сокращениями
    """
    result = text

    # Специальные случаи для исправления
    special_cases = {
        "Псалтырь": "Пс",
        "Псалтирь": "Пс",
        "Книга Песни Песней Соломона": "Песн",
        "Книга Пророка Даниила": "Дан",
        "Книга Пророка Иоиля": "Иоил",
        "Книга Пророка Амоса": "Ам",
        "Книга Пророка": "Пророка",  # Временная замена для обработки
    }

    # Сначала обрабатываем специальные случаи
    for pattern, replacement in special_cases.items():
        result = re.sub(r'\b' + re.escape(pattern) + r'\b',
                        replacement, result, flags=re.IGNORECASE)

    # Убираем лишние слова "Пророка" после нормализации
    result = re.sub(r'\bПророка\s+', '', result)

    # Сортируем по длине (сначала длинные, чтобы избежать частичных замен)
    sorted_books = sorted(BOOK_NORMALIZATIONS.items(),
                          key=lambda x: len(x[0]), reverse=True)

    for full_name, abbr in sorted_books:
        # Заменяем точные совпадения (с учетом границ слов)
        pattern = r'\b' + re.escape(full_name) + r'\b'
        result = re.sub(pattern, abbr, result, flags=re.IGNORECASE)

    # Дополнительные исправления для конкретных случаев
    corrections = {
        r'\bКнига\s+Песн\b': 'Песн',
        r'\bКнига\s+(\w+)\b': r'\1',  # Убираем "Книга" перед сокращениями
        r'\bПесн\s+Соломона\b': 'Песн',
        # Исправляем разрывы в ссылках
        r'\bДан\s+(\d+:\d+-\s*\d+)\b': r'Дан \1',
        # Исправляем пробелы вокруг точек с запятой
        r';\s*(\w+)\s*;': r'; \1;',
    }

    for pattern, replacement in corrections.items():
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    # Убираем лишние пробелы
    result = re.sub(r'\s+', ' ', result).strip()

    return result


def parse_txt_plan(filepath: str) -> Tuple[str, List[Dict]]:
    """
    Парсит txt файл с планом чтения.

    Args:
        filepath: Путь к txt файлу

    Returns:
        Кортеж (название_плана, список_дней)
    """
    days = []
    current_day = None
    entries = []
    title = Path(filepath).stem

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

        # Извлекаем заголовок из первых строк
        lines = content.split('\n')
        for line in lines[:5]:
            line = line.strip()
            if line and not line.startswith('□') and 'День' not in line and len(line) < 100:
                if 'план' in line.lower() or 'чтения' in line.lower() or 'библии' in line.lower():
                    title = line
                    break

        # Парсим дни
        for line in lines:
            line = line.strip()

            # Ищем строки с днями
            day_match = re.match(r'[□\-\s]*День\s+(\d+)\s*[—-]\s*(.+)', line)
            if day_match:
                # Сохраняем предыдущий день
                if current_day is not None:
                    normalized_entries = []
                    for entry in entries:
                        normalized_entry = normalize_book_reference(entry)
                        normalized_entries.append(normalized_entry)

                    days.append({
                        'day': current_day,
                        'entries': normalized_entries
                    })

                # Начинаем новый день
                current_day = int(day_match.group(1))
                day_text = day_match.group(2).strip()
                entries = [day_text]

            elif current_day is not None and line and not line.startswith('□'):
                # Дополнительные строки для текущего дня
                if not re.match(r'День\s+\d+', line):
                    entries.append(line)

        # Сохраняем последний день
        if current_day is not None:
            normalized_entries = []
            for entry in entries:
                normalized_entry = normalize_book_reference(entry)
                normalized_entries.append(normalized_entry)

            days.append({
                'day': current_day,
                'entries': normalized_entries
            })

    return title, days


def convert_plan_to_csv(txt_filepath: str, csv_filepath: str) -> None:
    """
    Конвертирует план чтения из txt в CSV формат.

    Args:
        txt_filepath: Путь к исходному txt файлу
        csv_filepath: Путь к результирующему CSV файлу
    """
    title, days = parse_txt_plan(txt_filepath)

    with open(csv_filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)

        # Заголовок
        writer.writerow(['plan_title', title])
        writer.writerow(['day', 'reading'])

        # Данные
        for day_info in days:
            day = day_info['day']
            # Объединяем все записи дня в одну строку через точку с запятой
            reading = '; '.join(day_info['entries'])
            writer.writerow([day, reading])


def main():
    """Основная функция для конвертации всех планов."""
    plans_dir = Path('data/plans')
    output_dir = Path('data/plans_csv')

    # Создаем выходную директорию
    output_dir.mkdir(exist_ok=True)

    # Конвертируем все txt файлы
    txt_files = list(plans_dir.glob('*.txt'))

    if not txt_files:
        print("Не найдено txt файлов в директории data/plans/")
        return

    print(f"Найдено {len(txt_files)} txt файлов для конвертации:")

    for txt_file in txt_files:
        csv_filename = txt_file.stem + '.csv'
        csv_filepath = output_dir / csv_filename

        print(f"  Конвертирую: {txt_file.name} -> {csv_filename}")

        try:
            convert_plan_to_csv(str(txt_file), str(csv_filepath))
            print(f"    ✓ Успешно сохранено в {csv_filepath}")
        except Exception as e:
            print(f"    ✗ Ошибка: {e}")

    print(f"\nКонвертация завершена. CSV файлы сохранены в {output_dir}/")


if __name__ == "__main__":
    main()
