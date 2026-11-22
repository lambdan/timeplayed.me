-- PC activity with an unknown OS goes on the "pc" platform, instead of assuming Windows
INSERT INTO platform (abbreviation, name, icon)
VALUES ('pc', 'PC', 'pc-display')
ON CONFLICT (abbreviation) DO NOTHING;
UPDATE platform SET search = id || ' pc pc' WHERE abbreviation = 'pc';
INSERT INTO history (platform_id, message)
SELECT id, 'Created by evolution 12' FROM platform WHERE abbreviation = 'pc';

ALTER TABLE "user" ALTER COLUMN pc_platform SET DEFAULT 'pc';

-- users who never picked a PC platform got Windows by default, they get "pc" now
-- no history for this, it would be a row for almost every user
UPDATE "user" u SET pc_platform = 'pc'
WHERE pc_platform = 'win'
    AND NOT EXISTS (
        SELECT 1 FROM history h
        WHERE h.user_id = u.id AND h.message LIKE 'PC platform changed%'
    );
