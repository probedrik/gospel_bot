-- Создание таблиц для Telegram Stars платежей

-- Таблица для хранения транзакций Telegram Stars
CREATE TABLE IF NOT EXISTS star_transactions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    transaction_id VARCHAR(255) NOT NULL UNIQUE,
    amount_stars INTEGER NOT NULL,
    transaction_type VARCHAR(50) NOT NULL, -- 'donation' или 'premium_purchase'
    related_id INTEGER NULL, -- ID связанной записи в donations или premium_purchases
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL
);

-- Таблица для хранения премиум запросов пользователей
CREATE TABLE IF NOT EXISTS premium_requests (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE,
    requests_count INTEGER NOT NULL DEFAULT 0,
    total_purchased INTEGER NOT NULL DEFAULT 0,
    total_used INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица для хранения покупок премиум запросов
CREATE TABLE IF NOT EXISTS premium_purchases (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    requests_count INTEGER NOT NULL,
    amount_rub DECIMAL(10,2) NULL, -- для рублевых платежей
    amount_stars INTEGER NULL, -- для Stars платежей
    payment_method VARCHAR(20) NOT NULL DEFAULT 'ruble', -- 'ruble' или 'stars'
    payment_id VARCHAR(255) NULL, -- для YooKassa
    telegram_payment_charge_id VARCHAR(255) NULL, -- для Stars платежей
    payment_status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL
);

-- Таблица для хранения пожертвований
CREATE TABLE IF NOT EXISTS donations (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    amount_rub DECIMAL(10,2) NULL, -- для рублевых пожертвований
    amount_stars INTEGER NULL, -- для Stars пожертвований
    payment_method VARCHAR(20) NOT NULL DEFAULT 'ruble', -- 'ruble' или 'stars'
    payment_id VARCHAR(255) NULL, -- для YooKassa
    telegram_payment_charge_id VARCHAR(255) NULL, -- для Stars платежей
    payment_status VARCHAR(50) DEFAULT 'pending',
    message TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL
);

-- Индексы для оптимизации
CREATE INDEX IF NOT EXISTS idx_star_transactions_user_id ON star_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_star_transactions_transaction_id ON star_transactions(transaction_id);
CREATE INDEX IF NOT EXISTS idx_star_transactions_type ON star_transactions(transaction_type);

CREATE INDEX IF NOT EXISTS idx_premium_requests_user_id ON premium_requests(user_id);

CREATE INDEX IF NOT EXISTS idx_premium_purchases_user_id ON premium_purchases(user_id);
CREATE INDEX IF NOT EXISTS idx_premium_purchases_payment_id ON premium_purchases(payment_id);
CREATE INDEX IF NOT EXISTS idx_premium_purchases_telegram_payment_id ON premium_purchases(telegram_payment_charge_id);

CREATE INDEX IF NOT EXISTS idx_donations_user_id ON donations(user_id);
CREATE INDEX IF NOT EXISTS idx_donations_payment_id ON donations(payment_id);
CREATE INDEX IF NOT EXISTS idx_donations_telegram_payment_id ON donations(telegram_payment_charge_id);

-- Триггер для автоматического обновления updated_at в premium_requests
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_premium_requests_updated_at 
    BEFORE UPDATE ON premium_requests 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Комментарии к таблицам
COMMENT ON TABLE star_transactions IS 'Транзакции через Telegram Stars для аудита и статистики';
COMMENT ON TABLE premium_requests IS 'Баланс премиум запросов пользователей';
COMMENT ON TABLE premium_purchases IS 'История покупок премиум запросов';
COMMENT ON TABLE donations IS 'История пожертвований пользователей';

-- Комментарии к колонкам
COMMENT ON COLUMN star_transactions.transaction_id IS 'telegram_payment_charge_id из Telegram';
COMMENT ON COLUMN star_transactions.transaction_type IS 'Тип транзакции: donation или premium_purchase';
COMMENT ON COLUMN star_transactions.related_id IS 'ID связанной записи в donations или premium_purchases';

COMMENT ON COLUMN premium_requests.requests_count IS 'Текущее количество доступных премиум запросов';
COMMENT ON COLUMN premium_requests.total_purchased IS 'Общее количество купленных запросов';
COMMENT ON COLUMN premium_requests.total_used IS 'Общее количество использованных запросов';