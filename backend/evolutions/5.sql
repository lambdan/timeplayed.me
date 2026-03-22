-- needed if updraging from < 5.1.0
-- adds hidden bool to game table
ALTER TABLE "game" ADD COLUMN "hidden" boolean NOT NULL DEFAULT false;
