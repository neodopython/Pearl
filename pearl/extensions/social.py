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

from typing import List

import nekos
import discord
from discord.ext import commands

from utils.errors import *
from utils.formats import human_join


class Social(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def valid_mentions(self, ctx: commands.Context, members: List[discord.Member]):
        for member in members:
            if member == ctx.author:
                raise MemberIsAuthor()

            if member.bot:
                raise MemberIsBot()

            if len(members) != len(set(members)):
                raise ListHasDuplicates()

    @commands.command()
    async def hug(self, ctx: commands.Context, members: commands.Greedy[discord.Member]):
        self.valid_mentions(ctx, members)
        image = await ctx.loop.run_in_executor(None, nekos.img, 'hug')

        cuteheart = ctx.constants.cuteheart_emoji
        all_members = human_join([member.name for member in members], final='e')

        await ctx.send(title=f'{cuteheart} {ctx.author.name} abraçou {all_members}!', image=image)

    @commands.command()
    async def kiss(self, ctx: commands.Context, members: commands.Greedy[discord.Member]):
        self.valid_mentions(ctx, members)
        image = await ctx.loop.run_in_executor(None, nekos.img, 'kiss')

        cuteheart = ctx.constants.cuteheart_emoji
        all_members = human_join([member.name for member in members], final='e')

        await ctx.send(title=f'{cuteheart} {ctx.author.name} beijou {all_members}!', image=image)

    @commands.command()
    async def pat(self, ctx: commands.Context, members: commands.Greedy[discord.Member]):
        self.valid_mentions(ctx, members)
        image = await ctx.loop.run_in_executor(None, nekos.img, 'pat')

        cuteheart = ctx.constants.cuteheart_emoji
        all_members = human_join([member.name for member in members], final='e')

        await ctx.send(title=f'{cuteheart} {ctx.author.name} fez carinho em {all_members}!', image=image)

    @commands.command()
    async def tickle(self, ctx: commands.Context, members: commands.Greedy[discord.Member]):
        self.valid_mentions(ctx, members)
        image = await ctx.loop.run_in_executor(None, nekos.img, 'tickle')

        cuteheart = ctx.constants.cuteheart_emoji
        all_members = human_join([member.name for member in members], final='e')

        await ctx.send(title=f'{cuteheart} {ctx.author.name} fez cócegas em {all_members}!', image=image)
    
    @commands.command()
    async def poke(self, ctx: commands.Context, members: commands.Greedy[discord.Member]):
        self.valid_mentions(ctx, members)
        image = await ctx.loop.run_in_executor(None, nekos.img, 'poke')

        cuteheart = ctx.constants.cuteheart_emoji
        all_members = human_join([member.name for member in members], final='e')

        await ctx.send(title=f'{cuteheart} {ctx.author.name} cutucou {all_members}!', image=image)

    @commands.command()
    async def slap(self, ctx: commands.Context, members: commands.Greedy[discord.Member]):
        self.valid_mentions(ctx, members)
        image = await ctx.loop.run_in_executor(None, nekos.img, 'slap')

        cuteheart = ctx.constants.cuteheart_emoji
        all_members = human_join([member.name for member in members], final='e')

        await ctx.send(title=f'{cuteheart} {ctx.author.name} bateu em {all_members}!', image=image)

    @commands.command()
    async def cuddle(self, ctx: commands.Context, members: commands.Greedy[discord.Member]):
        self.valid_mentions(ctx, members)
        image = await ctx.loop.run_in_executor(None, nekos.img, 'cuddle')

        cuteheart = ctx.constants.cuteheart_emoji
        all_members = human_join([member.name for member in members], final='e')

        await ctx.send(title=f'{cuteheart} {ctx.author.name} mimou {all_members}!', image=image)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Social(bot))