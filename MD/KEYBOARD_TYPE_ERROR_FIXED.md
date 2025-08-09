# ✅ Ошибка типов клавиатур исправлена!

## 🔍 Проблема

Бот выдавал ошибку при нажатии кнопки "⬅️ Назад в главное меню":

```
ValidationError: 1 validation error for EditMessageText
reply_markup
  Input should be a valid dictionary or instance of InlineKeyboardMarkup 
  [type=model_type, input_value=ReplyKeyboardMarkup(...), input_type=ReplyKeyboardMarkup]
```

## 🔧 Причина

В функциях `back_to_main_menu` использовался метод `edit_text` с `ReplyKeyboardMarkup`:

```python
# ❌ Неправильно
await callback.message.edit_text(
    "🏠 Главное меню",
    reply_markup=get_main_keyboard()  # ReplyKeyboardMarkup
)
```

**Проблема:** `edit_text` может работать только с `InlineKeyboardMarkup`, а `get_main_keyboard()` возвращает `ReplyKeyboardMarkup`.

## ✅ Решение

Заменили `edit_text` на `delete` + `answer`:

```python
# ✅ Правильно
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    # Удаляем сообщение с inline клавиатурой
    await callback.message.delete()
    
    # Отправляем новое сообщение с обычной клавиатурой
    await callback.message.answer(
        "🏠 Главное меню",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()
```

## 🔧 Исправленные файлы

### `handlers/bookmarks_new.py`
- ✅ Функция `back_to_main_menu` исправлена
- ✅ Теперь удаляет сообщение и отправляет новое

### `handlers/settings.py`
- ✅ Функция `back_to_main_menu` исправлена
- ✅ Теперь удаляет сообщение и отправляет новое

## 🎮 Результат

### Что работает:
- ✅ Кнопка "⬅️ Назад в главное меню" в закладках
- ✅ Кнопка "⬅️ Назад в главное меню" в настройках
- ✅ Плавный переход от inline к обычной клавиатуре
- ✅ Никаких ошибок валидации

### Поведение:
1. **Пользователь нажимает "⬅️ Назад в главное меню"**
2. **Сообщение с inline кнопками удаляется**
3. **Появляется новое сообщение с обычными кнопками**
4. **Пользователь видит главное меню**

## 📋 Типы клавиатур в Telegram

### ReplyKeyboardMarkup (обычная клавиатура):
- Показывается внизу экрана
- Заменяет системную клавиатуру
- Используется в `message.answer()`
- **Нельзя** использовать в `edit_text()`

### InlineKeyboardMarkup (inline клавиатура):
- Показывается под сообщением
- Кнопки с callback_data
- Используется в `edit_text()` и `edit_reply_markup()`
- **Можно** редактировать без пересылки сообщения

## 🚀 Готово!

Теперь переходы между меню работают корректно:
- ✅ Из закладок в главное меню
- ✅ Из настроек в главное меню
- ✅ Никаких ошибок типов клавиатур
- ✅ Плавный пользовательский опыт

**Бот готов к использованию!** 🎉