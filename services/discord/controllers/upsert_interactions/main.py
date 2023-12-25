import asyncio

from DiscordInterpythons.handlers.handler import InteractionHandlerClass
from DiscordInterpythons.providers.application_command import ApplicationCommandAPI
from DiscordInterpythons.models.snowflake import GuildID, ApplicationID

from services.discord.shared.providers.config.yaml import load as config_load

from services.discord.controllers.commands.ping import main as _
from services.discord.controllers.commands.import_category import main as _
from services.discord.controllers.commands.show import main as _



config = config_load(True)


application_commands = InteractionHandlerClass.generate_application_commands()


discord_application_command_api = ApplicationCommandAPI.from_interaction_handler_class(
    token=config.discord.token,
    application_id=ApplicationID(config.discord.application_id),
    debug_guild_id=GuildID(config.discord.debug_guild_id) if config.discord.debug_guild_id else None,
)


asyncio.run(discord_application_command_api.initialize())
