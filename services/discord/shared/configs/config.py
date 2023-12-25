from __future__ import annotations

from shared.pydantic import BaseModel



class Database(BaseModel):
    dsn: str
    ssl_cert: str


class Discord(BaseModel):
    application_id: int
    debug_guild_id: int | None
    public_key: str
    token: str


class Config(BaseModel):
    database: Database
    discord: Discord
