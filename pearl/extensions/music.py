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
from datetime import timedelta

import lavalink
import humanize
import discord
from discord.ext import commands

import config
from utils.errors import *


url_regex = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        lavalink.add_event_hook(self.track_hook)

    def cog_unload(self):
        self.lavalink._event_hooks.clear()

    @commands.Cog.listener()
    async def on_ready(self):
        if not hasattr(self, 'lavalink'):
            self.lavalink = lavalink.Client(self.bot.user.id, connect_back=True)
            self.lavalink.add_node('127.0.0.1', 2333, config.lavalink, 'br', 'pearl')
            self.bot.add_listener(self.lavalink.voice_update_handler, 'on_socket_response')

    async def track_hook(self, event: lavalink.Event) -> None:
        if isinstance(event, lavalink.events.QueueEndEvent):
            guild_id = int(event.player.guild_id)
            await self.connect_to(guild_id, None)

    async def connect_to(self, guild_id: int, channel_id: typing.Optional[str]) -> None:
        ws = self.bot._connection._get_websocket(guild_id)
        await ws.voice_state(str(guild_id), channel_id)

    async def cog_before_invoke(self, ctx: commands.Context):
        await self.ensure_voice(ctx)

    async def ensure_voice(self, ctx: commands.Context) -> None:
        player = self.lavalink.player_manager.create(ctx.guild.id, endpoint=str(ctx.guild.region))
        should_connect = ctx.command.name in ('play',)

        if not ctx.author.voice or not ctx.author.voice.channel:
            raise RequesterNotConnected()

        if not player.is_connected:
            if not should_connect:
                raise BotNotConnected()

            permissions = ctx.author.voice.channel.permissions_for(ctx.me)

            if not permissions.connect or not permissions.speak:
                raise CannotConnect()

            player.store('channel', ctx.channel.id)
            await self.connect_to(ctx.guild.id, str(ctx.author.voice.channel.id))
        else:
            if int(player.channel_id) != ctx.author.voice.channel.id:
                raise WrongChannel()

    @commands.command(aliases=['p'])
    async def play(self, ctx: commands.Context, *, query: str):
        player = self.lavalink.player_manager.get(ctx.guild.id)
        query = query.strip('<>')

        if not url_regex.match(query):
            query = f'ytsearch:{query}'

        results = await player.node.get_tracks(query)

        if not results or not results['tracks']:
            raise NothingFound()

        if results['loadType'] == 'PLAYLIST_LOADED':
            tracks = results['tracks']

            for track in tracks:
                player.add(requester=ctx.author.id, track=track)

            playlist_name = results['playlistInfo']['name']
            tracks_length = f'`{len(tracks)}` música' + ('' if len(tracks) == 1 else 's')

            title = 'Playlist adicionada'
            description = f'{playlist_name} - {tracks_length}'
        else:
            track = results['tracks'][0]

            track_name = discord.utils.escape_markdown(track['info']['title'])
            track_link = track['info']['uri']

            title = 'Música adicionada'
            description = f'[{track_name}]({track_link})'

            track = lavalink.models.AudioTrack(track, ctx.author.id, recommended=True)
            player.add(requester=ctx.author.id, track=track)

        await ctx.send(f'**{title}**\n{description}')

        if not player.is_playing:
            await player.play()

    @commands.command()
    async def pause(self, ctx: commands.Context):
        player = self.lavalink.player_manager.get(ctx.guild.id)
        
        if player.paused:
            raise AlreadyPaused()

        await player.set_pause(True)
        await ctx.send(f'Música foi pausada por {ctx.author.mention}.')

    @commands.command()
    async def resume(self, ctx: commands.Context):
        player = self.lavalink.player_manager.get(ctx.guild.id)
        
        if not player.paused:
            raise AlreadyResumed()

        await player.set_pause(False)
        await ctx.send(f'Música foi resumida por {ctx.author.mention}.')

    @commands.command(aliases=['s'])
    async def skip(self, ctx: commands.Context):
        player = self.lavalink.player_manager.get(ctx.guild.id)
        await player.skip()

        await ctx.send(f'Música pulada por {ctx.author.mention}.')

    @commands.command()
    async def seek(self, ctx: commands.Context, time: int):
        if time < 0:
            raise InvalidSeekTime()

        player = self.lavalink.player_manager.get(ctx.guild.id)
        delta = humanize.precisedelta(timedelta(seconds=time or 1), minimum_unit='seconds')

        await player.seek(time * 1000)
        await ctx.send(f'Tempo alterado para {delta}.')

    @commands.command()
    async def volume(self, ctx: commands.Context, volume: int):
        if not 0 <= volume <= 100:
            raise InvalidVolume()

        player = self.lavalink.player_manager.get(ctx.guild.id)
        
        await player.set_volume(volume * 10)
        await ctx.send(f'Volume alterado para {volume}%.')

    @commands.command(aliases=['np'])
    async def nowplaying(self, ctx: commands.Context):
        player = self.lavalink.player_manager.get(ctx.guild.id)
        current = player.current

        title = discord.utils.escape_markdown(current.title)
        duration = humanize.precisedelta(timedelta(milliseconds=current.duration))

        # TODO: Add "is_stream" and current music timestamp.
        messages = [
            f'Música: [{title}]({current.uri})',
            f'Canal: `{current.author}`',
            f'Duração: **{duration}**'
        ]

        size = 24
        placeholder = '▬' * size

        percentage = int((size * int(player.position)) / int(current.duration))
        messages.append(placeholder[:percentage] + '○' + placeholder[percentage + 1:])

        await ctx.send('\n'.join(messages))


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Music(bot))