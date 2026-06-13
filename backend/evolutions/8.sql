-- enable pg_trgm extension
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- add search columns
ALTER TABLE "game" ADD COLUMN IF NOT EXISTS search VARCHAR(255) NOT NULL DEFAULT '';
ALTER TABLE "user" ADD COLUMN IF NOT EXISTS search VARCHAR(255) NOT NULL DEFAULT '';
ALTER TABLE "platform" ADD COLUMN IF NOT EXISTS search VARCHAR(255) NOT NULL DEFAULT '';

-- create trigram indexes
CREATE INDEX game_search_trgm_idx ON "game" USING gin (search gin_trgm_ops);
CREATE INDEX user_search_trgm_idx ON "user" USING gin (search gin_trgm_ops);
CREATE INDEX platform_search_trgm_idx ON "platform" USING gin (search gin_trgm_ops);
