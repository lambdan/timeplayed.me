-- needed if updraging from < 5.1.0
-- add hidden bool to game
ALTER TABLE "game" ADD COLUMN "hidden" boolean NOT NULL DEFAULT false;
-- add hidden bool to activity
ALTER TABLE "activity" ADD COLUMN "hidden" boolean NOT NULL DEFAULT false;
