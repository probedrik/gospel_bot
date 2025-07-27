-- Создание таблицы bookmarks в Supabase с новой структурой
-- Поддержка диапазонов глав и стихов

-- Удаляем старую таблицу если нужно (ОСТОРОЖНО! Это удалит все данные)
-- DROP TABLE IF EXISTS bookmarks;

-- Создаем новую таблицу bookmarks
CREATE TABLE IF NOT EXISTS bookmarks (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    book_id INTEGER NOT NULL,
    chapter_start INTEGER NOT NULL,
    chapter_end INTEGER,
    verse_start INTEGER,
    verse_end INTEGER,
    display_text TEXT,
    note TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Создаем индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_bookmarks_user_id 
ON bookmarks(user_id);

CREATE INDEX IF NOT EXISTS idx_bookmarks_chapters 
ON bookmarks(user_id, book_id, chapter_start, chapter_end);

CREATE INDEX IF NOT EXISTS idx_bookmarks_verses 
ON bookmarks(user_id, book_id, chapter_start, verse_start, verse_end);

-- Включаем Row Level Security (RLS)
ALTER TABLE bookmarks ENABLE ROW LEVEL SECURITY;

-- Создаем политику безопасности: пользователи могут видеть только свои закладки
CREATE POLICY "Users can view own bookmarks" ON bookmarks
    FOR SELECT USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can insert own bookmarks" ON bookmarks
    FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

CREATE POLICY "Users can update own bookmarks" ON bookmarks
    FOR UPDATE USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can delete own bookmarks" ON bookmarks
    FOR DELETE USING (auth.uid()::text = user_id::text);