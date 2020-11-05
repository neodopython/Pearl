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

import re
import asyncio
import random
from datetime import timedelta
from async_timeout import timeout
from typing import Optional

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

        if isinstance(event, lavalink.events.TrackEndEvent):
            player = event.player
            player.store('skip_votes', 0)
            player.store('already_voted', [])

    async def connect_to(self, guild_id: int, channel_id: Optional[str]) -> None:
        ws = self.bot._connection._get_websocket(guild_id)
        await ws.voice_state(str(guild_id), channel_id)

    async def cog_before_invoke(self, ctx: commands.Context):
        await self.ensure_voice(ctx)

    async def ensure_voice(self, ctx: commands.Context) -> None:
        player = ctx.bot.lavalink.player_manager.create(ctx.guild.id, endpoint=str(ctx.guild.region))
        should_connect = ctx.command.name in ('play', 'search')

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
            player.store('skip_votes', 0)
            player.store('already_voted', [])
            await self.connect_to(ctx.guild.id, str(ctx.author.voice.channel.id))
        else:
            if int(player.channel_id) != ctx.author.voice.channel.id:
                raise WrongChannel()

    @commands.command(aliases=['p'])
    async def play(self, ctx: commands.Context, *, query: str):
        """Toca uma música com o título dado."""
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

            name = self.escape_markdown(track['info']['title'])
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
    async def search(self, ctx: commands.Context, *, query: str):
        """Procura por uma música e enfim adiciona ela através do índice dado."""
        player = ctx.bot.lavalink.player_manager.get(ctx.guild.id)
        query = query.strip('<>')

        if not url_regex.match(query):
            query = f'ytsearch:{query}'

        results = await player.node.get_tracks(query)

        if not results or not results['tracks']:
            raise NothingFound()

        tracks = results['tracks'][:10]

        def enumerate_track(value) -> str:
            i, track = value

            title = track['info']['title']
            author = track['info']['author']
            return f'`{i}.` **{title}** ({author})'
        
        all_tracks = map(enumerate_track, enumerate(tracks, start=1))
        tracks_message = await ctx.send('\n'.join(all_tracks))

        def check(message: discord.Message) -> bool:
            return message.author == ctx.author

        try:
            message = await ctx.bot.wait_for('message', check=check, timeout=60)
        except asyncio.TimeoutError:
            await ctx.send('Operação cancelada devido a inatividade.')
            return

        content = message.content
        if content == 'cancel':
            return await ctx.send('Cancelado.')

        try:
            track = tracks[int(content) - 1]
        except ValueError:
            raise InvalidValueIndex()
        except IndexError:
            raise InvalidMusicIndex()

        name = self.escape_markdown(track['info']['title'])
        url = track['info']['uri']
        author = track['info']['author']

        info = f'Música: [{name}]({url})\nCanal: **{author}**'

        try:
            duration = humanize.precisedelta(timedelta(milliseconds=track['info']['length']))
        except OverflowError:
            duration = '**[ao vivo]**'

        player.add(requester=ctx.author.id, track=track)
        await ctx.send(f'{info}\nDuração: **{duration}**', title='Música adicionada')

        if not player.is_playing:
            await player.play()

    @commands.command()
    async def pause(self, ctx: commands.Context):
        """Pausa a música caso esteja tocando."""
        player = ctx.bot.lavalink.player_manager.get(ctx.guild.id)
        
        if player.paused:
            raise AlreadyPaused()

        if not self.has_dj_permissions(player, ctx):
            raise NotDJ()

        await player.set_pause(True)
        await ctx.send(f'Música foi pausada por {ctx.author.mention}.')

    @commands.command()
    async def resume(self, ctx: commands.Context):
        """Resume a música caso esteja pausada."""
        player = ctx.bot.lavalink.player_manager.get(ctx.guild.id)
        
        if not player.paused:
            raise AlreadyResumed()

        if not self.has_dj_permissions(player, ctx):
            raise NotDJ()

        await player.set_pause(False)
        await ctx.send(f'Música foi resumida por {ctx.author.mention}.')

    @commands.command(aliases=['s'])
    async def skip(self, ctx: commands.Context):
        """Pula a música atual."""
        player = ctx.bot.lavalink.player_manager.get(ctx.guild.id)
        channel = ctx.me.voice.channel

        if not self.has_dj_permissions(player, ctx):
            already_voted = player.fetch('already_voted')
            if ctx.author.id in already_voted:
                raise AlreadyVoted()

            total_members = len(list(filter(lambda m: m.bot, channel.members)))
            needed_votes = round((total_members * 7) / 10)

            total_votes = player.fetch('skip_votes') + 1

            if total_votes < needed_votes:
                already_voted.append(ctx.author.id)
                player.store('skip_votes', total_votes)
                player.store('already_voted', already_voted)

                await ctx.send(f'Votado para pular esta música, `{total_votes}/{needed_votes}` votos necessários.')
                return

        await ctx.send(f'Música pulada por {ctx.author.mention}.')
        await player.skip()

    @commands.command()
    async def seek(self, ctx: commands.Context, time: int):
        """Pula a música para um determinado tempo."""
        if time < 0:
            raise InvalidSeekTime()

        player = ctx.bot.lavalink.player_manager.get(ctx.guild.id)

        if not self.has_dj_permissions(player, ctx):
            raise NotDJ()

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
        """Mostra qual música está atualmente tocando."""
        player = ctx.bot.lavalink.player_manager.get(ctx.guild.id)
        current = player.current

        if not current:
            raise BotNotPlaying()

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
        """Para o player de música e me disconecta do canal."""
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
        """Mostra a fila de música."""
        player = ctx.bot.lavalink.player_manager.get(ctx.guild.id)
        queue = player.queue

        titles = []
        for index, track in enumerate(queue, start=1):
            titles.append(f'`{index}.` **{self.escape_markdown(track.title)}** ({track.author})')

        menu = Menu(titles or 'Não há nada na playlist.', per_page=12)
        await menu.start(ctx)

    @commands.command()
    async def shuffle(self, ctx: commands.Context):
        """Embaralha a fila de música."""
        player = ctx.bot.lavalink.player_manager.get(ctx.guild.id)

        random.shuffle(player.queue)
        await ctx.send('Fila de músicas embaralhada.')

    # TODO: Add loop command.
    # TODO: Add move command.

    @commands.command(aliases=['lq', 'repeatqueue', 'rq'])
    async def loopqueue(self, ctx: commands.Context):
        """A fila de música se repetirá caso ativado.""" 
        player = ctx.bot.lavalink.player_manager.get(ctx.guild.id)
        is_repeating = player.repeat

        repeat = True if not is_repeating else False
        word = ('des' if is_repeating else '') + 'ativado'

        player.set_repeat(repeat)
        await ctx.send(f'Loop da fila {word}.')

    @commands.command()
    async def remove(self, ctx: commands.Context, index: int):
        """Remove uma música da fila pelo índice."""
        player = ctx.bot.lavalink.player_manager.get(ctx.guild.id)

        if not self.has_dj_permissions(player, ctx):
            raise NotDJ()

        if index > len(player.queue) or index <= 0:
            raise CannotRemoveMusic()

        index -= 1

        track = player.queue[index]
        title = self.escape_markdown(track.title)

        del player.queue[index]
        await ctx.send(f'[{title}]({track.uri}) foi removido da fila.')

    @commands.command()
    async def clear(self, ctx: commands.Context):
        """Limpa a fila de música."""
        player = ctx.bot.lavalink.player_manager.get(ctx.guild.id)

        if not self.has_dj_permissions(player, ctx):
            raise NotDJ()

        if not len(player.queue):
            return NothingInQueue()

        player.queue = []
        await ctx.send('A fila de música foi limpa.')


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Music(bot))