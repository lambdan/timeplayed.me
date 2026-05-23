-- add history array to all tables
ALTER TABLE "activity" ADD COLUMN "history" text[] DEFAULT '{}';
ALTER TABLE "platform" ADD COLUMN "history" text[] DEFAULT '{}';
ALTER TABLE "game" ADD COLUMN "history" text[] DEFAULT '{}';
ALTER TABLE "user" ADD COLUMN "history" text[] DEFAULT '{}';

-- add created, updated columns
ALTER TABLE "activity" ADD COLUMN "created" timestamp with time zone DEFAULT now();
ALTER TABLE "platform" ADD COLUMN "created" timestamp with time zone DEFAULT now();
ALTER TABLE "game" ADD COLUMN "created" timestamp with time zone DEFAULT now();
ALTER TABLE "user" ADD COLUMN "created" timestamp with time zone DEFAULT now();

ALTER TABLE "activity" ADD COLUMN "updated" timestamp with time zone DEFAULT now();
ALTER TABLE "platform" ADD COLUMN "updated" timestamp with time zone DEFAULT now();
ALTER TABLE "game" ADD COLUMN "updated" timestamp with time zone DEFAULT now();
ALTER TABLE "user" ADD COLUMN "updated" timestamp with time zone DEFAULT now();

-- update existing Activity created, updated to timestamp
UPDATE "activity" SET created = timestamp;
UPDATE "activity" SET updated = timestamp;

-- update existing Platform created to oldest activity timestamp
UPDATE "platform" p
SET created = COALESCE((
    SELECT MIN(a.timestamp)
    FROM "activity" a
    WHERE a.platform_id = p.id
), now());

-- update existing Game created to oldest activity timestamp
UPDATE "game" g
SET created = COALESCE((
    SELECT MIN(a.timestamp)
    FROM "activity" a
    WHERE a.game_id = g.id
), now());

-- update existing User created to oldest activity timestamp
UPDATE "user" u
SET created = COALESCE((
    SELECT MIN(a.timestamp)
    FROM "activity" a
    WHERE a.user_id = u.id
), now());
