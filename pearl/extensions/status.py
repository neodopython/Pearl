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

from itertools import cycle

import discord
from discord.ext import commands, tasks


class Status(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.set_status.start()

    @tasks.loop(minutes=5.0)
    async def set_status(self):
        name, type_ = next(self.activities)
        name = name.format(users=users, guilds=guilds)
        
        guilds = len(self.bot.guilds)
        users = len(self.bot.users) - 1

        activity = discord.Activity(name=name, type=type_)
        status = discord.Status.dnd

        await self.bot.change_presence(activity=activity, status=status)

    @set_status.before_loop
    async def before_set_status(self):
        await self.bot.wait_until_ready()
        self.activities = cycle([
            ('{guilds} servidores', discord.ActivityType.watching),
            ('{users} usuários', discord.ActivityType.listening)
        ])

def setup(bot: commands.Bot) -> None:
    bot.add_cog(Status(bot))