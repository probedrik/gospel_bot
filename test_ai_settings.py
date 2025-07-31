#!/usr/bin/env python3
"""
Тестовый скрипт для проверки автоматического обновления настроек ИИ
"""

# Импортируем настройки
from config.ai_settings import AI_DAILY_LIMIT, PREMIUM_AI_PACKAGE_PRICE, PREMIUM_AI_PACKAGE_REQUESTS

# Импортируем функции, которые должны использовать эти настройки
from handlers.settings import get_premium_info_text, get_premium_detailed_info_text

def test_settings_integration():
    """Тестирует интеграцию настроек в тексты"""
    
    print("🧪 Тестирование интеграции настроек ИИ")
    print("=" * 50)
    
    # Показываем текущие настройки
    print(f"📊 Текущие настройки:")
    print(f"   • Дневной лимит: {AI_DAILY_LIMIT}")
    print(f"   • Цена пакета: {PREMIUM_AI_PACKAGE_PRICE}₽")
    print(f"   • Запросов в пакете: {PREMIUM_AI_PACKAGE_REQUESTS}")
    print()
    
    # Тестируем основной текст
    print("📝 Основной текст премиум доступа:")
    print("-" * 30)
    basic_text = get_premium_info_text()
    
    # Проверяем, что значения подставились
    if f"{PREMIUM_AI_PACKAGE_REQUESTS} премиум запросов за {PREMIUM_AI_PACKAGE_PRICE}₽" in basic_text:
        print("✅ Цена и количество запросов подставились корректно")
    else:
        print("❌ Ошибка: цена или количество запросов не подставились")
    
    if f"{AI_DAILY_LIMIT} запросов" in basic_text:
        print("✅ Дневной лимит подставился корректно")
    else:
        print("❌ Ошибка: дневной лимит не подставился")
    
    print()
    
    # Тестируем подробный текст
    print("📝 Подробный текст премиум доступа:")
    print("-" * 30)
    detailed_text = get_premium_detailed_info_text()
    
    # Проверяем расчеты
    total_requests = AI_DAILY_LIMIT + PREMIUM_AI_PACKAGE_REQUESTS
    if f"Всего доступно: {total_requests} запросов в день" in detailed_text:
        print("✅ Общее количество запросов рассчитано корректно")
    else:
        print("❌ Ошибка: общее количество запросов рассчитано неверно")
    
    if f"Дневной лимит: {AI_DAILY_LIMIT} запроса" in detailed_text:
        print("✅ Дневной лимит в примере подставился корректно")
    else:
        print("❌ Ошибка: дневной лимит в примере не подставился")
    
    print()
    print("🎯 Тестирование завершено!")
    
    # Показываем фрагменты текстов для проверки
    print("\n" + "=" * 50)
    print("📋 Фрагменты сгенерированных текстов:")
    print("=" * 50)
    
    print("\n🔹 Основной текст (фрагмент):")
    lines = basic_text.split('\n')
    for line in lines[10:15]:  # Показываем строки с ценой
        if 'премиум запросов за' in line or 'дневные лимиты' in line:
            print(f"   {line}")
    
    print("\n🔹 Подробный текст (фрагмент):")
    lines = detailed_text.split('\n')
    for line in lines:
        if 'Дневной лимит:' in line or 'Всего доступно:' in line or 'Стоимость:' in line:
            print(f"   {line}")

if __name__ == "__main__":
    test_settings_integration()