-- Таблица для хранения премиум запросов пользователей
CREATE TABLE IF NOT EXISTS premium_requests (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    requests_count INTEGER NOT NULL DEFAULT 0,
    total_purchased INTEGER NOT NULL DEFAULT 0,
    total_used INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- Таблица для истории покупок премиум запросов
CREATE TABLE IF NOT EXISTS premium_purchases (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    requests_count INTEGER NOT NULL,
    amount_rub INTEGER NOT NULL,
    payment_id VARCHAR(255),
    payment_status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL
);

-- Таблица для пожертвований
CREATE TABLE IF NOT EXISTS donations (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    amount_rub INTEGER NOT NULL,
    payment_id VARCHAR(255),
    payment_status VARCHAR(50) DEFAULT 'pending',
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL
);

-- Индексы для оптимизации
CREATE INDEX IF NOT EXISTS idx_premium_requests_user_id ON premium_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_premium_purchases_user_id ON premium_purchases(user_id);
CREATE INDEX IF NOT EXISTS idx_premium_purchases_payment_id ON premium_purchases(payment_id);
CREATE INDEX IF NOT EXISTS idx_donations_user_id ON donations(user_id);
CREATE INDEX IF NOT EXISTS idx_donations_payment_id ON donations(payment_id);