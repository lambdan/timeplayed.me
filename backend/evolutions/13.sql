create table token (
    id varchar(36) not null primary key,
    created timestamp not null,
    expires timestamp not null,
    user_id integer references "user"(id) on delete cascade
  );

