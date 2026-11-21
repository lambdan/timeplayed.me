-- a game's cover: uploaded by an admin, or IGDB's. One per game, the image is an ImageFile
-- (see 8.sql) and its smaller versions point to it. SteamGridDB and image URLs are gone
CREATE TABLE game_cover (
    game_id integer PRIMARY KEY REFERENCES game (id) ON DELETE CASCADE,
    image_id uuid NOT NULL REFERENCES imagefile (id) ON DELETE CASCADE,
    -- 'upload' or 'igdb'
    source varchar(255) NOT NULL,
    -- for 'igdb': the IGDB ID it's the cover of (if the game's changes, it's looked up again)
    igdb_id integer,
    created timestamp with time zone NOT NULL DEFAULT now()
);
ALTER TABLE game DROP COLUMN sgdb_id;
ALTER TABLE game DROP COLUMN image_url;
-- the game's page on IGDB, it's not made from the IGDB ID. Set when IGDB is asked about the game
ALTER TABLE game ADD COLUMN igdb_url text;
