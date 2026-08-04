-- Repeat-safe A/L catalogue migration. Existing learning records are untouched.
CREATE TABLE IF NOT EXISTS subjects (
 id INT AUTO_INCREMENT PRIMARY KEY, level VARCHAR(20) NOT NULL DEFAULT 'AL', stream VARCHAR(100) NOT NULL,
 subject_code VARCHAR(10) NOT NULL, name_en VARCHAR(255) NOT NULL, name_ta VARCHAR(255) NOT NULL,
 name_si VARCHAR(255) NOT NULL, description TEXT, is_active BOOLEAN NOT NULL DEFAULT TRUE,
 sort_order INT NOT NULL DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 UNIQUE KEY uq_subject_level_code (level,subject_code), INDEX idx_subject_level_active (level,is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE IF NOT EXISTS subject_streams (
 subject_id INT NOT NULL, stream VARCHAR(100) NOT NULL, PRIMARY KEY(subject_id,stream),
 FOREIGN KEY(subject_id) REFERENCES subjects(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO subjects(level,stream,subject_code,name_en,name_ta,name_si,sort_order) VALUES
('AL','Physical Science','01','Physics','இயற்பியல்','භෞතික විද්‍යාව',1),
('AL','Physical Science','02','Chemistry','வேதியியல்','රසායන විද්‍යාව',2),
('AL','Biological Science','08','Agricultural Science','விவசாய விஞ்ஞானம்','කෘෂි විද්‍යාව',8),
('AL','Biological Science','09','Biology','உயிரியல்','ජීව විද්‍යාව',9),
('AL','Physical Science','10','Combined Mathematics','இணைந்த கணிதம்','සංයුක්ත ගණිතය',10),
('AL','Physical Science','11','Higher Mathematics','உயர் கணிதம்','උසස් ගණිතය',11),
('AL','General/Common Subjects','12','Common General Test','பொது பொது பரீட்சை','සාමාන්‍ය පොදු පරීක්ෂණය',12),
('AL','General/Common Subjects','13','General English','பொது ஆங்கிலம்','සාමාන්‍ය ඉංග්‍රීසි',13),
('AL','Engineering Technology','14','Civil Technology','சிவில் தொழில்நுட்பம்','සිවිල් තාක්ෂණය',14),
('AL','Engineering Technology','15','Mechanical Technology','இயந்திர தொழில்நுட்பம்','යාන්ත්‍රික තාක්ෂණය',15),
('AL','Engineering Technology','16','Electrical, Electronic and Information Technology','மின், மின்னணு மற்றும் தகவல் தொழில்நுட்பம்','විදුලි, ඉලෙක්ට්‍රොනික හා තොරතුරු තාක්ෂණය',16),
('AL','Bio Systems Technology','17','Food Technology','உணவுத் தொழில்நுட்பம்','ආහාර තාක්ෂණය',17),
('AL','Bio Systems Technology','18','Agro Technology','விவசாய தொழில்நுட்பம்','කෘෂි තාක්ෂණය',18),
('AL','Bio Systems Technology','19','Bio Resource Technology','உயிர் வள தொழில்நுட்பம்','ජෛව සම්පත් තාක්ෂණය',19),
('AL','Engineering Technology','20','Information and Communication Technology','தகவல் மற்றும் தொடர்பாடல் தொழில்நுட்பம்','තොරතුරු හා සන්නිවේදන තාක්ෂණය',1),
('AL','Commerce','21','Economics','பொருளியல்','ආර්ථික විද්‍යාව',21),
('AL','Arts','22','Geography','புவியியல்','භූගෝල විද්‍යාව',22),
('AL','Arts','23','Political Science','அரசியல் விஞ்ஞானம்','දේශපාලන විද්‍යාව',23),
('AL','Arts','24','Logic and Scientific Method','தர்க்கமும் விஞ்ஞான முறையும்','තර්ක ශාස්ත්‍රය හා විද්‍යාත්මක ක්‍රමය',24),
('AL','Arts','25A','History of Sri Lanka and India','இலங்கை மற்றும் இந்திய வரலாறு','ශ්‍රී ලංකා හා ඉන්දීය ඉතිහාසය',25),
('AL','Arts','25B','History of Sri Lanka and Europe','இலங்கை மற்றும் ஐரோப்பிய வரலாறு','ශ්‍රී ලංකා හා යුරෝපා ඉතිහාසය',26),
('AL','Arts','25C','History of Sri Lanka and Modern World','இலங்கை மற்றும் நவீன உலக வரலாறு','ශ්‍රී ලංකා හා නූතන ලෝක ඉතිහාසය',27),
('AL','Arts','28','Home Economics','மனைப் பொருளியல்','ගෘහ ආර්ථික විද්‍යාව',28),
('AL','Arts','29','Communication and Media Studies','தொடர்பாடல் மற்றும் ஊடகக் கற்கைகள்','සන්නිවේදනය හා මාධ්‍ය අධ්‍යයනය',29),
('AL','Commerce','31','Business Statistics','வணிகப் புள்ளிவிபரவியல்','ව්‍යාපාර සංඛ්‍යානය',31),
('AL','Commerce','32','Business Studies','வணிகக் கல்வி','ව්‍යාපාර අධ්‍යයනය',32),
('AL','Commerce','33','Accounting','கணக்கியல்','ගිණුම්කරණය',33),
('AL','Arts','41','Buddhism','பௌத்தம்','බුද්ධ ධර්මය',41),('AL','Arts','42','Hinduism','இந்து சமயம்','හින්දු ධර්මය',42),
('AL','Arts','43','Christianity','கிறிஸ்தவம்','ක්‍රිස්තියානි ධර්මය',43),('AL','Arts','44','Islam','இஸ்லாம்','ඉස්ලාම්',44),
('AL','Arts','45','Buddhist Civilization','பௌத்த நாகரிகம்','බෞද්ධ ශිෂ්ටාචාරය',45),('AL','Arts','46','Hindu Civilization','இந்து நாகரிகம்','හින්දු ශිෂ්ටාචාරය',46),
('AL','Arts','47','Islamic Civilization','இஸ்லாமிய நாகரிகம்','ඉස්ලාමීය ශිෂ්ටාචාරය',47),('AL','Arts','48','Greek and Roman Civilization','கிரேக்க ரோம நாகரிகம்','ග්‍රීක හා රෝම ශිෂ්ටාචාරය',48),
('AL','Arts','49','Christian Civilization','கிறிஸ்தவ நாகரிகம்','ක්‍රිස්තියානි ශිෂ්ටාචාරය',49),
('AL','Arts','51','Art','சித்திரம்','චිත්‍ර කලාව',51),('AL','Arts','52','Dancing (Indigenous)','நடனம் (சுதேச)','නර්තනය (දේශීය)',52),('AL','Arts','53','Dancing (Bharatha)','பரத நடனம்','භරත නර්තනය',53),
('AL','Arts','54','Oriental Music','கீழைத்தேய இசை','පෙරදිග සංගීතය',54),('AL','Arts','55','Carnatic Music','கர்நாடக இசை','කර්ණාටක සංගීතය',55),('AL','Arts','56','Western Music','மேற்கத்திய இசை','බටහිර සංගීතය',56),
('AL','Arts','57','Drama and Theatre (Sinhala)','நாடகமும் அரங்கியலும் (சிங்களம்)','නාට්‍ය හා රංග කලාව (සිංහල)',57),('AL','Arts','58','Drama and Theatre (Tamil)','நாடகமும் அரங்கியலும் (தமிழ்)','නාට්‍ය හා රංග කලාව (දෙමළ)',58),('AL','Arts','59','Drama and Theatre (English)','நாடகமும் அரங்கியலும் (ஆங்கிலம்)','නාට්‍ය හා රංග කලාව (ඉංග්‍රීසි)',59),
('AL','Engineering Technology','65','Engineering Technology','பொறியியல் தொழில்நுட்பம்','ඉංජිනේරු තාක්ෂණවේදය',2),('AL','Bio Systems Technology','66','Bio Systems Technology','உயிர் முறைமைகள் தொழில்நுட்பம்','ජෛව පද්ධති තාක්ෂණවේදය',2),('AL','Engineering Technology','67','Science for Technology','தொழில்நுட்பத்திற்கான விஞ்ஞானம்','තාක්ෂණවේදය සඳහා විද්‍යාව',3),
('AL','Arts','71','Sinhala','சிங்களம்','සිංහල',71),('AL','Arts','72','Tamil','தமிழ்','දෙමළ',72),('AL','Arts','73','English','ஆங்கிலம்','ඉංග්‍රීසි',73),('AL','Arts','74','Pali','பாளி','පාලි',74),('AL','Arts','75','Sanskrit','சமஸ்கிருதம்','සංස්කෘත',75),('AL','Arts','78','Arabic','அரபு','අරාබි',78),('AL','Arts','79','Malay','மலாய்','මැලේ',79),('AL','Arts','81','French','பிரெஞ்சு','ප්‍රංශ',81),('AL','Arts','82','German','ஜெர்மன்','ජර්මානු',82),('AL','Arts','83','Russian','ரஷ்ய','රුසියානු',83),('AL','Arts','84','Hindi','ஹிந்தி','හින්දි',84),('AL','Arts','86','Chinese','சீனம்','චීන',86),('AL','Arts','87','Japanese','ஜப்பானியம்','ජපන්',87),
('AL','General/Common Subjects','GIT','General Information Technology','பொது தகவல் தொழில்நுட்பம்','සාමාන්‍ය තොරතුරු තාක්ෂණය',90)
ON DUPLICATE KEY UPDATE name_en=VALUES(name_en),name_ta=VALUES(name_ta),name_si=VALUES(name_si),sort_order=VALUES(sort_order);

INSERT IGNORE INTO subject_streams(subject_id,stream)
SELECT s.id,m.stream FROM subjects s JOIN (
 SELECT '01' code,'Physical Science' stream UNION ALL SELECT '01','Biological Science' UNION ALL SELECT '02','Physical Science' UNION ALL SELECT '02','Biological Science'
 UNION ALL SELECT '08','Biological Science' UNION ALL SELECT '09','Biological Science' UNION ALL SELECT '10','Physical Science' UNION ALL SELECT '11','Physical Science'
 UNION ALL SELECT '20','Physical Science' UNION ALL SELECT '20','Commerce' UNION ALL SELECT '20','Engineering Technology' UNION ALL SELECT '20','Bio Systems Technology'
 UNION ALL SELECT '21','Commerce' UNION ALL SELECT '21','Arts' UNION ALL SELECT '31','Commerce' UNION ALL SELECT '32','Commerce' UNION ALL SELECT '33','Commerce'
 UNION ALL SELECT '14','Engineering Technology' UNION ALL SELECT '15','Engineering Technology' UNION ALL SELECT '16','Engineering Technology'
 UNION ALL SELECT '17','Bio Systems Technology' UNION ALL SELECT '18','Bio Systems Technology' UNION ALL SELECT '19','Bio Systems Technology'
 UNION ALL SELECT '65','Engineering Technology' UNION ALL SELECT '66','Bio Systems Technology' UNION ALL SELECT '67','Engineering Technology' UNION ALL SELECT '67','Bio Systems Technology'
 UNION ALL SELECT '12','General/Common Subjects' UNION ALL SELECT '13','General/Common Subjects' UNION ALL SELECT 'GIT','General/Common Subjects'
 UNION ALL SELECT '22','Arts' UNION ALL SELECT '23','Arts' UNION ALL SELECT '24','Arts' UNION ALL SELECT '25A','Arts' UNION ALL SELECT '25B','Arts' UNION ALL SELECT '25C','Arts' UNION ALL SELECT '28','Arts' UNION ALL SELECT '29','Arts'
 UNION ALL SELECT '41','Arts' UNION ALL SELECT '42','Arts' UNION ALL SELECT '43','Arts' UNION ALL SELECT '44','Arts' UNION ALL SELECT '45','Arts' UNION ALL SELECT '46','Arts' UNION ALL SELECT '47','Arts' UNION ALL SELECT '48','Arts' UNION ALL SELECT '49','Arts'
 UNION ALL SELECT '51','Arts' UNION ALL SELECT '52','Arts' UNION ALL SELECT '53','Arts' UNION ALL SELECT '54','Arts' UNION ALL SELECT '55','Arts' UNION ALL SELECT '56','Arts' UNION ALL SELECT '57','Arts' UNION ALL SELECT '58','Arts' UNION ALL SELECT '59','Arts'
 UNION ALL SELECT '71','Arts' UNION ALL SELECT '72','Arts' UNION ALL SELECT '73','Arts' UNION ALL SELECT '74','Arts' UNION ALL SELECT '75','Arts' UNION ALL SELECT '78','Arts' UNION ALL SELECT '79','Arts' UNION ALL SELECT '81','Arts' UNION ALL SELECT '82','Arts' UNION ALL SELECT '83','Arts' UNION ALL SELECT '84','Arts' UNION ALL SELECT '86','Arts' UNION ALL SELECT '87','Arts'
) m ON m.code=s.subject_code WHERE s.level='AL';
