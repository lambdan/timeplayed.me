-- remove steam id
ALTER TABLE game DROP COLUMN steam_id;

-- remove history columns, and add history table 

ALTER TABLE game DROP COLUMN history;
ALTER TABLE activity DROP COLUMN history;
ALTER TABLE "user" DROP COLUMN history;
ALTER TABLE platform DROP COLUMN history;


create table history (
    id serial primary key,
    timestamp timestamp with time zone default now(),
    game_id integer references game(id) on delete cascade,
    user_id integer references "user"(id) on delete cascade,
    platform_id integer references platform(id) on delete cascade,
    activity_id integer references activity(id) on delete cascade,
    message text
);

