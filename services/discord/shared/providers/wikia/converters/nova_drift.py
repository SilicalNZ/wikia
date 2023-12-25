from services.discord.shared.providers.wikia.aiohttp.wikia import Page
from . import convert_strategy


def handler_find_patch(content: convert_strategy.Handler, page: convert_strategy.ConvertedPage):
    if "Last Update" not in content.n[0][0]:
        content.n = content.n[2:]
        return

    patch = content.n[0][1]
    content.n = content.n[3:]


def handler_find_stat_fields(content: convert_strategy.Handler, page: convert_strategy.ConvertedPage):
    if "GEAR TYPE" not in content.n[0][0]:
        return

    value = content.n[1]
    for x in range(len(value)):
        value[x] = f"• {value[x]}"
    value = "\n".join(value)
    value = value.replace(":\n•", ": ")

    page.data.fields = (
        *page.data.fields,
        store_model.PageField(
            name="**Stats**",
            value=value,
        ),
    )

    content.n = content.n[2:]


async def converter(page: Page) -> convert_strategy.ConvertedPage:
    return await convert_strategy.behaviour(
        (
            # convert_strategy.handler_trim,
            convert_strategy.handler_find_image,
            convert_strategy.handler_find_colour,
            convert_strategy.handler_trim_empty_tags,
            handler_find_stat_fields,
            handler_find_patch,
            convert_strategy.handler_trim_before_content,
            convert_strategy.handler_merge_td_into_li,
            convert_strategy.handler_join_li_semicolons,
            convert_strategy.handler_collapse_ext,
            convert_strategy.handler_find_fields,
        ),
        page,
    )
