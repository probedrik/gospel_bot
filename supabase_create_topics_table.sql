-- Создание таблицы для библейских тем в Supabase
-- Выполните этот скрипт в Supabase SQL Editor

CREATE TABLE IF NOT EXISTS bible_topics (
    id SERIAL PRIMARY KEY,
    topic_name TEXT NOT NULL UNIQUE,
    verses TEXT NOT NULL,  -- Строка со ссылками, разделенными "; "
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индекс для быстрого поиска по названию темы
CREATE INDEX IF NOT EXISTS idx_bible_topics_name ON bible_topics(topic_name);

-- Индекс для полнотекстового поиска по темам
CREATE INDEX IF NOT EXISTS idx_bible_topics_search ON bible_topics USING gin(to_tsvector('russian', topic_name));

-- Комментарии к таблице
COMMENT ON TABLE bible_topics IS 'Библейские темы и ссылки на стихи';
COMMENT ON COLUMN bible_topics.topic_name IS 'Название темы (например, "Божья защита")';
COMMENT ON COLUMN bible_topics.verses IS 'Ссылки на стихи, разделенные "; " (например, "Бытие 1:1; Псалом 22:1")';

-- Проверяем результат
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'bible_topics' 
ORDER BY ordinal_position; 