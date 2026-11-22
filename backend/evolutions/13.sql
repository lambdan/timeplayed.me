-- who made the change, null when nobody did (eg Oblivionis sync)
ALTER TABLE history ADD COLUMN IF NOT EXISTS actor_id integer REFERENCES "user"(id) ON DELETE SET NULL;

-- backfill from the messages that named who made the change. The messages are kept
CREATE TEMP TABLE parsed (
    history_id integer PRIMARY KEY,
    message text NOT NULL,
    actor_name text,
    actor_id integer
) ON COMMIT DROP;

-- "Edited by admin X", "Game added by admin X", "Token 5 revoked by admin X"...
INSERT INTO parsed (history_id, message, actor_name)
SELECT id, m[1], m[2] FROM (
    SELECT id, regexp_match(message, '^(.*) by admin (.+)$') AS m
    FROM history WHERE actor_id IS NULL
) s WHERE m IS NOT NULL;

-- "Revoked 3 tokens (admin X)"
INSERT INTO parsed (history_id, message, actor_name)
SELECT id, m[1], m[2] FROM (
    SELECT id, regexp_match(message, '^(Revoked \d+ tokens) \(admin (.+)\)$') AS m
    FROM history WHERE actor_id IS NULL
) s WHERE m IS NOT NULL;

-- Discord commands: "Platform added by command by X", "Game added by SGDB ID by user X",
-- "Game added by IGDB ID by user X"
INSERT INTO parsed (history_id, message, actor_name)
SELECT id, m[1], m[2] FROM (
    SELECT id, regexp_match(message, '^(Platform added by command|Game added by [SI]GDB ID) by (?:user )?(.+)$') AS m
    FROM history WHERE actor_id IS NULL
) s WHERE m IS NOT NULL;

-- names are Discord usernames, only used when exactly one user has it
UPDATE parsed p SET actor_id = u.id
FROM "user" u
WHERE u.name = p.actor_name
    AND (SELECT count(*) FROM "user" WHERE name = p.actor_name) = 1;

-- "Game added by SGDB ID by user 5" had the user id instead (sometimes)
UPDATE parsed p SET actor_id = u.id
FROM "user" u
WHERE p.actor_id IS NULL AND p.actor_name ~ '^\d+$' AND u.id = p.actor_name::integer;

-- "Edited by admin X" and "Permissions set by admin X" were written last in the same
-- save as the changes they're about: the same thing, a lower id, and at most a couple
-- of seconds older
UPDATE history s SET actor_id = p.actor_id
FROM parsed p JOIN history e ON e.id = p.history_id
WHERE p.actor_id IS NOT NULL
    AND p.message IN ('Edited', 'Permissions set')
    AND s.actor_id IS NULL
    AND s.id < e.id
    AND s.timestamp >= e.timestamp - interval '2 seconds'
    AND s.id NOT IN (SELECT history_id FROM parsed)
    AND s.game_id IS NOT DISTINCT FROM e.game_id
    AND s.user_id IS NOT DISTINCT FROM e.user_id
    AND s.platform_id IS NOT DISTINCT FROM e.platform_id
    AND s.activity_id IS NOT DISTINCT FROM e.activity_id;

UPDATE history h SET actor_id = p.actor_id
FROM parsed p
WHERE h.id = p.history_id AND p.actor_id IS NOT NULL;
