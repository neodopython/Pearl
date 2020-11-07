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
'''
The MIT License (MIT)

Copyright (c) 2015 Rapptz

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
'''

import textwrap
from typing import Union, List, Optional, Dict

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
    def __init__(self, data: Union[str, List[str]], **kwargs):
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
        data = [f'{item} ...' if item != wrapped[-1] else item for item in wrapped] or ['[empty string]']

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
    def __init__(self, data: List[str], **kwargs):
        per_page = kwargs.pop('per_page', 1)
        self.kwargs = kwargs
        super().__init__(data, per_page=per_page)

    async def format_page(self, menu: menus.Menu, entry: Union[str, List[str]]):
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

    async def prompt(self, ctx: commands.Context) -> Optional[bool]:
        await self.start(ctx, wait=True)
        if self.result is None:
            await ctx.send('Tempo esgotado.')

        return self.result


# help menu
class BotHelpInterface(menus.ListPageSource):
    def __init__(self, commands: Dict[commands.Cog, List[commands.Command]]):
        cogs = sorted(commands.keys(), key=lambda c: c.qualified_name)
        self.commands = commands
        super().__init__(cogs, per_page=4)

        total_commands = 0
        for commands in commands.values():
            total_commands += len(commands)

        self.total_commands = total_commands

    async def format_page(self, menu: menus.Menu, cogs: List[commands.Cog]):
        ctx = menu.ctx
        prefix = ctx.prefix

        content = f'Digite `{prefix}help <comando>` para saber mais sobre um comando.\n' \
                  f'Digite `{prefix}help <categoria>` para saber mais sobre uma categoria.'

        fields = []

        for cog in cogs:
            if cog.description:
                short_doc = cog.description.split('\n', 1)[0]
            else:
                short_doc = 'Nenhuma ajuda encontrada.'

            commands = ' '.join([f'`{c.name}`' for c in self.commands[cog]])
            value = f'{short_doc}\n{commands}'

            fields.append({'name': cog.qualified_name, 'value': value, 'inline': False})

        embed = ctx.get_embed(content, title='Categorias', fields=fields)

        commands = f'{self.total_commands} comandos'
        embed.set_footer(text=f'Página {menu.current_page + 1}/{self.get_max_pages()} ({commands})')
        return embed


class GroupHelpInterface(menus.ListPageSource):
    def __init__(self, group, commands):
        super().__init__(commands, per_page=6)
        self.group = group
        self.commands = commands
        self.title = f'Comandos - {self.group.qualified_name}'
        self.content = self.group.description or self.group.short_doc or 'Nenhuma ajuda encontrada.'

    async def format_page(self, menu: menus.Menu, commands: List[commands.Command]):
        fields = []
        for command in commands:
            signature = f'{menu.ctx.prefix}{command.qualified_name} {command.signature}'
            value = command.short_doc or 'Nenhuma ajuda encontrada.'
            fields.append({'name': signature, 'value': value, 'inline': False})

        embed = menu.ctx.get_embed(self.content, title=self.title, fields=fields)

        total_commands = f'{len(self.commands)} comando' + ('s' if len(commands) != 1 else '')
        embed.set_footer(text=f'Página {menu.current_page + 1}/{self.get_max_pages()} ({total_commands})')
        return embed


class HelpMenu(_BaseMenu):
    def __init__(self, interface: menus.ListPageSource):
        super().__init__(interface, clear_reactions_after=True)