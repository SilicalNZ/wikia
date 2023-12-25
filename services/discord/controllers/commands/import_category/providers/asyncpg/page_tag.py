from dataclasses import dataclass
from datetime import datetime
import uuid

from shared.asyncpg.register import Register
from shared.asyncpg.type_coerce import type_convert_to_record

from .page import PageID


@dataclass
class PageTag:
    page_id: PageID
    tag: str


class PageTagRegister(Register):
    async def create(self, page_tag: PageTag):
        query = """
        insert into page_tag(page_id, tag)
        values($1, $2)
        """

        async with self.pool.acquire() as conn:
            await conn.fetch(query, page_tag.page_id, page_tag.tag)

    async def read_or_create(self, page_tag: PageTag):
        query = """
            select exists(select 1 from page_tag where page_id = $1 and tag = $2)
        """
        async with self.pool.acquire() as conn:
            records = await conn.fetch(query, page_tag.page_id, page_tag.tag)
        records = type_convert_to_record(records)

        if records[0]["exists"]:
            return

        return await self.create(page_tag)