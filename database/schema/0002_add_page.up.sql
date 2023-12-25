create table page
(
    id       uuid    not null default uuid_generate_v4() primary key, --immutable

    wikia_id uuid    not null references wikia,                       --immutable
    name     text    not null,
    data     json    not null,
    url      text    not null unique,

    unique (wikia_id, name)
);
