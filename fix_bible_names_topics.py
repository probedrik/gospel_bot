#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для исправления названий библейских книг в темах
Исправляет ошибки типа "Иисуса Навина" -> "Иисус Навин"
"""

import csv
import re
from pathlib import Path


def fix_bible_book_names(text):
    """Исправляет названия библейских книг в тексте"""

    # Словарь исправлений: неправильное -> правильное
    corrections = {
        # Иисус Навин
        r'\bИисуса Навина\b': 'Иисус Навин',

        # Малахия
        r'\bМалахии\b': 'Малахия',

        # Второзаконие
        r'\bВторозакония\b': 'Второзаконие',

        # Псалом (может быть и "Псалтирь", оставляем как есть)
        r'\bПсалма\b': 'Псалом',

        # Исаия
        r'\bИсайя\b': 'Исаия',

        # ИСПРАВЛЕННАЯ ЛОГИКА: добавляем номер только если его НЕТ
        # Коринфянам без номера - только если перед ним НЕТ цифры
        r'(?<!\d\s)\bКоринфянам\s+(\d+)': r'1 Коринфянам \1',

        # Фессалоникийцам без номера - только если перед ним НЕТ цифры
        r'(?<!\d\s)\bФессалоникийцам\s+(\d+)': r'1 Фессалоникийцам \1',

        # Исправляем очевидные ошибки с пробелами
        r'\b1Паралипоменон\b': '1 Паралипоменон',
        r'\b2Коринфянам\b': '2 Коринфянам',
        r'\b1Петра\b': '1 Петра',

        # Екклесиаст vs Екклезиаст
        r'\bЕкклезиаст\b': 'Екклесиаст',
    }

    result = text
    changes_made = []

    for pattern, replacement in corrections.items():
        old_result = result
        result = re.sub(pattern, replacement, result)
        if result != old_result:
            changes_made.append(f"{pattern} -> {replacement}")

    return result, changes_made


def main():
    """Основная функция"""
    input_file = "bible_verses_by_topic.csv"
    output_file = "bible_verses_by_topic_fixed.csv"

    if not Path(input_file).exists():
        print(f"❌ Файл {input_file} не найден!")
        return

    total_changes = 0
    topic_changes = {}

    try:
        # Читаем и исправляем CSV
        with open(input_file, 'r', encoding='utf-8') as infile, \
                open(output_file, 'w', encoding='utf-8', newline='') as outfile:

            reader = csv.reader(infile)
            writer = csv.writer(outfile, quoting=csv.QUOTE_ALL)

            for row_num, row in enumerate(reader):
                if len(row) >= 2:  # Тема и стихи
                    topic = row[0]
                    verses = row[1]

                    # Исправляем названия книг в стихах
                    fixed_verses, changes = fix_bible_book_names(verses)

                    if changes:
                        total_changes += len(changes)
                        topic_changes[topic] = changes
                        print(f"📝 Тема '{topic}':")
                        for change in changes:
                            print(f"   🔧 {change}")
                        print()

                    # Записываем исправленную строку
                    writer.writerow([topic, fixed_verses])
                else:
                    # Заголовок или пустая строка
                    writer.writerow(row)

        print(f"✅ Обработка завершена!")
        print(f"📊 Всего исправлений: {total_changes}")
        print(f"📁 Результат сохранен в: {output_file}")

        if topic_changes:
            print(f"\n📋 Исправлены темы: {len(topic_changes)}")
            for topic, changes in topic_changes.items():
                print(f"   • {topic} ({len(changes)} исправлений)")
        else:
            print("ℹ️ Исправлений не потребовалось")

    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    main()
