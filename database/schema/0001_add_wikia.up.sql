create table wikia
(
    id   uuid not null default uuid_generate_v4() primary key, --immutable

    name text not null unique,
    url  text not null unique
);
