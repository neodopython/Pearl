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

import typing

import asyncpg
import discord
from discord.ext import commands

from .embed import Embed
from .menus import Confirm


class Context(commands.Context):
    @property
    def pool(self) -> asyncpg.pool.Pool:
        """Returns a PostgreSQL pool."""
        return self.bot.pool

    @property
    def color(self):
        """Returns a invisible embed color."""
        return 0x2f3136

    @property
    def constants(self):
        """Returns all constants module."""
        return self.bot.constants

    @property
    def loop(self):
        """Returns asyncio's loop."""
        return self.bot.loop

    @property
    def dagpi(self):
        """Returns Dagpi's client."""
        return self.bot.dagpi

    def get_embed(self, content: str = None, **kwargs) -> Embed:
        """Returns a ready-to-use embed with given content."""
        author = kwargs.pop('author', {
            'name': self.author.display_name,
            'icon_url': self.author.avatar_url
        })
        color = kwargs.pop('color', self.color)

        return Embed(description=content, author=author, color=color, **kwargs)
    
    async def send(self, content: str = None, **kwargs) -> discord.Message:
        """This method was overrided to send a rendered cool embed."""
        delete_after = kwargs.pop('delete_after', None)
        file = kwargs.pop('file', None)

        embed = self.get_embed(content=content, **kwargs)
        return await super().send(embed=embed, delete_after=delete_after, file=file)

    async def prompt(self, content: str) -> typing.Optional[bool]:
        confirm = Confirm(content)
        return await confirm.prompt(self)