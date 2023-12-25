from __future__ import annotations

from dataclasses import dataclass

import asyncio
import aiohttp

from shared.pydantic import BaseModel


class Page(BaseModel):
    wikia: str
    title: str
    id: int
    text: str
    url: str


class RawPageParse(BaseModel):
    pageid: int
    title: str
    text: str


class RawPage(BaseModel):
    parse: RawPageParse

    def as_page(self, url: str, wikia: str) -> Page:
        return Page(
            wikia=wikia,
            title=self.parse.title,
            id=self.parse.pageid,
            text=self.parse.text,
            url=url,
        )


class Category(BaseModel):
    id: int
    title: str
    url: str
    ns: str


class RawCategory(BaseModel):
    items: list[Category]


@dataclass
class Wikia:
    _BASE_URL = "https://{wikia}.fandom.com"
    wikia_name: str

    @property
    def api_url(self) -> str:
        return f"{self._BASE_URL.format(wikia=self.wikia_name)}/api"

    async def read_page_from_name(
            self,
            page_name: str,
    ) -> Page:
        url = f"{self.api_url}.php?action=parse&format=json&page={page_name}&prop=text&formatversion=2"

        async with aiohttp.ClientSession(raise_for_status=True) as session:
            async with session.get(url) as resp:
                data = await resp.json()

        return RawPage(**data).as_page(
            url=f"{self._BASE_URL.format(wikia=self.wikia_name)}/wiki/{page_name.replace(' ', '_')}",
            wikia=self.wikia_name,
        )

    async def read_pages_from_category_name(
            self,
            category_name: str,
    ) -> tuple[Page, ...]:
        page_names = await self.read_page_names_from_category_name(category_name)

        results = []
        for page_name in page_names:
            results.append(await self.read_page_from_name(page_name=page_name))
            await asyncio.sleep(0.5)

        return tuple(results)

    async def read_page_names_from_category_name(
            self,
            category_name: str,
    ) -> tuple[str, ...]:
        url = f"{self.api_url}/api/v1/Articles/List?category={category_name}&from=R&limit=1000"

        async with aiohttp.ClientSession(raise_for_status=True) as session:
            async with session.get(url) as resp:
                data = await resp.json()

        return tuple(i.title for i in RawCategory(**data).items)
