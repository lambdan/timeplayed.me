-- create new users table

CREATE TABLE users_new (
    id BIGINT PRIMARY KEY,
    discord_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    default_platform_id INTEGER NOT NULL REFERENCES platform(id),
    bot_commands_blocked BOOLEAN DEFAULT FALSE,
    pc_platform VARCHAR(255) DEFAULT 'pc'
);

-- copy over users, sorted by activity timestamps (eg oldest activity = oldest user)

INSERT INTO users_new (id, discord_id, name, default_platform_id, bot_commands_blocked, pc_platform)
SELECT
    ROW_NUMBER() OVER (ORDER BY first_activity) AS id,
    u.id,
    u.name,
    u.default_platform_id,
    u.bot_commands_blocked,
    u.pc_platform
FROM "user" u
LEFT JOIN (
    SELECT user_id, MIN(timestamp) AS first_activity
    FROM activity
    GROUP BY user_id
) a ON a.user_id = u.id
ORDER BY first_activity NULLS LAST;

-- mapping table

CREATE TEMP TABLE user_id_map AS
SELECT discord_id, id AS new_id
FROM users_new;

-- migrate activities

ALTER TABLE activity ADD COLUMN user_new_id BIGINT;

UPDATE activity a
SET user_new_id = m.new_id
FROM user_id_map m
WHERE a.user_id = m.discord_id;

ALTER TABLE activity DROP CONSTRAINT activity_user_id_fkey;
ALTER TABLE activity DROP COLUMN user_id;

ALTER TABLE activity RENAME COLUMN user_new_id TO user_id;

ALTER TABLE activity
ADD CONSTRAINT activity_user_id_fkey
FOREIGN KEY (user_id) REFERENCES users_new(id) ON DELETE CASCADE;

-- migrate live activity

ALTER TABLE liveactivity ADD COLUMN user_new_id BIGINT;

UPDATE liveactivity l
SET user_new_id = m.new_id
FROM user_id_map m
WHERE l.user_id = m.discord_id;

ALTER TABLE liveactivity DROP CONSTRAINT liveactivity_user_id_fkey;
ALTER TABLE liveactivity DROP COLUMN user_id;

ALTER TABLE liveactivity RENAME COLUMN user_new_id TO user_id;

ALTER TABLE liveactivity
ADD CONSTRAINT liveactivity_user_id_fkey
FOREIGN KEY (user_id) REFERENCES users_new(id) ON DELETE CASCADE;

-- replace user table

DROP TABLE "user";

ALTER TABLE users_new
RENAME TO "user";

-- drop temp table
DROP TABLE user_id_map;

-- fix auto-increment

CREATE SEQUENCE user_id_seq;

ALTER TABLE "user"
ALTER COLUMN id SET DEFAULT nextval('user_id_seq');

SELECT setval('user_id_seq', (SELECT MAX(id) FROM "user"));

-- done with migration!

-- add permissions array to users
ALTER TABLE "user"
ADD COLUMN permissions text[] DEFAULT '{"commands","manual_activity","oblivionis_sync"}';
ALTER TABLE "user" DROP COLUMN bot_commands_blocked;
