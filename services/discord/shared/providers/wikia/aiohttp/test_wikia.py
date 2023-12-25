from unittest import IsolatedAsyncioTestCase

from services.discord.shared.providers.wikia.aiohttp import wikia
from services.discord.shared.providers.wikia.converters.nova_drift import converter


class WikiaTest(IsolatedAsyncioTestCase):
    async def test_read_page_from_name(self):
        nova_drift_wikia = wikia.Wikia("nova-drift")

        result = await nova_drift_wikia.read_page_from_name("Antimatter_Rounds")

        page = await converter(result)

        print(page.data.dict())

    async def test_read_page_names_from_category_name(self):
        nova_drift_wikia = wikia.Wikia("nova-drift")

        result = await nova_drift_wikia.read_page_names_from_category_name("mods")

        print(result)
