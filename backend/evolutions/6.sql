ALTER TABLE "activity" ADD COLUMN "history" text[] DEFAULT '{}';
ALTER TABLE "platform" ADD COLUMN "history" text[] DEFAULT '{}';
ALTER TABLE "game" ADD COLUMN "history" text[] DEFAULT '{}';
ALTER TABLE "user" ADD COLUMN "history" text[] DEFAULT '{}';
