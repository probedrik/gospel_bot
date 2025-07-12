#!/usr/bin/env python3
"""
Финальная версия скрипта для конвертации планов чтения из txt файлов в CSV формат
с максимально точной нормализацией сокращений книг.
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

    # Предварительная очистка
    result = re.sub(r'\s+', ' ', result).strip()

    # Специальные замены для проблемных случаев
    special_replacements = [
        # Псалтырь/Псалтирь
        (r'\bПсалтырь(\d+)\b', r'Пс \1'),
        (r'\bПсалтирь(\d+)\b', r'Пс \1'),
        (r'\bПсалтырь\b', 'Пс'),
        (r'\bПсалтирь\b', 'Пс'),

        # Книги с "Книга Пророка"
        (r'\bКнига\s+Пророка\s+Даниила\b', 'Дан'),
        (r'\bКнига\s+Пророка\s+Иоиля\b', 'Иоил'),
        (r'\bКнига\s+Пророка\s+Амоса\b', 'Ам'),
        (r'\bКнига\s+Пророка\s+Исаии\b', 'Ис'),
        (r'\bКнига\s+Пророка\s+Иеремии\b', 'Иер'),
        (r'\bКнига\s+Пророка\s+Иезекииля\b', 'Иез'),
        (r'\bКнига\s+Пророка\s+Осии\b', 'Ос'),
        (r'\bКнига\s+Пророка\s+Авдия\b', 'Авд'),
        (r'\bКнига\s+Пророка\s+Ионы\b', 'Ион'),
        (r'\bКнига\s+Пророка\s+Михея\b', 'Мих'),
        (r'\bКнига\s+Пророка\s+Наума\b', 'Наум'),
        (r'\bКнига\s+Пророка\s+Аввакума\b', 'Авв'),
        (r'\bКнига\s+Пророка\s+Софонии\b', 'Соф'),
        (r'\bКнига\s+Пророка\s+Аггея\b', 'Агг'),
        (r'\bКнига\s+Пророка\s+Захарии\b', 'Зах'),
        (r'\bКнига\s+Пророка\s+Малахии\b', 'Мал'),

        # Книги Царств
        (r'\bПервая\s+Книга\s+Царств\b', '1Цар'),
        (r'\bВторая\s+Книга\s+Царств\b', '2Цар'),
        (r'\bТретья\s+Книга\s+Царств\b', '3Цар'),
        (r'\bЧетвертая\s+Книга\s+Царств\b', '4Цар'),

        # Другие книги с "Книга"
        (r'\bКнига\s+Иисуса\s+Навина\b', 'Нав'),
        (r'\bКнига\s+Судей\b', 'Суд'),
        (r'\bКнига\s+Ездры\b', 'Езд'),
        (r'\bКнига\s+Неемии\b', 'Неем'),
        (r'\bКнига\s+Есфири\b', 'Есф'),
        (r'\bКнига\s+Иова\b', 'Иов'),
        (r'\bКнига\s+Екклесиаста\b', 'Еккл'),
        (r'\bКнига\s+Песни\s+Песней\s+Соломона\b', 'Песн'),
        (r'\bКнига\s+Чисел\b', 'Чис'),

        # Евангелия
        (r'\bЕвангелие\s+от\s+Матфея\b', 'Мф'),
        (r'\bЕвангелие\s+от\s+Марка\b', 'Мк'),
        (r'\bЕвангелие\s+от\s+Луки\b', 'Лк'),
        (r'\bЕвангелие\s+от\s+Иоанна\b', 'Ин'),

        # Послания
        (r'\bДеяния\s+апостолов\b', 'Деян'),
        (r'\bПослание\s+к\s+Римлянам\b', 'Рим'),
        (r'\bПервое\s+послание\s+к\s+Коринфянам\b', '1Кор'),
        (r'\bВторое\s+послание\s+к\s+Коринфянам\b', '2Кор'),
        (r'\bПослание\s+к\s+Галатам\b', 'Гал'),
        (r'\bПослание\s+к\s+Ефесянам\b', 'Еф'),
        (r'\bПослание\s+к\s+Филиппийцам\b', 'Флп'),
        (r'\bПослание\s+к\s+Колоссянам\b', 'Кол'),
        (r'\bПервое\s+послание\s+к\s+Фессалоникийцам\b', '1Фес'),
        (r'\bВторое\s+послание\s+к\s+Фессалоникийцам\b', '2Фес'),
        (r'\bПервое\s+послание\s+к\s+Тимофею\b', '1Тим'),
        (r'\bВторое\s+послание\s+к\s+Тимофею\b', '2Тим'),
        (r'\bПослание\s+к\s+Титу\b', 'Тит'),
        (r'\bПослание\s+к\s+Филимону\b', 'Флм'),
        (r'\bПослание\s+к\s+Евреям\b', 'Евр'),
        (r'\bПослание\s+Иакова\b', 'Иак'),
        (r'\bПервое\s+послание\s+Петра\b', '1Пет'),
        (r'\bВторое\s+послание\s+Петра\b', '2Пет'),
        (r'\bПервое\s+послание\s+Иоанна\b', '1Ин'),
        (r'\bВторое\s+послание\s+Иоанна\b', '2Ин'),
        (r'\bТретье\s+послание\s+Иоанна\b', '3Ин'),
        (r'\bПослание\s+Иуды\b', 'Иуд'),
        (r'\bОткровение\s+Иоанна\b', 'Откр'),

        # Простые названия
        (r'\bБытие\b', 'Быт'),
        (r'\bИсход\b', 'Исх'),
        (r'\bЛевит\b', 'Лев'),
        (r'\bЧисла\b', 'Чис'),
        (r'\bВторозаконие\b', 'Втор'),
        (r'\bИисус\s+Навин\b', 'Нав'),
        (r'\bСудей\b', 'Суд'),
        (r'\bРуфь\b', 'Руф'),
        (r'\bЕздра\b', 'Езд'),
        (r'\bНеемия\b', 'Неем'),
        (r'\bЕсфирь\b', 'Есф'),
        (r'\bИов\b', 'Иов'),
        (r'\bПритчи\s+Соломоновы\b', 'Прит'),
        (r'\bПритчи\s+Соломона\b', 'Прит'),
        (r'\bПритчи\b', 'Прит'),
        (r'\bЕкклесиаст\b', 'Еккл'),
        (r'\bПеснь\s+Песней\b', 'Песн'),
        (r'\bПесни\s+Песней\b', 'Песн'),
        (r'\bИсаия\b', 'Ис'),
        (r'\bИеремия\b', 'Иер'),
        (r'\bПлач\s+Иеремии\b', 'Плач'),
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
    for pattern, replacement in special_replacements:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    # Убираем остатки слов "Книга", "Пророка" и т.д.
    cleanup_patterns = [
        (r'\bКнига\s+', ''),
        (r'\bПророка\s+', ''),
        (r'\s+Соломона\b', ''),  # Убираем "Соломона" после "Песн"
    ]

    for pattern, replacement in cleanup_patterns:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    # Финальная очистка пробелов
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
    output_dir = Path('data/plans_csv_final')

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
            print()

        except Exception as e:
            print(f"    ✗ Ошибка: {e}")

    print(f"\nКонвертация завершена. CSV файлы сохранены в {output_dir}/")


if __name__ == "__main__":
    main()
