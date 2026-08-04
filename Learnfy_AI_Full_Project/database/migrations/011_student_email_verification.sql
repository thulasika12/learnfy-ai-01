-- Preserve existing accounts while requiring verification for new registrations.
ALTER TABLE users
  ADD COLUMN is_email_verified BOOLEAN NOT NULL DEFAULT TRUE AFTER is_verified_teacher,
  ADD COLUMN student_verification_status ENUM('unverified','pending','verified','rejected') NOT NULL DEFAULT 'unverified' AFTER is_email_verified,
  ADD COLUMN student_verified_at DATETIME NULL AFTER student_verification_status,
  ADD COLUMN student_verified_by INT NULL AFTER student_verified_at,
  ADD CONSTRAINT fk_users_student_verified_by FOREIGN KEY (student_verified_by) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE users ALTER COLUMN is_email_verified SET DEFAULT FALSE;

CREATE TABLE email_verification_codes (
  id INT AUTO_INCREMENT PRIMARY KEY, user_id INT NOT NULL, code_hash VARCHAR(64) NOT NULL,
  expires_at DATETIME NOT NULL, attempts INT NOT NULL DEFAULT 0, is_used BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  INDEX idx_email_codes_user_created (user_id, created_at)
) ENGINE=InnoDB;

CREATE TABLE student_verifications (
  id INT AUTO_INCREMENT PRIMARY KEY, user_id INT NOT NULL, proof_file_path VARCHAR(500) NOT NULL,
  original_filename VARCHAR(255) NOT NULL, status ENUM('pending','verified','rejected') NOT NULL DEFAULT 'pending',
  rejection_reason TEXT NULL, submitted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  reviewed_at DATETIME NULL, reviewed_by INT NULL,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (reviewed_by) REFERENCES users(id) ON DELETE SET NULL,
  INDEX idx_student_verifications_status_submitted (status, submitted_at)
) ENGINE=InnoDB;

-- Academic fields are retained and optional. This is repeat-safe for current schema definitions.
ALTER TABLE users MODIFY academic_level VARCHAR(20) NULL, MODIFY academic_stream VARCHAR(100) NULL, MODIFY academic_subject VARCHAR(255) NULL;
ALTER TABLE user_academic_profiles MODIFY education_level_id INT NULL, MODIFY grade_id INT NULL, MODIFY stream_id INT NULL, MODIFY medium VARCHAR(10) NULL, MODIFY school_name VARCHAR(255) NULL, MODIFY district VARCHAR(100) NULL;
