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

from typing import Mapping, Optional, List

import discord
from discord.ext import commands

from utils.menus import HelpMenu, BotHelpInterface, GroupHelpInterface


class HelpCommand(commands.HelpCommand):
    def get_destination(self) -> commands.Context:
        return self.context

    def command_not_found(self, string: str) -> str:
        return f'Não há nenhum comando com o nome `{string}`.'

    def subcommand_not_found(self, command: commands.Group, string: str) -> str:
        if isinstance(command, commands.Group) and len(command.all_commands):
            return f'O comando `{command.name}` não possui o subcomando `{string}`.'
        return f'O comando `{command.name}` não possui subcomandos.'

    async def send_bot_help(self, mapping):
        ctx = self.context
        entries = await self.filter_commands(ctx.bot.commands, sort=True)

        all_commands = {}
        for command in entries:
            if not command.cog:
                continue

            try:
                all_commands[command.cog].append(command)
            except KeyError:
                all_commands[command.cog] = [command]

        menu = HelpMenu(BotHelpInterface(all_commands))
        await menu.start(ctx)

    async def send_cog_help(self, cog: commands.Cog):
        entries = await self.filter_commands(cog.get_commands(), sort=True)

        menu = HelpMenu(GroupHelpInterface(cog, entries))
        await menu.start(self.context)

    async def send_group_help(self, group: commands.Group):
        commands = group.commands
        if not len(commands):
            return await self.send_command_help(group)

        entries = await self.filter_commands(group.commands, sort=True)
        if not len(entries):
            return await self.send_command_help(group)

        interface = GroupHelpInterface(group, entries)
        interface.title = self.get_command_signature(group)

        menu = HelpMenu(interface)
        await menu.start(self.context)

    async def send_command_help(self, command: commands.Command):
        ctx = self.context

        title = self.get_command_signature(command)
        content = command.short_doc or 'Nenhuma ajuda encontrada.'

        await ctx.send(content, title=title)


class Help(commands.Cog, name='Ajuda'):
    """Comandos de ajuda, obviamente."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self._original_help = bot.help_command
        bot.help_command = HelpCommand()
        bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self._original_help


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Help(bot))