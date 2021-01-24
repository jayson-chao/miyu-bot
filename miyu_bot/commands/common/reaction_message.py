import asyncio
from typing import List, Callable, Awaitable, Union

import discord
from discord import Message, Embed, Emoji
from discord.ext.commands import Context

AnyEmoji = Union[str, Emoji]


async def run_tabbed_message(ctx: Context, emojis: List[AnyEmoji], embeds: List[Embed], files=None, starting_index=0,
                             timeout=300):
    if len(emojis) != len(embeds):
        raise ValueError('Emojis and embeds must have the same number of elements.')

    message = await ctx.send(files=files, embed=embeds[starting_index])

    async def callback(emoji):
        await message.edit(embed=embeds[emojis.index(emoji)])

    await run_reaction_message(ctx, message, emojis, callback, timeout)


async def run_dynamically_paged_message(ctx: Context, embed_generator: Callable[[int], discord.Embed], timeout=300):
    left_arrow = '◀'
    right_arrow = '▶'
    arrows = [left_arrow, right_arrow]

    message = await ctx.send(embed=embed_generator(0))

    async def callback(emoji):
        if emoji == left_arrow:
            new_embed = embed_generator(-1)
        elif emoji == right_arrow:
            new_embed = embed_generator(1)
        else:
            return

        if new_embed:
            await message.edit(embed=new_embed)

    await run_reaction_message(ctx, message, arrows, callback, timeout)


async def run_paged_message(ctx: Context, base_embed: discord.Embed, content: List[str], page_size: int = 15,
                            header='', numbered: bool = True, timeout=300, max_tabbed_pages=4, files=None):
    if header:
        header = f'`{header}`\n'

    if max_tabbed_pages > 9:
        raise ValueError('max_tabbed_pages must be 9 or less.')

    if not content:
        embed = base_embed.copy().set_footer(text='Page 0/0')
        await ctx.send(embed=embed)
        return

    page_contents = [content[i:i + page_size] for i in range(0, len(content), page_size)]

    item_number = 0
    max_item_number_length = len(str(len(content)))

    def format_item(item):
        nonlocal item_number
        item_number += 1
        if numbered:
            return f'`{item_number}.{" " * (max_item_number_length - len(str(item_number)))} {item}`'
        else:
            return f'`{item}`'

    embeds = [
        base_embed.from_dict({
            **base_embed.to_dict(),
            'description': header + '\n'.join((format_item(i) for i in page)),
        }).set_footer(text=f'Page {i + 1}/{len(page_contents)}')
        for i, page in enumerate(page_contents)]

    if len(embeds) == 1:
        await ctx.send(embed=embeds[0])
        return

    if len(embeds) <= max_tabbed_pages:
        reaction_emoji = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣']
        await run_tabbed_message(ctx, reaction_emoji[:len(embeds)], embeds, timeout=timeout)
    else:
        message = await ctx.send(embed=embeds[0], files=files or [])

        double_left_arrow = '⏪'
        double_right_arrow = '⏩'
        left_arrow = '◀'
        right_arrow = '▶'

        arrows = [double_left_arrow, left_arrow, right_arrow, double_right_arrow]

        index = 0

        async def callback(emoji):
            nonlocal index
            start_index = index
            if emoji == double_left_arrow:
                index = 0
            elif emoji == left_arrow:
                index -= 1
            elif emoji == right_arrow:
                index += 1
            elif emoji == double_right_arrow:
                index = len(embeds) - 1
            index = min(len(embeds) - 1, max(0, index))

            if index != start_index:
                await message.edit(embed=embeds[index])

        await run_reaction_message(ctx, message, arrows, callback, timeout)


async def run_deletable_message(ctx: Context, message: Message, timeout=300):
    await run_reaction_message(ctx, message, [], _noop, timeout=timeout)


async def _noop(n):
    return None


async def run_reaction_message(ctx: Context, message: Message, emojis: List[AnyEmoji],
                               callback: Callable[[AnyEmoji], Awaitable[None]], timeout=300):
    emojis.append('❎')
    for emoji in emojis:
        await message.add_reaction(emoji)

    def check(rxn, usr):
        return usr == ctx.author and rxn.emoji in emojis and rxn.message.id == message.id

    while True:
        try:
            reaction, user = await ctx.bot.wait_for('reaction_add', timeout=timeout, check=check)
            if reaction.emoji == '❎':
                await message.delete()
                return
            await callback(reaction.emoji)
            await message.remove_reaction(reaction, user)
        except asyncio.TimeoutError:
            for emoji in emojis:
                await message.remove_reaction(emoji, ctx.bot.user)
            break
