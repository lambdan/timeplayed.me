-- the default platform setting was removed, activity always comes with a platform now
ALTER TABLE "user" DROP COLUMN default_platform_id;
