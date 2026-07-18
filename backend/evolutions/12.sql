-- remove steam id
ALTER TABLE game DROP COLUMN steam_id;

-- add history table 


create table history (
    id serial primary key,
    timestamp timestamp with time zone default now(),
    game_id integer references game(id) on delete cascade,
    user_id integer references "user"(id) on delete cascade,
    platform_id integer references platform(id) on delete cascade,
    activity_id integer references activity(id) on delete cascade,
    message text
);

-- migrate data from history columns to history table

-- Game history
INSERT INTO history (timestamp, game_id, message)
SELECT
    m[1]::timestamptz,
    g.id,
    m[2]
FROM game g
CROSS JOIN LATERAL unnest(g.history) AS entry
CROSS JOIN LATERAL regexp_matches(
    entry,
    '^\[(.*?)\]\s*(.*)$'
) AS m;

-- User history
INSERT INTO history (timestamp, user_id, message)
SELECT
    m[1]::timestamptz,
    u.id,
    m[2]
FROM "user" u
CROSS JOIN LATERAL unnest(u.history) AS entry
CROSS JOIN LATERAL regexp_matches(
    entry,
    '^\[(.*?)\]\s*(.*)$'
) AS m;

-- Platform history
INSERT INTO history (timestamp, platform_id, message)
SELECT
    m[1]::timestamptz,
    p.id,
    m[2]
FROM platform p
CROSS JOIN LATERAL unnest(p.history) AS entry
CROSS JOIN LATERAL regexp_matches(
    entry,
    '^\[(.*?)\]\s*(.*)$'
) AS m;

-- Activity history 
INSERT INTO history (timestamp, activity_id, message)
SELECT
    m[1]::timestamptz,
    a.id,
    m[2]
FROM activity a
CROSS JOIN LATERAL unnest(a.history) AS entry
CROSS JOIN LATERAL regexp_matches(
    entry,
    '^\[(.*?)\]\s*(.*)$'
) AS m;




-- drop old columns

ALTER TABLE game DROP COLUMN history;
ALTER TABLE activity DROP COLUMN history;
ALTER TABLE "user" DROP COLUMN history;
ALTER TABLE platform DROP COLUMN history;

