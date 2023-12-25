import asyncio
from functools import wraps

from aiohttp import web

from DiscordInterpythons.handlers import handlers
from DiscordInterpythons.models.interaction import Interaction, InteractionType, InteractionResponse, InteractionResponseType
from DiscordInterpythons.providers.webhook import UpdateWebhookMessageReq, InteractionResponseAPI


def verify(func, discord_public_key: str):
    async def _wrapper(request: web.Request) -> web.Response:
        signature = request.headers.get("X-Signature-Ed25519")
        timestamp = request.headers.get("X-Signature-Timestamp")

        if signature is None \
                or timestamp is None \
                or not handlers.verify_key(await request.read(), signature, timestamp, discord_public_key):
            raise web.HTTPUnauthorized(reason="Bad request signature")
        return await func(request)

    return _wrapper


def handle(func):
    async def _wrapper(request: web.Request) -> web.Response:
        data = await request.json()
        print(data)

        return web.json_response(await handlers.handle_interaction(data))
    return _wrapper


def respond(func, is_prod: bool, discord_public_key: str):
    async def _wrapper(request: web.Request) -> web.Response:
        data = await request.json()

        interaction = Interaction(**data)

        try:
            response = await func(interaction)
        except Exception as e:
            response = interaction.response.reply(f"Encountered an Unexpected Error: {e}")

            await InteractionResponseAPI(
                token=interaction.token,
            ).update(
                interaction.application_id,
                message=UpdateWebhookMessageReq(
                    content=response.data.content,
                    embeds=response.data.embeds,
                    allowed_mentions=response.data.allowed_mentions,
                    components=response.data.components,
                    attachments=response.data.attachments,
                ),
            )

            return web.HTTPAccepted()

        if response.data is None:
            return web.HTTPOk()

        await InteractionResponseAPI(
            token=interaction.token,
        ).update(
            interaction.application_id,
            message=UpdateWebhookMessageReq(
                content=response.data.content,
                embeds=response.data.embeds,
                allowed_mentions=response.data.allowed_mentions,
                components=response.data.components,
                attachments=response.data.attachments,
            ),
        )

        return web.HTTPOk()
    if not is_prod:
        return verify(handle(_wrapper), discord_public_key)
    return _wrapper


def enforce_guild_only(coro):
    @wraps(coro)
    async def _wrapper(self, interaction: Interaction, *args, **kwargs):
        if interaction.guild_id is None:
            return interaction.response.reply("Command is Guild Only")

        return await coro(self, interaction, *args, **kwargs)
    return _wrapper


def _enforce_me(interation: Interaction) -> bool:
    return ((interation.user is not None and interation.user.id == "182668063882215424")
            or (interation.member is not None and interation.member.user.id == "182668063882215424"))


def enforce_me(coro):
    @wraps(coro)
    async def _wrapper(self, interaction: Interaction, *args, **kwargs):
        if _enforce_me(interaction):
            return await coro(self, interaction, *args, **kwargs)

        return interaction.response.reply("Insufficient Permissions, must be Owner")
    return _wrapper


def enforce_administrator(coro):
    @wraps(coro)
    async def _wrapper(self, interaction: Interaction, *args, **kwargs):
        if _enforce_me(interaction) or interaction.member.permissions.administrator:
            return await coro(self, interaction, *args, **kwargs)

        return interaction.response.reply("Insufficient Permissions, must be Administrator")

    return _wrapper
