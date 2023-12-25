from dataclasses import dataclass
from datetime import datetime
import uuid
import json

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


class PageID(uuid.UUID):
    pass


class PageRegister(Register):
    async def read_from_name(self, page_name: str, wikia_id: WikiaID) -> None | PageData:
        query = """
        select data
        from page
        where name ~* $1
          and wikia_id = $2
        """

        async with self.pool.acquire() as conn:
            records = await conn.fetch(query, page_name, wikia_id)
        records = type_convert_to_record(records)

        if len(records) != 1:
            return None

        return PageData(**json.loads(records[0]["data"]))

