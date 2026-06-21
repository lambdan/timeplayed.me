-- backend 9.1.0
--
-- add display_name column to User
ALTER TABLE "user" ADD COLUMN "display_name" VARCHAR(255) DEFAULT NULL;
-- populate display_name with name for existing users
UPDATE "user" SET "display_name" = "name" WHERE "display_name" IS NULL;
-- make display_name not null
ALTER TABLE "user" ALTER COLUMN "display_name" SET NOT NULL;



