-- the presence tracker tracks every game a user plays at the same time, not only the
-- first one: one row per user, game and platform
ALTER TABLE discordpresence DROP CONSTRAINT discordpresence_discord_user_id_key;
CREATE UNIQUE INDEX discordpresence_user_game_platform
    ON discordpresence (discord_user_id, game_name, platform);
