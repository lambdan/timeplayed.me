-- add search column to game
ALTER TABLE "game" ADD COLUMN search VARCHAR(255) NOT NULL DEFAULT '';

-- enable pg_trgm extension for fuzzy searching
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- create trigram index on game search column
CREATE INDEX game_search_trgm_idx ON "game" USING gin (search gin_trgm_ops);
