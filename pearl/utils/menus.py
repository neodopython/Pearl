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

import discord
from discord.ext import menus


class _BaseMenu(menus.MenuPages):
    async def update(self, payload: discord.RawReactionActionEvent):
        if self._can_remove_reactions:
            if payload.event_type == 'REACTION_REMOVE':
                return

            await self.message.remove_reaction(payload.emoji, payload.member)
        await super().update(payload)


class Menu(_BaseMenu):
    def __init__(self, data: str, **kwargs):
        paginator = TextPaginator(data, **kwargs)
        super().__init__(paginator, delete_message_after=True, check_embeds=True)


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