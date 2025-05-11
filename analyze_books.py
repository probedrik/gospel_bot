import pandas as pd

# Загрузка файла Excel
df = pd.read_excel('file.xlsx')

# Вывод основной информации
print(f"Количество книг в файле: {len(df)}")
print("\nСписок книг и их главы:")
print("=" * 60)
print(f"{'ID':<5} {'Название':<30} {'Главы':<10}")
print("=" * 60)

# Вывод всех книг с их ID и количеством глав (если доступно)
for index, row in df.iterrows():
    book_id = row.get('book', 'Н/Д')
    book_name = row.get('Книга Библии', 'Неизвестно')
    chapters = row.get('Главы', 'Н/Д')

    print(f"{book_id:<5} {book_name:<30} {chapters}")

print("\nПроверка конкретных книг:")
print("=" * 60)

# Проверка 2 Петра
book_60 = df[df['book'] == 60]
if not book_60.empty:
    print(
        f"ID 60: {book_60.iloc[0].get('Книга Библии', 'Не найдено')}, Главы: {book_60.iloc[0].get('Главы', 'Н/Д')}")
else:
    print("ID 60 не найден в файле")

book_61 = df[df['book'] == 61]
if not book_61.empty:
    print(
        f"ID 61: {book_61.iloc[0].get('Книга Библии', 'Не найдено')}, Главы: {book_61.iloc[0].get('Главы', 'Н/Д')}")
else:
    print("ID 61 не найден в файле")

book_47 = df[df['book'] == 47]
if not book_47.empty:
    print(
        f"ID 47: {book_47.iloc[0].get('Книга Библии', 'Не найдено')}, Главы: {book_47.iloc[0].get('Главы', 'Н/Д')}")
else:
    print("ID 47 не найден в файле")
