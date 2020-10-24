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

import random

import asyncpg
import discord
from discord.ext import commands


class Waifu:
    def __init__(self, record: asyncpg.Record):
        self.name = record['name']
        self.anime = record['anime']

        file_name = self.name.lower().replace(' ', '_')
        format_ = record['format']
        self.file = f'{file_name}.{format_}'
        self.icon = discord.File(fp=f'assets/waifus/{self.file}')
        self.how_many_have = record['how_many_have']
        self.gender = record['gender']

    def __repr__(self):
        return f'<Waifu name={self.name!r} anime={self.anime!r}>'


class Waifus(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(aliases=['waifus'], invoke_without_command=True)
    async def waifu(self, ctx: commands.Context):
        pass

    @waifu.command(name='roll')
    async def waifu_roll(self, ctx: commands.Context):
        query = 'SELECT * FROM waifus'
        fetch = await ctx.pool.fetch(query)

        waifu = Waifu(random.choice(fetch))

        how_many = f'{waifu.how_many_have} pessoa' + ('' if waifu.how_many_have == 1 else 's')
        gender = 'esta waifu' if waifu.gender == b'f' else 'este husbando'

        description = f'Anime: **{waifu.anime}**\n{how_many} possuem {gender}'

        await ctx.send(
            title=waifu.name,
            content=description,
            file=waifu.icon,
            image=f'attachment://{waifu.file}'
        )

def setup(bot: commands.Bot) -> None:
    bot.add_cog(Waifus(bot))