-- backend 8.1.0
-- add sgdb grid id  
ALTER TABLE "game" ADD COLUMN "sgdb_grid_id" integer default null;
