create table token (
    id serial primary key,
    created timestamp not null,
    expires timestamp not null,
    user_id integer references "user"(id) on delete cascade not null,
    sha256 text not null unique
);

