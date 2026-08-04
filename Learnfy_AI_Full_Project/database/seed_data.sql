-- ============================================================
-- Learnfy AI — Idempotent sample data
-- ============================================================
-- Sample passwords:
--   admin@learnfy.ai   -> Admin@123
--   teacher@learnfy.ai -> Teacher@123
--   student@learnfy.ai -> Student@123
-- Change or remove these accounts before a public deployment.
-- ============================================================

USE learnfy_ai;

INSERT INTO users (name, email, password, role, is_verified_teacher, is_active)
VALUES
  ('Learnfy Admin', 'admin@learnfy.ai', '$2b$12$Ek3v5234RXmHcasesv3d..2uh8GoGXI2NlSKAe9ub0pFwfYb4EEvG', 'admin', TRUE, TRUE),
  ('Priya Teacher', 'teacher@learnfy.ai', '$2b$12$ec8YlotsSdbZ1uB62/hKwOhCKFbyF8k2vdZ7GMspOyfvCFN3TVnHS', 'teacher', TRUE, TRUE),
  ('Rahul Student', 'student@learnfy.ai', '$2b$12$lRpnwAlLEo3xBc1Y4HAnUukRqpCIGeCeEwC8TQuy3gl2j.bUO0mH2', 'student', FALSE, TRUE)
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  role = VALUES(role),
  is_verified_teacher = VALUES(is_verified_teacher),
  is_active = TRUE;

-- A seeded teacher must have the same audited approval state required by teacher routes.
INSERT INTO teacher_verifications (user_id, full_name, qualification, institution_name, subjects_taught, grades_taught, years_of_experience, proof_file_path, original_filename, status, reviewed_at, reviewed_by)
SELECT teacher.id, teacher.name, 'Seeded verified educator', 'Learnfy AI Demo', '["Mathematics"]', '["General"]', 1, 'seeded-account-no-document', NULL, 'approved', CURRENT_TIMESTAMP, admin.id
FROM users teacher JOIN users admin ON admin.email='admin@learnfy.ai'
WHERE teacher.email='teacher@learnfy.ai' AND NOT EXISTS (SELECT 1 FROM teacher_verifications tv WHERE tv.user_id=teacher.id AND tv.status='approved');

INSERT INTO study_groups (name, description, creator_id)
SELECT 'Physics Warriors', 'Group for physics preparation and doubt discussion', u.id
FROM users AS u
WHERE u.email = 'teacher@learnfy.ai'
  AND NOT EXISTS (SELECT 1 FROM study_groups WHERE name = 'Physics Warriors');

INSERT INTO study_groups (name, description, creator_id)
SELECT 'Data Structures Study Circle', 'Weekly DSA problem-solving sessions', u.id
FROM users AS u
WHERE u.email = 'student@learnfy.ai'
  AND NOT EXISTS (SELECT 1 FROM study_groups WHERE name = 'Data Structures Study Circle');

INSERT IGNORE INTO group_members (group_id, user_id, role)
SELECT
  g.id,
  u.id,
  CASE WHEN u.email = 'teacher@learnfy.ai' THEN 'admin' ELSE 'member' END
FROM study_groups AS g
JOIN users AS u ON u.email IN ('teacher@learnfy.ai', 'student@learnfy.ai')
WHERE g.name = 'Physics Warriors';

INSERT IGNORE INTO group_members (group_id, user_id, role)
SELECT g.id, u.id, 'admin'
FROM study_groups AS g
JOIN users AS u ON u.email = 'student@learnfy.ai'
WHERE g.name = 'Data Structures Study Circle';

-- Keep every group creator as its admin even when this seed is run again.
UPDATE group_members AS gm
JOIN study_groups AS sg ON sg.id = gm.group_id AND sg.creator_id = gm.user_id
SET gm.role = 'admin';
