from dataclasses import dataclass
from datetime import datetime
import uuid
from pydantic import Json


from shared.asyncpg.register import Register
from shared.asyncpg.type_coerce import type_convert_to_record
from shared.pydantic import BaseModel

from .wikia import WikiaID


class PageField(BaseModel):
    name: str
    value: str


class PageData(BaseModel):
    title: str
    thumbnail: dict
    color: int
    description: str
    fields: list[PageField]

    def get_thumbnail_url(self) -> None | str:
        return self.thumbnail.get("url")


class Page(BaseModel):
    name: str
    data: Json[PageData] | PageData
    url: str


class PageID(uuid.UUID):
    pass


class PageRegister(Register):
    async def read_from_url(self, url: str, wikia_id: WikiaID) -> None | PageID:
        query = """
        select id
        from page
        where url = $1
          and wikia_id = $2
        """

        async with self.pool.acquire() as conn:
            records = await conn.fetch(query, url, wikia_id)
        records = type_convert_to_record(records)

        if len(records) != 1:
            return None

        return records[0]["id"]

    async def create_or_update(self, page: Page, wikia_id: WikiaID) -> PageID:
        page_id = await self.read_from_url(page.url, wikia_id)

        if page_id is not None:
            return await self.update(page, page_id)

        return await self.create(page, wikia_id)

    async def create(self, page: Page, wikia_id: WikiaID) -> PageID:
        query = """
        insert into page(name, wikia_id, data, url)
        values($1::text, $2::uuid, $3::jsonb, $4::text)
        returning id
        """

        async with self.pool.acquire() as conn:
            records = await conn.fetch(query, page.name, wikia_id, page.data.json(), page.url)
        records = type_convert_to_record(records)

        return records[0]["id"]

    async def update(self, page: Page, page_id: PageID) -> PageID:
        query = """
        update page 
        set data = $1
        where id = $2
        """

        async with self.pool.acquire() as conn:
            records = await conn.fetch(query, page.data.json(), page_id)
        records = type_convert_to_record(records)

        return page_id