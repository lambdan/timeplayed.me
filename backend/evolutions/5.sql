-- the default platform setting was removed, activity without a platform gets the unknown platform
ALTER TABLE "user" DROP COLUMN default_platform_id;
