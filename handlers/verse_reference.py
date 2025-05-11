async def get_verse_by_reference(state: FSMContext, reference: str) -> tuple:
    """
    Обработка ссылки на стих или главу в формате "Книга Глава:Стих" или "Книга Глава"
    Возвращает текст и имеет ли стих/глава продолжение
    """
    translation = await get_current_translation(state)

    try:
        # Распарсить ссылку
        book_name, chapter, verse = parse_reference(reference)
        if not book_name:
            return "Неверный формат ссылки. Используйте формат 'Книга Глава:Стих' или 'Книга Глава'", False

        # Получить ID книги
        book_id = bible_data.get_book_id_by_name(book_name)
        if not book_id:
            return f"Книга '{book_name}' не найдена.", False

        # Проверка допустимости главы
        # ПРИМЕЧАНИЕ: 2 Петра имеет ID 47 (не 61)
        max_chapter = bible_data.max_chapters.get(book_id, 0)

        logger.info(
            f"Запрос на стих: {book_name} (ID: {book_id}) глава {chapter}, макс. глав: {max_chapter}")

        if chapter < 1 or chapter > max_chapter:
            return f"Книга '{book_name}' содержит {max_chapter} глав. Укажите главу от 1 до {max_chapter}.", False

        # Получение текста: стих или вся глава
        if verse:
            # Сохраняем выбранную книгу и главу в состоянии
            await set_chosen_book(state, book_id)
            await set_current_chapter(state, chapter)

            result = await bible_api.get_verse(book_id, chapter, verse, translation)
            # Предполагаем, что у стиха есть продолжение (глава)
            has_continuation = True
        else:
            # Сохраняем выбранную книгу и главу в состоянии
            await set_chosen_book(state, book_id)
            await set_current_chapter(state, chapter)

            result = await bible_api.get_formatted_chapter(book_id, chapter, translation)

            # Проверка наличия следующей и предыдущей главы
            has_previous = chapter > 1
            has_next = chapter < max_chapter
            has_continuation = has_previous or has_next

        if result.startswith("Ошибка:"):
            return result, False

        return result, has_continuation
    except Exception as e:
        logger.error(
            f"Ошибка при обработке ссылки на стих: {e}", exc_info=True)
        return "Произошла ошибка при обработке ссылки. Пожалуйста, проверьте формат и попробуйте снова.", False
