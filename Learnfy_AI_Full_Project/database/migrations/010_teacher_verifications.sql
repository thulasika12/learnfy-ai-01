CREATE TABLE IF NOT EXISTS teacher_verifications (
 id INT AUTO_INCREMENT PRIMARY KEY, user_id INT NOT NULL, full_name VARCHAR(150) NOT NULL,
 institution_name VARCHAR(255) NOT NULL, subjects_taught TEXT NOT NULL, grades_taught TEXT NOT NULL,
 years_of_experience INT NOT NULL, official_email VARCHAR(150) NULL, proof_file_path VARCHAR(500) NOT NULL,
 additional_information TEXT NULL, status ENUM('pending','approved','rejected') NOT NULL DEFAULT 'pending',
 rejection_reason TEXT NULL, submitted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, reviewed_at DATETIME NULL,
 reviewed_by INT NULL, pending_user_id INT GENERATED ALWAYS AS (CASE WHEN status='pending' THEN user_id ELSE NULL END) STORED,
 UNIQUE KEY uq_teacher_verification_pending_user(pending_user_id),
 INDEX idx_teacher_verifications_user(user_id), INDEX idx_teacher_verifications_status_submitted(status,submitted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
-- MySQL disallows ON DELETE CASCADE when the referenced column also feeds an
-- indexed generated column. The FK still enforces ownership integrity; the
-- SQLAlchemy relationship removes applications before deleting a user.
SET @q=IF((SELECT COUNT(*) FROM information_schema.referential_constraints WHERE constraint_schema=DATABASE() AND table_name='teacher_verifications' AND constraint_name='fk_teacher_verification_user')=0,'ALTER TABLE teacher_verifications ADD CONSTRAINT fk_teacher_verification_user FOREIGN KEY(user_id) REFERENCES users(id)','SELECT 1'); PREPARE s FROM @q; EXECUTE s; DEALLOCATE PREPARE s;
SET @q=IF((SELECT COUNT(*) FROM information_schema.referential_constraints WHERE constraint_schema=DATABASE() AND table_name='teacher_verifications' AND constraint_name='fk_teacher_verification_reviewer')=0,'ALTER TABLE teacher_verifications ADD CONSTRAINT fk_teacher_verification_reviewer FOREIGN KEY(reviewed_by) REFERENCES users(id) ON DELETE SET NULL','SELECT 1'); PREPARE s FROM @q; EXECUTE s; DEALLOCATE PREPARE s;
