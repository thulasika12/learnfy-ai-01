-- ============================================================
-- Learnfy AI migration 002: Stripe payments and subscriptions
-- Repeat-safe and non-destructive. Existing user data is retained.
-- ============================================================

USE learnfy_ai;

CREATE TABLE IF NOT EXISTS payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    order_id VARCHAR(64) NOT NULL,
    provider VARCHAR(30) NOT NULL DEFAULT 'stripe',
    provider_payment_id VARCHAR(100) DEFAULT NULL,
    plan_code VARCHAR(30) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    currency CHAR(3) NOT NULL DEFAULT 'LKR',
    status VARCHAR(30) NOT NULL DEFAULT 'initiated',
    payment_method VARCHAR(50) DEFAULT NULL,
    status_message VARCHAR(255) DEFAULT NULL,
    paid_at DATETIME DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_payments_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uq_payments_order_id (order_id),
    INDEX idx_payments_user (user_id),
    INDEX idx_payments_provider_payment (provider_payment_id),
    INDEX idx_payments_status (status)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS subscriptions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    plan_code VARCHAR(30) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'active',
    current_period_start DATETIME NOT NULL,
    current_period_end DATETIME NOT NULL,
    source_payment_id INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_subscriptions_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_subscriptions_payment FOREIGN KEY (source_payment_id) REFERENCES payments(id) ON DELETE CASCADE,
    UNIQUE KEY uq_subscriptions_source_payment (source_payment_id),
    INDEX idx_subscriptions_user (user_id),
    INDEX idx_subscriptions_status (status),
    INDEX idx_subscriptions_period_end (current_period_end)
) ENGINE=InnoDB;
