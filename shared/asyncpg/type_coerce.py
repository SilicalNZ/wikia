import asyncpg

from typing import Tuple, List, cast


def type_convert_to_record(records: list) -> Tuple[asyncpg.Record, ...]:
    return tuple(i for i in cast(List[asyncpg.Record], records))
