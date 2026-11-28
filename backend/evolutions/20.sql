-- colors for a user's tiles, like games and platforms have. Set by the user in settings
ALTER TABLE "user" ADD COLUMN color_primary VARCHAR(6);
ALTER TABLE "user" ADD COLUMN color_secondary VARCHAR(6);
