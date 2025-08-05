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
    amount_rub INTEGER NOT NULL DEFAULT 0,
    amount_stars INTEGER NOT NULL DEFAULT 0,
    payment_method VARCHAR(20) NOT NULL DEFAULT 'ruble', -- 'ruble' или 'stars'
    payment_id VARCHAR(255),
    telegram_payment_charge_id VARCHAR(255), -- для Stars платежей
    payment_status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL
);

-- Таблица для пожертвований
CREATE TABLE IF NOT EXISTS donations (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    amount_rub INTEGER NOT NULL DEFAULT 0,
    amount_stars INTEGER NOT NULL DEFAULT 0,
    payment_method VARCHAR(20) NOT NULL DEFAULT 'ruble', -- 'ruble' или 'stars'
    payment_id VARCHAR(255),
    telegram_payment_charge_id VARCHAR(255), -- для Stars платежей
    payment_status VARCHAR(50) DEFAULT 'pending',
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL
);

-- Таблица для отслеживания транзакций Telegram Stars
CREATE TABLE IF NOT EXISTS star_transactions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    transaction_id VARCHAR(255) NOT NULL,
    amount_stars INTEGER NOT NULL,
    transaction_type VARCHAR(50) NOT NULL, -- 'donation' или 'premium_purchase'
    related_id INTEGER, -- ID связанной записи (donations.id или premium_purchases.id)
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    UNIQUE(transaction_id)
);

-- Индексы для оптимизации
CREATE INDEX IF NOT EXISTS idx_premium_requests_user_id ON premium_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_premium_purchases_user_id ON premium_purchases(user_id);
CREATE INDEX IF NOT EXISTS idx_premium_purchases_payment_id ON premium_purchases(payment_id);
CREATE INDEX IF NOT EXISTS idx_premium_purchases_telegram_payment_id ON premium_purchases(telegram_payment_charge_id);
CREATE INDEX IF NOT EXISTS idx_donations_user_id ON donations(user_id);
CREATE INDEX IF NOT EXISTS idx_donations_payment_id ON donations(payment_id);
CREATE INDEX IF NOT EXISTS idx_donations_telegram_payment_id ON donations(telegram_payment_charge_id);
CREATE INDEX IF NOT EXISTS idx_star_transactions_user_id ON star_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_star_transactions_transaction_id ON star_transactions(transaction_id);
CREATE INDEX IF NOT EXISTS idx_star_transactions_type ON star_transactions(transaction_type);