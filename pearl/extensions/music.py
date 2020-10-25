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
import re
import asyncio
import random
from datetime import timedelta
from async_timeout import timeout

import lavalink
import humanize
import discord
from discord.ext import commands

import config
from utils.errors import *
from utils.menus import Menu


url_regex = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        if not hasattr(bot, 'lavalink'):
            bot.lavalink = lavalink.Client(bot.user.id, connect_back=True)
            bot.lavalink.add_node('127.0.0.1', 2333, config.lavalink, 'br', 'pearl')
            bot.add_listener(bot.lavalink.voice_update_handler, 'on_socket_response')

        lavalink.add_event_hook(self.track_hook)

    def cog_unload(self):
        self.bot.lavalink._event_hooks.clear()

    def escape_markdown(self, text: str) -> str:
        return discord.utils.escape_markdown(text)

    def has_dj_permissions(self, player: lavalink.DefaultPlayer, ctx: commands.Context) -> bool:
        is_dj = ctx.author == player.fetch('dj')
        is_admin = ctx.author.guild_permissions.manage_channels
        return True if is_dj or is_admin else False

    async def track_hook(self, event: lavalink.Event) -> None:
        if isinstance(event, lavalink.events.QueueEndEvent):
            player = event.player

            still_active = player.fetch('still_active')
            still_active.clear()

            try:
                async with timeout(300, loop=self.bot.loop):
                    await still_active.wait()
            except asyncio.TimeoutError:
                guild_id = int(event.player.guild_id)
                await self.connect_to(guild_id, None)

                ctx = player.fetch('ctx')
                await ctx.send('Saí do canal devido a inatividade de comandos.', author=None)

        if isinstance(event, lavalink.events.TrackStartEvent):
            player = event.player
            track = player.current

            ctx = player.fetch('ctx')
            player.fetch('still_active').set()

            requester = ctx.guild.get_member(track.requester).mention or '**[usuário desconhecido]**'

            try:
                duration = humanize.precisedelta(timedelta(milliseconds=track.duration))
            except OverflowError:
                duration = '**[ao vivo]**'

            messages = [
                f'Música: [{self.escape_markdown(track.title)}]({track.uri})',
                f'Canal: **{track.author}**',
                f'Duração: **{duration}**',
                f'Solicitante: {requester}'
            ]

            await ctx.send('\n'.join(messages), title='Tocando agora', author=None)

    async def connect_to(self, guild_id: int, channel_id: typing.Optional[str]) -> None:
        ws = self.bot._connection._get_websocket(guild_id)
        await ws.voice_state(str(guild_id), channel_id)

    async def cog_before_invoke(self, ctx: commands.Context):
        await self.ensure_voice(ctx)

    async def ensure_voice(self, ctx: commands.Context) -> None:
        player = ctx.bot.lavalink.player_manager.create(ctx.guild.id, endpoint=str(ctx.guild.region))
        should_connect = ctx.command.name in ('play',)

        if not ctx.author.voice or not ctx.author.voice.channel:
            raise RequesterNotConnected()

        if not player.is_connected:
            if not should_connect:
                raise BotNotConnected()

            permissions = ctx.author.voice.channel.permissions_for(ctx.me)

            if not permissions.connect or not permissions.speak:
                raise CannotConnect()

            player.store('ctx', ctx)
            player.store('dj', ctx.author.id)
            player.store('still_active', asyncio.Event(loop=ctx.bot.loop))
            await self.connect_to(ctx.guild.id, str(ctx.author.voice.channel.id))
        else:
            if int(player.channel_id) != ctx.author.voice.channel.id:
                raise WrongChannel()

    @commands.command(aliases=['p'])
    async def play(self, ctx: commands.Context, *, query: str):
        """Plays a music with given query."""
        player = ctx.bot.lavalink.player_manager.get(ctx.guild.id)
        query = query.strip('<>')

        if not url_regex.match(query):
            query = f'ytsearch:{query}'

        results = await player.node.get_tracks(query)

        if not results or not results['tracks']:
            raise NothingFound()

        if results['loadType'] == 'PLAYLIST_LOADED':
            tracks = results['tracks']
            total_length = 0

            for track in tracks:
                player.add(requester=ctx.author.id, track=track)
                total_length += track['info']['length']

            playlist_name = results['playlistInfo']['name']
            total_tracks = f'{len(tracks)} música' + ('' if len(tracks) == 1 else 's')

            title = f'Playlist adicionada - {total_tracks}'
            info = f'Playlist: `{playlist_name}`'
        else:
            track = results['tracks'][0]
            total_length = track['info']['length']

            name = discord.utils.escape_markdown(track['info']['title'])
            url = track['info']['uri']
            author = track['info']['author']

            title = 'Música adicionada'
            info = f'Música: [{name}]({url})\nCanal: **{author}**'

            track = lavalink.models.AudioTrack(track, ctx.author.id, recommended=True)
            player.add(requester=ctx.author.id, track=track)

        try:
            duration = humanize.precisedelta(timedelta(milliseconds=total_length))
        except OverflowError:
            duration = '**[ao vivo]**'

        await ctx.send(f'{info}\nDuração: **{duration}**', title=title)

        if not player.is_playing:
            await player.play()

    @commands.command()
    async def pause(self, ctx: commands.Context):
        """Pauses the current player."""
        player = ctx.bot.lavalink.player_manager.get(ctx.guild.id)
        
        if player.paused:
            raise AlreadyPaused()

        if not self.has_dj_permissions(player, ctx):
            raise NotDJ()

        await player.set_pause(True)
        await ctx.send(f'Música foi pausada por {ctx.author.mention}.')

    @commands.command()
    async def resume(self, ctx: commands.Context):
        """Resumes the current player."""
        player = ctx.bot.lavalink.player_manager.get(ctx.guild.id)
        
        if not player.paused:
            raise AlreadyResumed()

        if not self.has_dj_permissions(player, ctx):
            raise NotDJ()

        await player.set_pause(False)
        await ctx.send(f'Música foi resumida por {ctx.author.mention}.')

    @commands.command(aliases=['s'])
    async def skip(self, ctx: commands.Context):
        """Skips the current music."""
        player = ctx.bot.lavalink.player_manager.get(ctx.guild.id)

        await ctx.send(f'Música pulada por {ctx.author.mention}.')
        await player.skip()

    # TODO: Add docstring for this method.
    @commands.command()
    async def seek(self, ctx: commands.Context, time: int):
        if time < 0:
            raise InvalidSeekTime()

        if not self.has_dj_permissions(player, ctx):
            raise NotDJ()

        player = ctx.bot.lavalink.player_manager.get(ctx.guild.id)
        delta = humanize.precisedelta(timedelta(seconds=time or 1), minimum_unit='seconds')

        await player.seek(time * 1000)
        await ctx.send(f'Tempo alterado para {delta}.')

    @commands.command()
    async def volume(self, ctx: commands.Context, volume: int):
        """Changes the player volume."""
        if not 0 <= volume <= 100:
            raise InvalidVolume()

        player = ctx.bot.lavalink.player_manager.get(ctx.guild.id)
        
        await player.set_volume(volume)
        await ctx.send(f'Volume alterado para {volume}%.')

    @commands.command(aliases=['np'])
    async def nowplaying(self, ctx: commands.Context):
        """Shows what music is currently playing."""
        player = ctx.bot.lavalink.player_manager.get(ctx.guild.id)
        current = player.current

        title = self.escape_markdown(current.title)
        requester = ctx.guild.get_member(current.requester).mention or '**[usuário desconhecido]**'

        try:
            duration = humanize.precisedelta(timedelta(milliseconds=current.duration))
        except OverflowError:
            duration = '**[ao vivo]**'

        # TODO: Add "is_stream" and current music timestamp.
        messages = [
            f'Música: [{title}]({current.uri})',
            f'Canal: **{current.author}**',
            f'Duração: **{duration}**',
            f'Solicitante: {requester}'
        ]

        size = 24
        placeholder = '▬' * size

        percentage = int((size * int(player.position)) / int(current.duration))
        messages.append(placeholder[:percentage] + '○' + placeholder[percentage + 1:])

        await ctx.send('\n'.join(messages))

    @commands.command(aliases=['dc', 'stop'])
    async def disconnect(self, ctx: commands.Context):
        """Stop player and disconnects bot from channel."""
        player = ctx.bot.lavalink.player_manager.get(ctx.guild.id)

        if not player.is_connected:
            raise BotNotConnected()

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            raise WrongChannel()

        if not self.has_dj_permissions(player, ctx):
            raise NotDJ()

        player.queue.clear()
        player.fetch('still_active').set()
        
        await player.stop()
        await self.connect_to(ctx.guild.id, None)

        await ctx.send(f'Fui desconectada por {ctx.author.mention}.')

    @commands.command(aliases=['q'])
    async def queue(self, ctx: commands.Context):
        """Show the current queue."""
        player = ctx.bot.lavalink.player_manager.get(ctx.guild.id)
        queue = player.queue

        titles = []
        for index, track in enumerate(queue, start=1):
            titles.append(f'`{index}.` **{self.escape_markdown(track.title)}** ({track.author})')

        menu = Menu(titles or 'Não há nada na playlist.', per_page=12)
        await menu.start(ctx)

    # TODO: Add docstring for this method.
    @commands.command()
    async def shuffle(self, ctx: commands.Context):
        player = ctx.bot.lavalink.player_manager.get(ctx.guild.id)

        random.shuffle(player.queue)
        await ctx.send('Fila de músicas embaralhada.')

    # TODO: Add docstring for this method.
    @commands.command(aliases=['lq', 'repeatqueue', 'rq'])
    async def loopqueue(self, ctx: commands.Context):
        player = ctx.bot.lavalink.player_manager.get(ctx.guild.id)
        is_repeating = player.repeat

        repeat = True if not is_repeating else False
        word = ('des' if is_repeating else '') + 'ativado'

        player.set_repeat(repeat)
        await ctx.send(f'Loop da fila {word}.')

    # TODO: Add docstring for this method.
    @commands.command()
    async def remove(self, ctx: commands.Context, index: int):
        player = ctx.bot.lavalink.player_manager.get(ctx.guild.id)

        if index > len(player.queue) or index <= 0:
            raise CannotRemoveMusic()

        index -= 1

        track = player.queue[index]
        title = self.escape_markdown(track.title)

        del player.queue[index]
        await ctx.send(f'[{title}]({track.uri}) foi removido da fila.')

    # TODO: Add docstring for this method.
    @commands.command()
    async def clear(self, ctx: commands.Context):
        player = ctx.bot.lavalink.player_manager.get(ctx.guild.id)

        if not len(player.queue):
            return NothingInQueue()

        player.queue = []
        await ctx.send('A fila foi limpa.')


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Music(bot))