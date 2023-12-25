from os import environ
from typing import Any, Callable, Coroutine

from aiohttp import web
from DiscordInterpythons.handlers.handler import (
    ChatInputHandler, InteractionHandlerClass
)
from DiscordInterpythons.models.interaction import Interaction, InteractionResponse

from services.discord.shared.providers.config.yaml import load
from services.discord.shared.providers.discord import respond


_type_callable_web_request_website = Callable[
    [web.Request, Any],
    Coroutine[Any, Any, web.Response],
]


VERSION = 1

IS_PROD = environ.get("is_prod", False)

config = load(IS_PROD)


class CommandHandler(InteractionHandlerClass):
    @ChatInputHandler(name="ping")
    async def action(self, interaction: Interaction) -> InteractionResponse:
        """Ping the application"""

        return interaction.response.reply(
            content="pong",
        )


app = web.Application()

app.router.add_post(f"/discord/interactions/commands/ping", respond(
    CommandHandler().action._call,
    IS_PROD,
    config.discord.public_key,
))
