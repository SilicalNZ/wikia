from os import environ
from typing import Any, Callable, Coroutine
from ssl import create_default_context

from aiohttp import web
import asyncpg
from DiscordInterpythons.handlers.handler import (
    ChatInputHandler, InteractionHandlerClass
)
from DiscordInterpythons.models.interaction import Interaction
from DiscordInterpythons.models.embed import Embed

from services.discord.controllers.commands.show.providers import asyncpg as register
from services.discord.shared.providers.config.yaml import load
from services.discord.shared.providers.discord import respond, enforce_administrator, enforce_guild_only


_type_callable_web_request_website = Callable[
    [web.Request, Any],
    Coroutine[Any, Any, web.Response],
]


VERSION = 1

IS_PROD = environ.get("is_prod", False)

config = load(IS_PROD)

wikia_database = register.WikiaRegister(None)
page_database = register.PageRegister(None)


class CommandHandler(InteractionHandlerClass):
    @ChatInputHandler(name="show")
    async def action(self, interaction: Interaction, page_name: str):
        """Show Page From a Wikia

        :param page_name: Name of the page being selected
        """

        wikia_id = await wikia_database.read_from_name("nova-drift")

        result = await page_database.read_from_name(page_name, wikia_id)

        if result is None:
            return interaction.response.reply("Page not found")

        return interaction.response.complex_reply(
            embeds=Embed(**result.dict()),
        )

async def connect_db(_: web.Application):
    pool = await asyncpg.create_pool(
        dsn=config.database.dsn,
        ssl=create_default_context(cadata=config.database.ssl_cert),
        server_settings={"application_name": "wikia-discord-commands-show"},
    )

    wikia_database.pool = pool
    page_database.pool = pool


app = web.Application()

app.on_startup.append(connect_db)

app.router.add_post(f"/discord/interactions/commands/show", respond(
    CommandHandler().action._call,
    IS_PROD,
    config.discord.public_key,
))
