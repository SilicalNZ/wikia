from dataclasses import dataclass, field
import asyncio
import io
from typing import Callable, Coroutine, Any
from pydantic import Json

from PIL import Image, ImageStat
import aiohttp

from services.discord.shared.providers.wikia.converters.parser import (
    Handler,
    Url,
    Dl,
    Td,
    Li,
    H2,
    Extra,
)
from services.discord.shared.providers.wikia.aiohttp.wikia import Page
from shared.pydantic import BaseModel
from services.discord.shared.providers.wikia.converters.parser import PreciseHTMLParser



class PageField(BaseModel):
    name: str
    value: str


class PageData(BaseModel):
    title: str
    thumbnail: dict
    color: int
    description: str
    fields: list[PageField]

    def get_thumbnail_url(self) -> None | str:
        return self.thumbnail.get("url")


class ConvertedPage(BaseModel):
    name: str
    data: Json[PageData] | PageData
    url: str


def handler_trim(content: Handler, page: ConvertedPage):
    # Trim
    content.n = content.n[9:]


def handler_trim_empty_tags(content: Handler, page: ConvertedPage):
    content.filter(lambda x: x and not isinstance(x, Dl))


def handler_trim_before_content(content: Handler, page: ConvertedPage):
    for x, i in enumerate(content.n):
        if isinstance(i, H2) and i[0] == "Contents":
            content.n.pop(x)
            content.n.pop(x)
            content.n.pop(x-1)
            break


def handler_merge_td_into_li(content: Handler, page: ConvertedPage):
    list_objects = []
    for i in content.n:
        if isinstance(i, (Td, Li)):
            list_objects.append(i)
        elif len(list_objects) == 1:
            list_objects = []
        elif list_objects:
            new_li = list_objects[0]
            for i in list_objects[1:]:
                content.n.remove(i)
                for j in i:
                    new_li.append(j)
            list_objects = []


def handler_join_li_semicolons(content: Handler, page: ConvertedPage):
    for x, i in enumerate(content.n):
        if isinstance(i, Li):
            new_li = Li()
            for y, val in enumerate(i):
                if len(val) > 3 and val[0] == "[" and val[2] == "]":
                    val = val[3:]

                if new_li and (new_li[-1].endswith(":")):
                    new_li[-1] += f" {val}"
                elif new_li and (val.startswith("'")):
                    new_li[-1] += val
                elif new_li and (val.startswith("[") and val.endswith("]")):
                    continue
                elif new_li and val.startswith("."):
                    new_li[-1] += val
                else:
                    new_li.append(val)
            content.n[x] = new_li


def handler_collapse_ext(content: Handler, page: ConvertedPage):
    drop = []
    for x, i in enumerate(content.n):
        if x and isinstance(i, Extra):
            content.n[x-1][-1]+= i[0]
            drop.append(x)
        elif not x and isinstance(i, Extra):
            content.n[0] = H2(("Stats", ))

    for x, i in enumerate(drop):
        content.n.pop(i-x)


def handler_find_image(content: Handler, page: ConvertedPage):
    # Find the image we want
    name = page.name.replace(':', '')

    options = (
        name.replace(' ', '_').lower(),
        name.replace('_', '').lower(),
    )

    url = None

    for x in content:
        if not isinstance(x, Url):
            continue

        if any(option in x[0].lower() for option in options):
            url = x[0]
            break

    # Strip wikia formatting
    url = url[:url.index('latest') + len('latest')]
    page.data.thumbnail = {"url": url}

    # Trim
    content.filter(lambda x: not isinstance(x, Url))


async def handler_find_colour(content: Handler, page: ConvertedPage):
    assert page.data.get_thumbnail_url()

    result = await _get_avg_colour(page.data.get_thumbnail_url())

    page.data.color = _rgb2int(result)


def handler_find_fields(content: Handler, page: ConvertedPage):
    for name, values in zip(content.n[0::2], content.n[1::2]):
        if name[0] == "Gallery":
            break

        result_str = ""
        name = f"**{name[0]}**"

        for x in range(len(values)):
            if len(values[x]) > 500:
                values[x] = f"{values[x]}..."

            append_str = f"• {values[x]}\n"

            if len(result_str) + len(append_str) > 800:
                page.data.fields = (
                    *page.data.fields,
                    PageField(
                        name=name,
                        value=result_str,
                    ),
                )

                result_str = ""

            result_str += append_str

        page.data.fields = (
            *page.data.fields,
            PageField(
                name=name,
                value=result_str,
            ),
        )


async def behaviour(
        funcs: tuple[
            Callable[
                [Handler, Page],
                Coroutine[Any, Any, None]
            ] | Callable[
                [Handler, Page],
                None
            ], ...],
        page: Page,
) -> Page:
    text = page.text

    text = text[:text.index('<!--')]

    text = text.rstrip()
    text = text.replace('\\t', '').replace('\\n', '')

    handler = PreciseHTMLParser().feed(text)

    store_page = ConvertedPage(
        name=page.title,
        data=PageData(
            title=f"**{page.title.upper().replace('_', ' ')}**",
            thumbnail="",
            color=0,
            description=f"[Wikia Page]({page.url})",
            fields=[],
        ),
        url=page.url,
    )

    for func in funcs:
        if asyncio.iscoroutinefunction(func):
            await func(handler, store_page)
        else:
            func(handler, store_page)

    return store_page


async def _get_avg_colour(url: str) -> tuple[int, int, int]:
    """Requests image from url and returns it as BytesIO"""
    async with aiohttp.ClientSession(raise_for_status=True) as session:
        async with session.get(url) as resp:
            byte_io = io.BytesIO(await resp.read())

    im = Image.open(byte_io).convert("RGB")

    mult = 0.25
    im = im.crop((
        int(im.width * mult),
        int(im.height * mult),
        int(im.height * (1 - mult)),
        int(im.width * (1 - mult)),
    ))

    return ImageStat.Stat(im)._getmedian()


def _rgb2hex(rgb: tuple[int, int, int]):
    return "0x{:02x}{:02x}{:02x}".format(*rgb)


def _rgb2int(rgb: tuple[int, int, int]):
    return int(_rgb2hex(rgb), 16)
