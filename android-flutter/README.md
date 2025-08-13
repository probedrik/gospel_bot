# Gospel Bot Flutter

Минимальная Flutter-версия приложения, работающая локально с текстами Библии и синхронизацией закладок в Supabase.

## Подготовка

1. Установите Flutter 3.22+.
2. Скопируйте файлы Библии из корня проекта:
   - `../local/rst.json` → `android-flutter/assets/rst.json`
   - `../local/rbo.json` → `android-flutter/assets/rbo.json`
3. Передайте ключи Supabase при запуске:

```
flutter run \
  --dart-define=SUPABASE_URL=https://YOUR.supabase.co \
  --dart-define=SUPABASE_ANON_KEY=YOUR_ANON_KEY
```

## Функции
- Просмотр списка книг и глав из локальных JSON.
- Сохранение закладок в таблицу `bookmarks` Supabase (анон-ключ, RLS-политики должны это разрешать).

> Пример считывает главы из структуры `books[].chapters[]` как в JSON ваших локальных файлов.

## Кастомизация отображения текста (где менять)

В `lib/main.dart` есть два места, отвечающие за стиль номера стиха и отступы.

1) Отрывки из закладок (элемент `RichText`):
```
// ищите по маркеру: "filtered.map((v)" в BookmarkReadPage
TextSpan(
  text: '$numLabel   ', // тут 3 пробела после номера
  style: Theme.of(context).textTheme.bodySmall?.copyWith(
    fontWeight: FontWeight.w400,
    color: Theme.of(context).textTheme.bodySmall?.color?.withOpacity(0.6),
  ),
),
```

2) Экран главы (элемент `RichText`):
```
TextSpan(
  text: '$numLabel   ',
  style: Theme.of(context).textTheme.bodySmall?.copyWith(
    fontWeight: FontWeight.w400,
    color: Theme.of(context).textTheme.bodySmall?.color?.withOpacity(0.6),
  ),
),
```

Можно менять количество пробелов, прозрачность (0.6), базовый стиль (`bodySmall` → `labelSmall`) и т.д.




