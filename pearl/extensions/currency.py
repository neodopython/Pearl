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

import discord
from discord.ext import commands


class Currency(commands.Cog, name='Monetário'):
    """Comandos relacionados ao sistema monetário."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def insert_into(self, ctx: commands.Context, *, member: discord.Member = None) -> None:
        member = member or ctx.author

        query = 'INSERT INTO currency (user_id) VALUES ($1) ON CONFLICT (user_id) DO NOTHING'
        await ctx.pool.execute(query, member.id)

    @commands.command()
    async def bank(self, ctx: commands.Context, *, member: discord.Member = None):
        member = member or ctx.author
        await self.insert_into(ctx, member=member)

        query = 'SELECT pearkies FROM currency WHERE user_id = $1'
        fetch = await ctx.pool.fetchrow(query, member.id)

        pearkies = fetch['pearkies']
        word = 'Você' if member == ctx.author else member.mention

        await ctx.send(f'{word} possui {pearkies} {ctx.constants.pearkies_emoji}.')

    @commands.command()
    @commands.cooldown(1, 86400, commands.BucketType.member)
    async def daily(self, ctx: commands.Context, *, member: discord.Member = None):
        member = member or ctx.author
        await self.insert_into(ctx, member=member)

        pearkies = random.randint(20, 50)
        word = 'Você' if member == ctx.author else member.mention

        query = 'UPDATE currency SET pearkies = pearkies + $2 WHERE user_id = $1'
        await ctx.pool.execute(query, member.id, pearkies)

        await ctx.send(f'{word} recebeu {pearkies} {ctx.constants.pearkies_emoji}.')


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Currency(bot))