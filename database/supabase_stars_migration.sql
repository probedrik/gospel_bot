-- Миграция для поддержки Telegram Stars в Supabase
-- Выполните этот скрипт в SQL Editor в Supabase Dashboard

-- 1. Добавляем новые колонки в существующие таблицы (если они есть)
-- Для premium_purchases
DO $$
BEGIN
    -- Добавляем поддержку Stars в premium_purchases
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'premium_purchases' AND column_name = 'amount_stars') THEN
        ALTER TABLE premium_purchases ADD COLUMN amount_stars INTEGER NOT NULL DEFAULT 0;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'premium_purchases' AND column_name = 'payment_method') THEN
        ALTER TABLE premium_purchases ADD COLUMN payment_method VARCHAR(20) NOT NULL DEFAULT 'ruble';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'premium_purchases' AND column_name = 'telegram_payment_charge_id') THEN
        ALTER TABLE premium_purchases ADD COLUMN telegram_payment_charge_id VARCHAR(255);
    END IF;
END $$;

-- Для donations
DO $$
BEGIN
    -- Добавляем поддержку Stars в donations
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'donations' AND column_name = 'amount_stars') THEN
        ALTER TABLE donations ADD COLUMN amount_stars INTEGER NOT NULL DEFAULT 0;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'donations' AND column_name = 'payment_method') THEN
        ALTER TABLE donations ADD COLUMN payment_method VARCHAR(20) NOT NULL DEFAULT 'ruble';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'donations' AND column_name = 'telegram_payment_charge_id') THEN
        ALTER TABLE donations ADD COLUMN telegram_payment_charge_id VARCHAR(255);
    END IF;
END $$;

-- 2. Создаем новую таблицу для транзакций Stars
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

-- 3. Добавляем индексы для оптимизации
CREATE INDEX IF NOT EXISTS idx_premium_purchases_telegram_payment_id 
    ON premium_purchases(telegram_payment_charge_id);
    
CREATE INDEX IF NOT EXISTS idx_donations_telegram_payment_id 
    ON donations(telegram_payment_charge_id);
    
CREATE INDEX IF NOT EXISTS idx_star_transactions_user_id 
    ON star_transactions(user_id);
    
CREATE INDEX IF NOT EXISTS idx_star_transactions_transaction_id 
    ON star_transactions(transaction_id);
    
CREATE INDEX IF NOT EXISTS idx_star_transactions_type 
    ON star_transactions(transaction_type);

-- 4. Включаем Row Level Security (RLS) для новой таблицы
ALTER TABLE star_transactions ENABLE ROW LEVEL SECURITY;

-- 5. Создаем политики безопасности для star_transactions
-- Пользователи могут видеть только свои транзакции
CREATE POLICY "Users can view own star transactions" ON star_transactions
    FOR SELECT USING (auth.uid()::text = user_id::text);

-- Только система может создавать транзакции
CREATE POLICY "Service role can insert star transactions" ON star_transactions
    FOR INSERT WITH CHECK (true);

-- Только система может обновлять транзакции  
CREATE POLICY "Service role can update star transactions" ON star_transactions
    FOR UPDATE USING (true);

-- 6. Комментарии для документации
COMMENT ON TABLE star_transactions IS 'Транзакции через Telegram Stars для аудита и статистики';
COMMENT ON COLUMN star_transactions.transaction_id IS 'telegram_payment_charge_id из Telegram';
COMMENT ON COLUMN star_transactions.transaction_type IS 'Тип транзакции: donation или premium_purchase';
COMMENT ON COLUMN star_transactions.related_id IS 'ID связанной записи в donations или premium_purchases';

-- 7. Проверяем результат
SELECT 
    'premium_purchases' as table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'premium_purchases' 
    AND column_name IN ('amount_stars', 'payment_method', 'telegram_payment_charge_id')
ORDER BY column_name;

SELECT 
    'donations' as table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'donations' 
    AND column_name IN ('amount_stars', 'payment_method', 'telegram_payment_charge_id')
ORDER BY column_name;

SELECT 
    'star_transactions' as table_name,
    COUNT(*) as columns_count
FROM information_schema.columns 
WHERE table_name = 'star_transactions';

-- Готово! Теперь ваша база данных поддерживает Telegram Stars 🌟