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

from datetime import datetime

import humanize
from discord.ext import commands


class Stats(commands.Cog, name='Estatísticas'):
    """Comandos que mostram algumas estatísticas do bot."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def uptime(self, ctx: commands.Context):
        delta = humanize.precisedelta(ctx.bot.uptime, format='%0.0f')
        await ctx.send(f'Estou online há **{delta}**.')


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Stats(bot))