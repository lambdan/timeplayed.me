-- needed if updraging from < 5.1.0
-- adds hidden bool to game table
ALTER TABLE "game" ADD COLUMN "hidden" boolean NOT NULL DEFAULT false;
-- add auto_hidden and manually_hidden to activity
ALTER TABLE "activity" ADD COLUMN "hidden" boolean NOT NULL DEFAULT false;
