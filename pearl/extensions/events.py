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

from datetime import timedelta

import discord
import humanize
from discord.ext import commands

from utils.errors import *


class Events(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def get_cooldown_message(self, ctx: commands.Context, error: commands.CommandOnCooldown) -> str:
        delta = timedelta(seconds=int(error.retry_after))
        precise_delta = humanize.precisedelta(delta)        
        return f'Espere **{precise_delta}** para usar este comando novamente.'

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        query = 'INSERT INTO settings (guild_id) VALUES ($1)'
        await self.bot.pool.execute(query, guild.id)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        query = 'DELETE FROM settings WHERE guild_id = $1'
        await self.bot.pool.execute(query, guild.id)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        ignored = ()
        error = getattr(error, 'original', error)

        if isinstance(error, ignored):
            return

        errors = {
            RequesterNotConnected: 'Conecte-se a um canal de voz antes de usar comandos de música.',
            BotNotConnected: 'Não estou conectada.',
            CannotConnect: 'Não consigo me conectar por falta de permissões (eu tenho permissão de conectar **e** falar?).',
            WrongChannel: 'Você precisa estar no mesmo canal que eu.',
            NothingFound: 'Nenhuma música encontrada.',
            AlreadyPaused: 'A música já está pausada.',
            AlreadyResumed: 'A música não está pausada.',
            InvalidSeekTime: 'Tempo inválido.',
            InvalidVolume: 'Volume inválido.',
            NotDJ: 'Você não é o DJ ou você não tem permissões para usar este comando.',
            AlreadyVoted: 'Você já votou para pular esta música.',
            InvalidValueIndex: 'Você digitou um valor inválido.',
            InvalidMusicIndex: 'Esta lista não possui este índice.',
            commands.CommandOnCooldown: self.get_cooldown_message,
            BotNotPlaying: 'Eu não estou tocando nenhuma música.',
            commands.BadArgument: 'Argumento inválido.'
        }

        if type(error) in errors:
            value = errors[type(error)]
            if callable(value):
                value = value(ctx, error)
            
            return await ctx.send(value)

        raise error


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Events(bot))