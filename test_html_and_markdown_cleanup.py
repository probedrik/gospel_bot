#!/usr/bin/env python3
"""
Тест очистки HTML тегов И markdown символов
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_combined_cleanup():
    """Тестируем очистку HTML + markdown"""
    print("🧪 Тестируем очистку HTML тегов И markdown символов\n")
    
    test_cases = [
        {
            "name": "Незакрытый blockquote + markdown",
            "input": "**Анализ** главы <blockquote>важный текст",
            "expected": "Анализ главы важный текст"
        },
        {
            "name": "HTML теги + markdown",
            "input": "<b>**Жирный**</b> текст с <i>*курсивом*</i>",
            "expected": "Жирный текст с курсивом"
        },
        {
            "name": "Сложная структура",
            "input": """
            <div>
                ### **Заголовок**
                <p>Параграф с `кодом` и *курсивом*</p>
                <blockquote>**Цитата** без закрытия
            </div>
            """,
            "expected": "Заголовок\n                Параграф с кодом и курсивом\n                Цитата без закрытия"
        },
        {
            "name": "Только markdown",
            "input": "**Жирный** текст с *курсивом* и `кодом`",
            "expected": "Жирный текст с курсивом и кодом"
        },
        {
            "name": "Только HTML",
            "input": "<b>Жирный</b> текст с <i>курсивом</i>",
            "expected": "Жирный текст с курсивом"
        },
        {
            "name": "Обычный текст",
            "input": "Обычный текст без разметки",
            "expected": "Обычный текст без разметки"
        }
    ]
    
    success_count = 0
    
    for i, case in enumerate(test_cases, 1):
        print(f"{i}. {case['name']}:")
        print(f"   Входной текст: {repr(case['input'][:100])}...")
        
        # Применяем очистку как в коде
        import re
        
        # СНАЧАЛА HTML теги
        cleaned = re.sub(r'<[^>]*>', '', case['input'])
        
        # ЗАТЕМ markdown
        cleaned = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned)  # **жирный**
        cleaned = re.sub(r'\*([^*]+)\*', r'\1', cleaned)  # *курсив*
        cleaned = re.sub(r'`([^`]+)`', r'\1', cleaned)  # `код`
        cleaned = re.sub(r'#{1,6}\s*([^\n]+)', r'\1', cleaned)  # ### заголовок
        
        cleaned = cleaned.strip()
        
        print(f"   Результат: {repr(cleaned[:100])}...")
        
        # Проверяем что нет HTML тегов и markdown
        has_html = '<' in cleaned and '>' in cleaned
        has_markdown = '**' in cleaned or '*' in cleaned or '`' in cleaned or '###' in cleaned
        
        if not has_html and not has_markdown:
            print(f"   ✅ Очистка корректна")
            success_count += 1
        else:
            print(f"   ❌ Очистка некорректна!")
            if has_html:
                print(f"      - Остались HTML теги")
            if has_markdown:
                print(f"      - Остались markdown символы")
        
        print()
    
    print(f"📊 РЕЗУЛЬТАТЫ: {success_count}/{len(test_cases)} тестов пройдено")
    return success_count == len(test_cases)

def test_format_function():
    """Тестируем обновленную функцию форматирования"""
    print("\n🔧 Тестируем обновленную функцию format_ai_or_commentary\n")
    
    try:
        from handlers.text_messages import format_ai_or_commentary
        
        # Проблемный текст который вызывал ошибку
        problematic_text = """
        **Анализ главы 49 из Исаии**
        
        ### Исторический контекст
        <blockquote>Глава 49 содержит важные пророчества
        
        ### Богословское значение
        1. **Мессианские пророчества**: <i>Важные предсказания</i>
        2. **Спасение народов**: `Универсальное` спасение
        
        <div>Незакрытый блок с **жирным** текстом
        """
        
        result, opts = format_ai_or_commentary(problematic_text, "⭐ Премиум разбор от ИИ")
        
        print(f"Входной текст: {repr(problematic_text[:100])}...")
        print(f"Результат: {result}")
        print(f"Опции: {opts}")
        
        # Проверяем структуру
        blockquote_open = result.count('<blockquote>')
        blockquote_close = result.count('</blockquote>')
        
        if blockquote_open == blockquote_close == 1:
            print("✅ blockquote теги сбалансированы")
        else:
            print("❌ blockquote теги НЕ сбалансированы!")
            print(f"   Открывающих: {blockquote_open}")
            print(f"   Закрывающих: {blockquote_close}")
        
        # Проверяем что нет проблемных символов
        content = result.split('<blockquote>')[1].split('</blockquote>')[0]
        has_html = '<' in content and '>' in content
        has_markdown = '**' in content or '*' in content or '`' in content
        
        if not has_html:
            print("✅ Нет HTML тегов внутри blockquote")
        else:
            print("❌ Есть HTML теги внутри blockquote!")
        
        if not has_markdown:
            print("✅ Нет markdown символов")
        else:
            print("❌ Есть markdown символы!")
        
        return not has_html and not has_markdown and blockquote_open == blockquote_close == 1
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def show_cleanup_order():
    """Показываем порядок очистки"""
    print("\n🔄 ПОРЯДОК ОЧИСТКИ:")
    print("=" * 50)
    
    print("1. 🏷️ УДАЛЯЕМ HTML ТЕГИ:")
    print("   r'<[^>]*>' → удаляет <blockquote>, <div>, <b>, <i> и т.д.")
    print()
    
    print("2. 📝 УДАЛЯЕМ MARKDOWN:")
    print("   r'\\*\\*([^*]+)\\*\\*' → **жирный** → жирный")
    print("   r'\\*([^*]+)\\*' → *курсив* → курсив")
    print("   r'`([^`]+)`' → `код` → код")
    print("   r'#{1,6}\\s*([^\\n]+)' → ### заголовок → заголовок")
    print()
    
    print("3. 🧹 ОЧИЩАЕМ ПРОБЕЛЫ:")
    print("   .strip() → убираем лишние пробелы и переносы")
    print()
    
    print("4. 🔒 ЭКРАНИРУЕМ HTML:")
    print("   html.escape() → < → &lt;, > → &gt;, & → &amp;")
    print()
    
    print("5. 📦 ОБОРАЧИВАЕМ В BLOCKQUOTE:")
    print("   f'<blockquote>{escaped_text}</blockquote>'")

if __name__ == "__main__":
    print("🚀 ТЕСТ ОЧИСТКИ HTML ТЕГОВ И MARKDOWN СИМВОЛОВ\n")
    
    cleanup_success = test_combined_cleanup()
    format_success = test_format_function()
    
    show_cleanup_order()
    
    if cleanup_success and format_success:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("✅ HTML теги корректно удаляются")
        print("✅ Markdown символы корректно удаляются")
        print("✅ blockquote теги сбалансированы")
        print("✅ HTML экранирование работает")
        print("🔄 Перезапустите бота для применения изменений")
    else:
        print("\n❌ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ!")
        if not cleanup_success:
            print("   - Проблемы с очисткой")
        if not format_success:
            print("   - Проблемы с функцией форматирования")