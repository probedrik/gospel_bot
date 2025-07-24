-- Создание таблицы для AI лимитов
CREATE TABLE IF NOT EXISTS ai_limits (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    date DATE NOT NULL,
    count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, date)
);

-- Создание индексов для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_ai_limits_user_date ON ai_limits(user_id, date);
CREATE INDEX IF NOT EXISTS idx_ai_limits_date ON ai_limits(date);

-- Создание таблицы для сохраненных толкований
CREATE TABLE IF NOT EXISTS saved_commentaries (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    book_id INTEGER NOT NULL,
    chapter_start INTEGER NOT NULL,
    chapter_end INTEGER,
    verse_start INTEGER,
    verse_end INTEGER,
    reference_text TEXT NOT NULL, -- полная ссылка типа "Лк 6:1-11" или "Быт 1:1-2:25"
    commentary_text TEXT NOT NULL,
    commentary_type VARCHAR(50) NOT NULL, -- 'ai' или 'lopukhin'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Создание индексов для быстрого поиска толкований
CREATE INDEX IF NOT EXISTS idx_saved_commentaries_user ON saved_commentaries(user_id);
CREATE INDEX IF NOT EXISTS idx_saved_commentaries_reference ON saved_commentaries(user_id, book_id, chapter_start);
CREATE INDEX IF NOT EXISTS idx_saved_commentaries_full ON saved_commentaries(user_id, book_id, chapter_start, chapter_end, verse_start, verse_end);

-- Отключаем Row Level Security для работы через сервисный ключ
ALTER TABLE ai_limits DISABLE ROW LEVEL SECURITY;
ALTER TABLE saved_commentaries DISABLE ROW LEVEL SECURITY;

-- Создаем роль для бота (опционально, для будущего использования)
-- DO $$ 
-- BEGIN
--     IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'bible_bot_role') THEN
--         CREATE ROLE bible_bot_role;
--     END IF;
-- END $$;

-- Предоставляем полные права на таблицы для сервисного ключа
GRANT ALL ON ai_limits TO service_role;
GRANT ALL ON saved_commentaries TO service_role;
GRANT ALL ON ai_limits TO anon;
GRANT ALL ON saved_commentaries TO anon;

-- Комментарии к таблицам
COMMENT ON TABLE ai_limits IS 'Хранит лимиты AI запросов пользователей по дням';
COMMENT ON TABLE saved_commentaries IS 'Хранит сохраненные пользователями толкования к стихам';

COMMENT ON COLUMN ai_limits.user_id IS 'ID пользователя Telegram';
COMMENT ON COLUMN ai_limits.date IS 'Дата в формате YYYY-MM-DD';
COMMENT ON COLUMN ai_limits.count IS 'Количество AI запросов за день';

COMMENT ON COLUMN saved_commentaries.user_id IS 'ID пользователя Telegram';
COMMENT ON COLUMN saved_commentaries.book_id IS 'ID книги Библии';
COMMENT ON COLUMN saved_commentaries.chapter IS 'Номер главы';
COMMENT ON COLUMN saved_commentaries.verse_start IS 'Начальный стих (NULL для всей главы)';
COMMENT ON COLUMN saved_commentaries.verse_end IS 'Конечный стих (NULL для одного стиха)';
COMMENT ON COLUMN saved_commentaries.reference_text IS 'Полная ссылка для отображения';
COMMENT ON COLUMN saved_commentaries.commentary_text IS 'Текст толкования';
COMMENT ON COLUMN saved_commentaries.commentary_type IS 'Тип толкования: ai или lopukhin'; 