from datetime import datetime
import uuid

from shared.asyncpg.register import Register
from shared.asyncpg.type_coerce import type_convert_to_record


class WikiaID(uuid.UUID):
    pass


class WikiaRegister(Register):
    async def read_from_name(self, name: str) -> None | WikiaID:
        query = """
        select id
        from wikia
        where name = $1
        """

        async with self.pool.acquire() as conn:
            records = await conn.fetch(query, name)
        records = type_convert_to_record(records)

        if len(records) != 1:
            return None

        return records[0]["id"]
