-- ============================================================
-- Learnfy AI migration 001
-- Adds creator-admin roles and approval-based group membership.
-- Safe to run more than once.
-- ============================================================

USE learnfy_ai;

SET @role_column_exists = (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'group_members'
      AND COLUMN_NAME = 'role'
);

SET @role_column_sql = IF(
    @role_column_exists = 0,
    'ALTER TABLE group_members ADD COLUMN role ENUM(''admin'', ''member'') NOT NULL DEFAULT ''member'' AFTER user_id',
    'SELECT 1'
);

PREPARE role_column_statement FROM @role_column_sql;
EXECUTE role_column_statement;
DEALLOCATE PREPARE role_column_statement;

-- Backfill creator memberships, including groups left behind by an earlier
-- failed create request before this migration was installed.
INSERT IGNORE INTO group_members (group_id, user_id, role)
SELECT sg.id, sg.creator_id, 'admin'
FROM study_groups AS sg;

UPDATE group_members AS gm
JOIN study_groups AS sg
  ON sg.id = gm.group_id
 AND sg.creator_id = gm.user_id
SET gm.role = 'admin';

CREATE TABLE IF NOT EXISTS group_join_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    group_id INT NOT NULL,
    user_id INT NOT NULL,
    status ENUM('pending', 'approved', 'rejected') NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at DATETIME DEFAULT NULL,
    FOREIGN KEY (group_id) REFERENCES study_groups(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uniq_group_join_request (group_id, user_id),
    INDEX idx_group_join_request_status (group_id, status)
) ENGINE=InnoDB;
