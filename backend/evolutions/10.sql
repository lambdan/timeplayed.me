-- backend 9.1.0
-- add display_name column to User
ALTER TABLE "user" ADD COLUMN "display_name" VARCHAR(255) DEFAULT NULL;



