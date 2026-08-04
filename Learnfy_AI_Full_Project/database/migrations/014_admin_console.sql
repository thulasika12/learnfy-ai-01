-- Learnfy AI migration 014: professional admin console and moderation
-- Idempotent and non-destructive for existing data.

SET @schema_name = DATABASE();

SET @sql = IF((SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=@schema_name AND TABLE_NAME='notes' AND COLUMN_NAME='is_hidden')=0,
  'ALTER TABLE notes ADD COLUMN is_hidden BOOLEAN NOT NULL DEFAULT FALSE AFTER is_reported', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql = IF((SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=@schema_name AND TABLE_NAME='resources' AND COLUMN_NAME='is_hidden')=0,
  'ALTER TABLE resources ADD COLUMN is_hidden BOOLEAN NOT NULL DEFAULT FALSE AFTER teacher_id', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql = IF((SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=@schema_name AND TABLE_NAME='study_groups' AND COLUMN_NAME='is_hidden')=0,
  'ALTER TABLE study_groups ADD COLUMN is_hidden BOOLEAN NOT NULL DEFAULT FALSE AFTER creator_id', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

CREATE TABLE IF NOT EXISTS content_reports (
  id INT AUTO_INCREMENT PRIMARY KEY,
  reporter_id INT NULL,
  target_type VARCHAR(30) NOT NULL,
  target_id INT NOT NULL,
  reason VARCHAR(1000) NOT NULL,
  status ENUM('pending','dismissed','hidden','deleted') NOT NULL DEFAULT 'pending',
  resolution_note TEXT NULL,
  reviewed_by INT NULL,
  reviewed_at DATETIME NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_content_reports_reporter FOREIGN KEY (reporter_id) REFERENCES users(id) ON DELETE SET NULL,
  CONSTRAINT fk_content_reports_reviewer FOREIGN KEY (reviewed_by) REFERENCES users(id) ON DELETE SET NULL,
  INDEX idx_content_reports_status_created (status, created_at),
  INDEX idx_content_reports_target (target_type, target_id)
) ENGINE=InnoDB;
