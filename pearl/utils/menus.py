'''
MIT License

Copyright (c) 2020 Caio Alexandre

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

import textwrap
import typing

import discord
from discord.ext import commands, menus

from .constants import checkmark_emoji, wrongmark_emoji


class InvalidData(Exception):
    def __init__(self):
        super().__init__('Invalid data type')


class _BaseMenu(menus.MenuPages):
    async def update(self, payload: discord.RawReactionActionEvent):
        if self._can_remove_reactions:
            if payload.event_type == 'REACTION_REMOVE':
                return

            await self.message.remove_reaction(payload.emoji, payload.member)
        await super().update(payload)


class Menu(_BaseMenu):
    def __init__(self, data: typing.Union[str, typing.List[str]], **kwargs):
        if isinstance(data, list):
            Paginator = ListPaginator
        elif isinstance(data, str):
            Paginator = TextPaginator
        else:
            raise InvalidData()
        
        paginator = Paginator(data, **kwargs)
        super().__init__(paginator, clear_reactions_after=True, check_embeds=True)


class TextPaginator(menus.ListPageSource):
    def __init__(self, text: str, **kwargs):
        wrapped = textwrap.wrap(text, width=2012)
        data = [f'{item}...' if item != wrapped[-1] else item for item in wrapped] or ['[empty string]']

        self.codeblock = kwargs.pop('codeblock', False)
        self.kwargs = kwargs
        super().__init__(data, per_page=1)

    async def format_page(self, menu: menus.Menu, entry: str):
        if self.codeblock:
            entry = f'```py\n{entry}```'

        embed = menu.ctx.get_embed(entry, **self.kwargs)
        embed.set_footer(text=f'Página {menu.current_page + 1}/{self.get_max_pages()}')
        return embed


class ListPaginator(menus.ListPageSource):
    def __init__(self, data: typing.List[str], **kwargs):
        per_page = kwargs.pop('per_page', 1)
        self.kwargs = kwargs
        super().__init__(data, per_page=per_page)

    async def format_page(self, menu: menus.Menu, entry: typing.Union[str, typing.List[str]]):
        if isinstance(entry, list):
            entry = '\n'.join(entry)

        embed = menu.ctx.get_embed(entry, **self.kwargs)
        embed.set_footer(text=f'Página {menu.current_page + 1}/{self.get_max_pages()}')
        return embed


class Confirm(menus.Menu):
    def __init__(self, content: str):
        super().__init__(delete_message_after=True, check_embeds=True)
        self.result = None
        self.content = content

    @menus.button(checkmark_emoji)
    async def on_confirm(self, payload: discord.RawReactionActionEvent):
        self.result = True
        self.stop()

    @menus.button(wrongmark_emoji)
    async def on_deny(self, payload: discord.RawReactionActionEvent):
        self.result = False
        self.stop()

    async def send_initial_message(self, ctx: commands.Context, _) -> discord.Message:
        return await ctx.send(self.content)

    async def prompt(self, ctx: commands.Context) -> typing.Optional[bool]:
        await self.start(ctx, wait=True)
        if self.result is None:
            await ctx.send('Tempo esgotado.')

        return self.result