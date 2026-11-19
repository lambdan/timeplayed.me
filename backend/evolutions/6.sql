-- cover art can be turned off for a game, this was image_url '-' before
ALTER TABLE game ADD COLUMN cover_disabled boolean NOT NULL DEFAULT false;
UPDATE game SET cover_disabled = true, image_url = NULL WHERE image_url = '-';
