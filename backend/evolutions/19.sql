-- colors for a game's tiles, like platforms have. Set by admins (picked from the cover with a
-- button in the admin game editor). Child games without their own use the parent's
ALTER TABLE game ADD COLUMN color_primary VARCHAR(6);
ALTER TABLE game ADD COLUMN color_secondary VARCHAR(6);
