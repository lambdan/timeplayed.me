ALTER TABLE "game" ADD COLUMN "parent_id" integer REFERENCES "game"(id) ON DELETE SET NULL;
