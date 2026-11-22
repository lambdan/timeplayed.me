-- what Discord users are playing right now according to their presence, so the bot
-- can track sessions across restarts. One row per user, removed when the session ends
CREATE TABLE discordpresence (
    id serial PRIMARY KEY,
    discord_user_id varchar(255) NOT NULL UNIQUE,
    discord_user_name varchar(255) NOT NULL,
    game_name text NOT NULL,
    platform varchar(255) NOT NULL,
    started timestamp without time zone NOT NULL,
    discord_started timestamp without time zone,
    last_seen timestamp without time zone NOT NULL
);
