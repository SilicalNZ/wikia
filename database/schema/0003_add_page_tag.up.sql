create table page_tag
(
    id      uuid    not null default uuid_generate_v4() primary key, --immutable

    tag     text    not null,                                        --immutable

    page_id uuid not null references page,                        --immutable

    unique (page_id, tag)
);
