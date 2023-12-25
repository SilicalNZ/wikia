import yaml
from sys import path

from services.discord.shared.configs.config import Config


DEVELOPMENT = "development"
PRODUCTION = "production"


def load(is_prod: bool) -> Config:
    environment = PRODUCTION if is_prod else DEVELOPMENT

    with open(f"{path[1]}/services/discord/shared/configs/{environment}/config.yaml", "r") as fp:
        data = yaml.load(fp, Loader=yaml.SafeLoader)

    with open(f"{path[1]}/services/discord/shared/configs/{environment}/database_ssl_cert", "r") as fp:
        if data.get("database") is None:
            data["database"] = {}

        data["database"]["ssl_cert"] = fp.read()

    config = Config(**data)

    return config
