-- Learnfy AI migration 003: complete flashcard system
-- Repeat-safe and non-destructive.
USE learnfy_ai;

CREATE TABLE IF NOT EXISTS flashcard_sets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    subject VARCHAR(100) NOT NULL,
    source_type VARCHAR(30) NOT NULL DEFAULT 'topic',
    source_name VARCHAR(255) DEFAULT NULL,
    language VARCHAR(5) NOT NULL DEFAULT 'en',
    difficulty VARCHAR(20) NOT NULL DEFAULT 'medium',
    is_favourite BOOLEAN NOT NULL DEFAULT FALSE,
    is_public BOOLEAN NOT NULL DEFAULT FALSE,
    share_token VARCHAR(100) DEFAULT NULL,
    share_expires_at DATETIME DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_flashcard_sets_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uq_flashcard_sets_share_token (share_token),
    INDEX idx_flashcard_sets_user (user_id),
    INDEX idx_flashcard_sets_subject (subject),
    INDEX idx_flashcard_sets_favourite (is_favourite)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS flashcards (
    id INT AUTO_INCREMENT PRIMARY KEY,
    set_id INT NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    image_url VARCHAR(500) DEFAULT NULL,
    is_favourite BOOLEAN NOT NULL DEFAULT FALSE,
    sort_order INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_flashcards_set FOREIGN KEY (set_id) REFERENCES flashcard_sets(id) ON DELETE CASCADE,
    INDEX idx_flashcards_set (set_id),
    INDEX idx_flashcards_favourite (is_favourite)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS flashcard_study_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    set_id INT NOT NULL,
    correct_count INT NOT NULL,
    incorrect_count INT NOT NULL,
    total_cards INT NOT NULL,
    score_percentage DOUBLE NOT NULL,
    duration_seconds INT NOT NULL,
    completed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_flashcard_sessions_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_flashcard_sessions_set FOREIGN KEY (set_id) REFERENCES flashcard_sets(id) ON DELETE CASCADE,
    INDEX idx_flashcard_sessions_user (user_id),
    INDEX idx_flashcard_sessions_set (set_id),
    INDEX idx_flashcard_sessions_completed (completed_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS flashcard_session_answers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    card_id INT NOT NULL,
    status VARCHAR(20) NOT NULL,
    answered_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_flashcard_answers_session FOREIGN KEY (session_id) REFERENCES flashcard_study_sessions(id) ON DELETE CASCADE,
    CONSTRAINT fk_flashcard_answers_card FOREIGN KEY (card_id) REFERENCES flashcards(id) ON DELETE CASCADE,
    INDEX idx_flashcard_answers_session (session_id),
    INDEX idx_flashcard_answers_card (card_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS flashcard_reminders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    is_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    reminder_time TIME NOT NULL,
    timezone VARCHAR(80) NOT NULL DEFAULT 'UTC',
    last_notified_at DATETIME DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_flashcard_reminders_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uq_flashcard_reminders_user (user_id)
) ENGINE=InnoDB;
