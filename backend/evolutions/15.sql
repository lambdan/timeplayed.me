-- add steam id
-- default null
-- unique
ALTER TABLE game ADD COLUMN steam_id INT NULL UNIQUE;
