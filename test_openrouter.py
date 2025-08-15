#!/usr/bin/env python3
"""
Тест подключения к OpenRouter API
"""
import asyncio
import aiohttp
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

async def test_openrouter():
    """Тестирует подключение к OpenRouter API"""
    
    # Получаем API ключи
    api_key = os.getenv("OPENROUTER_API_KEY")
    premium_api_key = os.getenv("OPENROUTER_PREMIUM_API_KEY")
    
    print(f"🔑 Обычный API ключ: {api_key[:20]}..." if api_key else "❌ Обычный API ключ не найден")
    print(f"🔑 Премиум API ключ: {premium_api_key[:20]}..." if premium_api_key else "❌ Премиум API ключ не найден")
    
    if not api_key:
        print("❌ OPENROUTER_API_KEY не установлен!")
        return
    
    # Тестируем обычный API ключ
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "google/gemini-2.5-flash-lite",
        "messages": [
            {"role": "user", "content": "Привет! Это тест."}
        ],
        "max_tokens": 50
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            print("🔄 Тестируем обычный API ключ...")
            async with session.post(url, headers=headers, json=payload) as resp:
                print(f"📊 Статус ответа: {resp.status}")
                data = await resp.json()
                
                if resp.status == 200:
                    print("✅ Обычный API ключ работает!")
                    if "choices" in data and data["choices"]:
                        response_text = data["choices"][0]["message"]["content"]
                        print(f"💬 Ответ: {response_text}")
                    else:
                        print("⚠️ Неожиданная структура ответа")
                        print(f"📄 Полный ответ: {data}")
                else:
                    print(f"❌ Ошибка API: {resp.status}")
                    print(f"📄 Ответ: {data}")
                    
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
    
    # Тестируем премиум API ключ
    if premium_api_key:
        premium_headers = {
            "Authorization": f"Bearer {premium_api_key}",
            "Content-Type": "application/json"
        }
        
        premium_payload = {
            "model": "google/gemini-2.5-flash-lite",
            "messages": [
                {"role": "user", "content": "Привет! Это тест премиум API."}
            ],
            "max_tokens": 50
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                print("\n🔄 Тестируем премиум API ключ...")
                async with session.post(url, headers=premium_headers, json=premium_payload) as resp:
                    print(f"📊 Статус ответа: {resp.status}")
                    data = await resp.json()
                    
                    if resp.status == 200:
                        print("✅ Премиум API ключ работает!")
                        if "choices" in data and data["choices"]:
                            response_text = data["choices"][0]["message"]["content"]
                            print(f"💬 Ответ: {response_text}")
                        else:
                            print("⚠️ Неожиданная структура ответа")
                            print(f"📄 Полный ответ: {data}")
                    else:
                        print(f"❌ Ошибка премиум API: {resp.status}")
                        print(f"📄 Ответ: {data}")
                        
        except Exception as e:
            print(f"❌ Ошибка при тестировании премиум API: {e}")

if __name__ == "__main__":
    asyncio.run(test_openrouter())