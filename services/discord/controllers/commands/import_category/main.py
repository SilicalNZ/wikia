from os import environ
from typing import Any, Callable, Coroutine, AsyncIterable
from enum import Enum
from ssl import create_default_context
from datetime import datetime, timedelta

from aiohttp import web
import asyncio
from DiscordInterpythons.handlers.handler import (
    ChatInputHandler, InteractionHandlerClass
)
from DiscordInterpythons.models.interaction import Interaction, InteractionResponse
from DiscordInterpythons.providers.webhook import InteractionResponseAPI, UpdateWebhookMessageReq
import asyncpg

from services.discord.controllers.commands.import_category.providers import asyncpg as register
from services.discord.shared.providers.config.yaml import load
from services.discord.shared.providers.discord import respond, enforce_me
from services.discord.shared.providers.wikia.aiohttp import Wikia
from services.discord.shared.providers.wikia.converters.nova_drift import converter as novadrift_converter


_type_callable_web_request_website = Callable[
    [web.Request, Any],
    Coroutine[Any, Any, web.Response],
]


VERSION = 1

IS_PROD = environ.get("is_prod", False)

config = load(IS_PROD)


class WikiaName(str, Enum):
    NOVA_DRIFT = "nova-drift"

    UNKNOWN = "UNKNOWN"

    @classmethod
    def _missing_(cls, value: object):
        return cls(cls.UNKNOWN)


wikia_database = register.WikiaRegister(None)
page_database = register.PageRegister(None)
page_tag_database = register.PageTagRegister(None)
wikia_converters = {
    WikiaName.NOVA_DRIFT.value: novadrift_converter,
}


async def update_pages_from_category(wikia_name: WikiaName, category_name: str) -> AsyncIterable[tuple[str | None, str | None, float]]:
    wikia_id = await wikia_database.read_from_name(wikia_name)
    assert  wikia_id is not None

    wikia_api = Wikia(wikia_name)

    page_names = await wikia_api.read_page_names_from_category_name(category_name)

    total_pages = len(page_names)
    for x, page_name in enumerate(page_names):
        page = await wikia_api.read_page_from_name(page_name=page_name)

        try:
            new_page = await wikia_converters[wikia_name](page)
        except:
            yield None, page.title, x / total_pages
            continue

        new_page_id = await page_database.create_or_update(new_page, wikia_id)

        await page_tag_database.read_or_create(register.PageTag(
            page_id=new_page_id,
            tag=category_name,
        ))

        await asyncio.sleep(0.5)

        yield new_page.name, None, x / total_pages


class CommandHandler(InteractionHandlerClass):
    @ChatInputHandler(name="import_category")
    @enforce_me
    async def action(self, interaction: Interaction, wikia_name: WikiaName, category_name: str) -> InteractionResponse:
        """Import Pages From a Category From a Wikia

        :param wikia_name: Name of the wikia being selected
        :param category_name: Name of the category being selected
        """
        last_progress_call = datetime.now().replace(microsecond=0) - timedelta(minutes=1)

        succeeded_page_names, failed_page_names = [], []
        async for succeeded_page_name, failed_page_name, progress in update_pages_from_category(
            wikia_name.value,
            category_name,
        ):
            if succeeded_page_name:
                succeeded_page_names.append(succeeded_page_name)

            if failed_page_name:
                failed_page_names.append(failed_page_name)

            now = datetime.now().replace(microsecond=0)
            if now - last_progress_call < timedelta(minutes=1):
                continue

            last_progress_call = now

            response = interaction.response.reply((
                f"Progress {progress*100:.3f}%\n\n"
                f"Success: {', '.join(succeeded_page_names[-50:])}\n\n"
                f"Failed: {', '.join(failed_page_names[-25:])}"
            ))

            await InteractionResponseAPI(
                token=interaction.token,
            ).update(
                interaction.application_id,
                message=UpdateWebhookMessageReq(
                    content=response.data.content,
                    embeds=response.data.embeds,
                ),
            )

        response = interaction.response.reply((
            f"Success: {', '.join(succeeded_page_names[-50:])}\n\n"
            f"Failed: {', '.join(failed_page_names[-25:])}"
        ))

        await InteractionResponseAPI(
            token=interaction.token,
        ).update(
            interaction.application_id,
            message=UpdateWebhookMessageReq(
                content=response.data.content,
                embeds=response.data.embeds,
            ),
        )

        return interaction.response.reply("Done")

async def connect_db(_: web.Application):
    pool = await asyncpg.create_pool(
        dsn=config.database.dsn,
        ssl=create_default_context(cadata=config.database.ssl_cert),
        server_settings={"application_name": "wikia-discord-commands-import-category"},
    )

    wikia_database.pool = pool
    page_database.pool = pool
    page_tag_database.pool = pool


app = web.Application()

app.on_startup.append(connect_db)


app.router.add_post(f"/discord/interactions/commands/import/category", respond(
    CommandHandler().action._call,
    IS_PROD,
    config.discord.public_key,
))
