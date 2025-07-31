-- Миграция для Supabase: Создание таблиц для управления настройками ИИ и премиум доступом
-- Выполните этот скрипт в SQL Editor вашего Supabase проекта

-- 1. Таблица для хранения динамических настроек ИИ
CREATE TABLE IF NOT EXISTS ai_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(100) NOT NULL UNIQUE,
    setting_value TEXT NOT NULL,
    setting_type VARCHAR(20) NOT NULL DEFAULT 'string', -- 'string', 'integer', 'float', 'boolean'
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Таблица для хранения премиум запросов пользователей
CREATE TABLE IF NOT EXISTS premium_requests (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    requests_count INTEGER NOT NULL DEFAULT 0,
    total_purchased INTEGER NOT NULL DEFAULT 0,
    total_used INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);

-- 3. Таблица для истории покупок премиум запросов
CREATE TABLE IF NOT EXISTS premium_purchases (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    requests_count INTEGER NOT NULL,
    amount_rub INTEGER NOT NULL,
    payment_id VARCHAR(255),
    payment_status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE NULL
);

-- 4. Таблица для пожертвований
CREATE TABLE IF NOT EXISTS donations (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    amount_rub INTEGER NOT NULL,
    payment_id VARCHAR(255),
    payment_status VARCHAR(50) DEFAULT 'pending',
    message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE NULL
);

-- Создание индексов для оптимизации
CREATE INDEX IF NOT EXISTS idx_ai_settings_key ON ai_settings(setting_key);
CREATE INDEX IF NOT EXISTS idx_premium_requests_user_id ON premium_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_premium_purchases_user_id ON premium_purchases(user_id);
CREATE INDEX IF NOT EXISTS idx_premium_purchases_payment_id ON premium_purchases(payment_id);
CREATE INDEX IF NOT EXISTS idx_donations_user_id ON donations(user_id);
CREATE INDEX IF NOT EXISTS idx_donations_payment_id ON donations(payment_id);

-- Вставляем значения по умолчанию для настроек ИИ
INSERT INTO ai_settings (setting_key, setting_value, setting_type, description) VALUES
('ai_daily_limit', '3', 'integer', 'Дневной лимит ИИ запросов для обычных пользователей'),
('premium_package_price', '100', 'integer', 'Цена премиум пакета в рублях'),
('premium_package_requests', '30', 'integer', 'Количество запросов в премиум пакете'),
('admin_premium_mode', 'true', 'boolean', 'Использует ли админ премиум ИИ по умолчанию'),
('free_premium_users', '[]', 'string', 'JSON список пользователей с бесплатным премиум доступом')
ON CONFLICT (setting_key) DO NOTHING;

-- Создание функции для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Создание триггеров для автоматического обновления updated_at
CREATE TRIGGER update_ai_settings_updated_at 
    BEFORE UPDATE ON ai_settings 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_premium_requests_updated_at 
    BEFORE UPDATE ON premium_requests 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Включение Row Level Security (RLS) для безопасности
ALTER TABLE ai_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE premium_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE premium_purchases ENABLE ROW LEVEL SECURITY;
ALTER TABLE donations ENABLE ROW LEVEL SECURITY;

-- Создание политик безопасности (настройте под ваши нужды)
-- Пример: разрешить все операции для сервисной роли
CREATE POLICY "Allow service role full access on ai_settings" ON ai_settings
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Allow service role full access on premium_requests" ON premium_requests
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Allow service role full access on premium_purchases" ON premium_purchases
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Allow service role full access on donations" ON donations
    FOR ALL USING (auth.role() = 'service_role');

-- Комментарии к таблицам для документации
COMMENT ON TABLE ai_settings IS 'Динамические настройки ИИ системы';
COMMENT ON TABLE premium_requests IS 'Премиум запросы пользователей';
COMMENT ON TABLE premium_purchases IS 'История покупок премиум запросов';
COMMENT ON TABLE donations IS 'История пожертвований пользователей';

-- Комментарии к важным колонкам
COMMENT ON COLUMN ai_settings.setting_key IS 'Уникальный ключ настройки';
COMMENT ON COLUMN ai_settings.setting_type IS 'Тип данных: string, integer, float, boolean';
COMMENT ON COLUMN premium_requests.requests_count IS 'Текущее количество доступных премиум запросов';
COMMENT ON COLUMN premium_requests.total_purchased IS 'Общее количество купленных запросов';
COMMENT ON COLUMN premium_requests.total_used IS 'Общее количество использованных запросов';

-- Проверка создания таблиц
DO $$
BEGIN
    RAISE NOTICE 'Миграция завершена успешно!';
    RAISE NOTICE 'Созданы таблицы:';
    RAISE NOTICE '- ai_settings (настройки ИИ)';
    RAISE NOTICE '- premium_requests (премиум запросы)';
    RAISE NOTICE '- premium_purchases (покупки)';
    RAISE NOTICE '- donations (пожертвования)';
    RAISE NOTICE 'Созданы индексы и триггеры для оптимизации';
    RAISE NOTICE 'Настроена Row Level Security';
END $$;