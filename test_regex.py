#!/usr/bin/env python3
"""
Тест регулярного выражения для заголовка
"""
import re

# Тестовый текст из логов
test_text = "Новый завет. Марк 6:\n\n1 И вышел оттуда и пришел в отечество Свое; за Ним следовали ученики Его. 2 Когда наступила суббота, Он начал учить в синагоге; и многие слышавшие с изумлением говорили: откуда у Него это"

print(f"Тестовый текст: {repr(test_text[:100])}")

# Тестируем разные паттерны
patterns = [
    r'^([^.]+\.[^:]+:)\n\n(.*)$',
    r'^([^.]+\.\s*[^:]+:\s*)\n\n(.*)$',
    r'^(.+?:\s*)\n\n(.*)$',
    r'^(.+?:)\n\n(.*)$'
]

for i, pattern in enumerate(patterns, 1):
    print(f"\nПаттерн {i}: {pattern}")
    match = re.match(pattern, test_text, re.DOTALL)
    if match:
        print(f"  ✓ Найдено!")
        print(f"  Заголовок: {repr(match.group(1))}")
        print(f"  Текст: {repr(match.group(2)[:50])}...")
    else:
        print(f"  ✗ Не найдено")

# Проверим, что происходит с разбивкой по \n\n
parts = test_text.split('\n\n', 1)
print(f"\nРазбивка по \\n\\n:")
print(f"Часть 1: {repr(parts[0])}")
if len(parts) > 1:
    print(f"Часть 2: {repr(parts[1][:50])}...")
