-- Таблица для хранения динамических настроек ИИ
CREATE TABLE IF NOT EXISTS ai_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(100) NOT NULL UNIQUE,
    setting_value TEXT NOT NULL,
    setting_type VARCHAR(20) NOT NULL DEFAULT 'string', -- 'string', 'integer', 'float', 'boolean'
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Вставляем значения по умолчанию
INSERT INTO ai_settings (setting_key, setting_value, setting_type, description) VALUES
('ai_daily_limit', '3', 'integer', 'Дневной лимит ИИ запросов для обычных пользователей'),
('premium_package_price', '100', 'integer', 'Цена премиум пакета в рублях'),
('premium_package_requests', '30', 'integer', 'Количество запросов в премиум пакете'),
('admin_premium_mode', 'true', 'boolean', 'Использует ли админ премиум ИИ по умолчанию'),
('free_premium_users', '[]', 'string', 'JSON список пользователей с бесплатным премиум доступом')
ON CONFLICT (setting_key) DO NOTHING;

-- Индекс для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_ai_settings_key ON ai_settings(setting_key);