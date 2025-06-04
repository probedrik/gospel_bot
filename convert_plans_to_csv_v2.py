#!/usr/bin/env python3
"""
Улучшенный скрипт для конвертации планов чтения из txt файлов в CSV формат
с точной нормализацией сокращений книг.
"""
import re
import csv
import os
from pathlib import Path
from typing import List, Dict, Tuple


def normalize_book_reference(text: str) -> str:
    """
    Нормализует ссылки на книги Библии, заменяя полные названия на стандартные сокращения.
    """
    result = text

    # Словарь замен (от длинных к коротким для избежания конфликтов)
    replacements = [
        # Новый Завет - полные названия
        (r'\bЕвангелие от Матфея\b', 'Мф'),
        (r'\bЕвангелие от Марка\b', 'Мк'),
        (r'\bЕвангелие от Луки\b', 'Лк'),
        (r'\bЕвангелие от Иоанна\b', 'Ин'),
        (r'\bДеяния апостолов\b', 'Деян'),
        (r'\bПослание к Римлянам\b', 'Рим'),
        (r'\bПервое послание к Коринфянам\b', '1Кор'),
        (r'\bВторое послание к Коринфянам\b', '2Кор'),
        (r'\bПослание к Галатам\b', 'Гал'),
        (r'\bПослание к Ефесянам\b', 'Еф'),
        (r'\bПослание к Филиппийцам\b', 'Флп'),
        (r'\bПослание к Колоссянам\b', 'Кол'),
        (r'\bПервое послание к Фессалоникийцам\b', '1Фес'),
        (r'\bВторое послание к Фессалоникийцам\b', '2Фес'),
        (r'\bПервое послание к Тимофею\b', '1Тим'),
        (r'\bВторое послание к Тимофею\b', '2Тим'),
        (r'\bПослание к Титу\b', 'Тит'),
        (r'\bПослание к Филимону\b', 'Флм'),
        (r'\bПослание к Евреям\b', 'Евр'),
        (r'\bПослание Иакова\b', 'Иак'),
        (r'\bПервое послание Петра\b', '1Пет'),
        (r'\bВторое послание Петра\b', '2Пет'),
        (r'\bПервое послание Иоанна\b', '1Ин'),
        (r'\bВторое послание Иоанна\b', '2Ин'),
        (r'\bТретье послание Иоанна\b', '3Ин'),
        (r'\bПослание Иуды\b', 'Иуд'),
        (r'\bОткровение Иоанна\b', 'Откр'),

        # Ветхий Завет - полные названия
        (r'\bПервая Книга Царств\b', '1Цар'),
        (r'\bВторая Книга Царств\b', '2Цар'),
        (r'\bТретья Книга Царств\b', '3Цар'),
        (r'\bЧетвертая Книга Царств\b', '4Цар'),
        (r'\bПервая Книга Паралипоменон\b', '1Пар'),
        (r'\bВторая Книга Паралипоменон\b', '2Пар'),
        (r'\bКнига Иисуса Навина\b', 'Нав'),
        (r'\bКнига Судей\b', 'Суд'),
        (r'\bКнига Ездры\b', 'Езд'),
        (r'\bКнига Неемии\b', 'Неем'),
        (r'\bКнига Есфири\b', 'Есф'),
        (r'\bКнига Иова\b', 'Иов'),
        (r'\bПритчи Соломоновы\b', 'Прит'),
        (r'\bПритчи Соломона\b', 'Прит'),
        (r'\bКнига Екклесиаста\b', 'Еккл'),
        (r'\bКнига Песни Песней Соломона\b', 'Песн'),
        (r'\bКнига Пророка Исаии\b', 'Ис'),
        (r'\bКнига Пророка Иеремии\b', 'Иер'),
        (r'\bПлач Иеремии\b', 'Плач'),
        (r'\bКнига Пророка Иезекииля\b', 'Иез'),
        (r'\bКнига Пророка Даниила\b', 'Дан'),
        (r'\bКнига Пророка Осии\b', 'Ос'),
        (r'\bКнига Пророка Иоиля\b', 'Иоил'),
        (r'\bКнига Пророка Амоса\b', 'Ам'),
        (r'\bКнига Пророка Авдия\b', 'Авд'),
        (r'\bКнига Пророка Ионы\b', 'Ион'),
        (r'\bКнига Пророка Михея\b', 'Мих'),
        (r'\bКнига Пророка Наума\b', 'Наум'),
        (r'\bКнига Пророка Аввакума\b', 'Авв'),
        (r'\bКнига Пророка Софонии\b', 'Соф'),
        (r'\bКнига Пророка Аггея\b', 'Агг'),
        (r'\bКнига Пророка Захарии\b', 'Зах'),
        (r'\bКнига Пророка Малахии\b', 'Мал'),
        (r'\bКнига Чисел\b', 'Чис'),

        # Простые названия
        (r'\bБытие\b', 'Быт'),
        (r'\bИсход\b', 'Исх'),
        (r'\bЛевит\b', 'Лев'),
        (r'\bЧисла\b', 'Чис'),
        (r'\bВторозаконие\b', 'Втор'),
        (r'\bИисус Навин\b', 'Нав'),
        (r'\bСудей\b', 'Суд'),
        (r'\bРуфь\b', 'Руф'),
        (r'\bЕздра\b', 'Езд'),
        (r'\bНеемия\b', 'Неем'),
        (r'\bЕсфирь\b', 'Есф'),
        (r'\bИов\b', 'Иов'),
        (r'\bПсалтырь\b', 'Пс'),
        (r'\bПсалтирь\b', 'Пс'),
        (r'\bПритчи\b', 'Прит'),
        (r'\bЕкклесиаст\b', 'Еккл'),
        (r'\bПеснь Песней\b', 'Песн'),
        (r'\bПесни Песней\b', 'Песн'),
        (r'\bИсаия\b', 'Ис'),
        (r'\bИеремия\b', 'Иер'),
        (r'\bИезекииль\b', 'Иез'),
        (r'\bДаниил\b', 'Дан'),
        (r'\bОсия\b', 'Ос'),
        (r'\bИоиль\b', 'Иоил'),
        (r'\bАмос\b', 'Ам'),
        (r'\bАвдий\b', 'Авд'),
        (r'\bИона\b', 'Ион'),
        (r'\bМихей\b', 'Мих'),
        (r'\bНаум\b', 'Наум'),
        (r'\bАввакум\b', 'Авв'),
        (r'\bСофония\b', 'Соф'),
        (r'\bАггей\b', 'Агг'),
        (r'\bЗахария\b', 'Зах'),
        (r'\bМалахия\b', 'Мал'),
    ]

    # Применяем все замены
    for pattern, replacement in replacements:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    # Убираем лишние слова "Книга" перед уже сокращенными названиями
    result = re.sub(r'\bКнига\s+([А-Я][а-я]*\d*)\b', r'\1', result)

    # Убираем лишние пробелы и нормализуем
    result = re.sub(r'\s+', ' ', result).strip()

    return result


def parse_txt_plan(filepath: str) -> Tuple[str, List[Dict]]:
    """
    Парсит txt файл с планом чтения.
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
    output_dir = Path('data/plans_csv_v2')

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

            # Показываем пример первых нескольких дней для проверки
            title, days = parse_txt_plan(str(txt_file))
            print(f"    Пример (первые 3 дня):")
            for day_info in days[:3]:
                reading = '; '.join(day_info['entries'])
                print(f"      День {day_info['day']}: {reading}")

        except Exception as e:
            print(f"    ✗ Ошибка: {e}")

    print(f"\nКонвертация завершена. CSV файлы сохранены в {output_dir}/")


if __name__ == "__main__":
    main()
