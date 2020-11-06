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

from typing import Union

import discord
import emoji
from discord.ext import commands
from pyfiglet import Figlet, FigletFont
from asyncdagpi import ImageFeatures

from utils.errors import ResponseError


_ALL_EMOJIS = list(emoji.EMOJI_UNICODE.values())


class Fun(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=['randomcat'])
    async def cat(self, ctx: commands.Context):
        """Envia um gif de um gatinho fofo aleatório."""
        async with ctx.bot.session.get('http://aws.random.cat/meow') as response:
            if response.status != 200:
                raise ResponseError()

            json = await response.json()
            await ctx.send(image=json['file'])

    @commands.command(aliases=['randomdog'])
    async def dog(self, ctx: commands.Context):
        """Envia um gif de um cachorrinho fofo aleatório."""
        async with ctx.bot.session.get('https://random.dog/woof.json') as response:
            if response.status != 200:
                raise ResponseError()

            json = await response.json()
            await ctx.send(image=json['url'])

    @commands.command(aliases=['sheriff'])
    async def cowboy(self, ctx: commands.Context, target: Union[discord.Emoji, str]):
        """Olá, parceiro! Eu sou um cowboy feito do que você quiser."""
        if isinstance(target, str):
            if target not in _ALL_EMOJIS:
                raise commands.BadArgument()

        cowboy = '⠀ ⠀ ⠀  🤠\n　   {0}{0}{0}\n    {0}   {0}　{0}\n   👇   {0}{0} 👇\n  　  {0}　{0}\n　   {0}　 {0}\n　    👢     👢'
        await ctx.channel.send(cowboy.format(target))

    @commands.group(name='ascii', invoke_without_command=True)
    async def ascii_(self, ctx: commands.Context, font: str, *, text: str):
        figlet = Figlet(font=font)
        rendered_text = figlet.renderText(text)

        await ctx.send(f'```\n{rendered_text}\n```')

    @ascii_.command(name='fonts')
    async def ascii_fonts(self, ctx: commands.Context):
        all_fonts = FigletFont.getFonts()
        fonts = [f'`{font}`' for font in all_fonts]

        await ctx.paginate(', '.join(fonts))

    @commands.command()
    async def wasted(self, ctx: commands.Context, *, member: discord.Member = None):
        member = member or ctx.author
        
        url = str(member.avatar_url_as(static_format='png', size=1024))
        image = await ctx.dagpi.image_process(ImageFeatures.wasted(), url)

        filename = f'wasted.{image.format}'
        file = discord.File(fp=image.image, filename=filename)

        await ctx.send(file=file, image=f'attachment://{filename}')

    @commands.command(aliases=['pixelate'])
    async def pixel(self, ctx: commands.Context, *, member: discord.Member = None):
        member = member or ctx.author
        
        url = str(member.avatar_url_as(static_format='png', size=1024))
        image = await ctx.dagpi.image_process(ImageFeatures.pixel(), url)

        filename = f'pixel.{image.format}'
        file = discord.File(fp=image.image, filename=filename)

        await ctx.send(file=file, image=f'attachment://{filename}')

    @commands.command()
    async def triggered(self, ctx: commands.Context, *, member: discord.Member = None):
        member = member or ctx.author
        
        url = str(member.avatar_url_as(static_format='png', size=1024))
        image = await ctx.dagpi.image_process(ImageFeatures.triggered(), url)

        filename = f'triggered.{image.format}'
        file = discord.File(fp=image.image, filename=filename)

        await ctx.send(file=file, image=f'attachment://{filename}')

    @commands.command()
    async def invert(self, ctx: commands.Context, *, member: discord.Member = None):
        member = member or ctx.author
        
        url = str(member.avatar_url_as(static_format='png', size=1024))
        image = await ctx.dagpi.image_process(ImageFeatures.invert(), url)

        filename = f'invert.{image.format}'
        file = discord.File(fp=image.image, filename=filename)

        await ctx.send(file=file, image=f'attachment://{filename}')

    @commands.command()
    async def sobel(self, ctx: commands.Context, *, member: discord.Member = None):
        member = member or ctx.author
        
        url = str(member.avatar_url_as(static_format='png', size=1024))
        image = await ctx.dagpi.image_process(ImageFeatures.sobel(), url)

        filename = f'sobel.{image.format}'
        file = discord.File(fp=image.image, filename=filename)

        await ctx.send(file=file, image=f'attachment://{filename}')

    @commands.command()
    async def jail(self, ctx: commands.Context, *, member: discord.Member = None):
        member = member or ctx.author
        
        url = str(member.avatar_url_as(static_format='png', size=1024))
        image = await ctx.dagpi.image_process(ImageFeatures.jail(), url)

        filename = f'jail.{image.format}'
        file = discord.File(fp=image.image, filename=filename)

        await ctx.send(file=file, image=f'attachment://{filename}')

    @commands.command(aliases=['whyareyougae'])
    async def whyareyougay(self, ctx: commands.Context, member: discord.Member, author: discord.Member = None):
        author = author or ctx.author
        
        member_avatar = str(member.avatar_url_as(static_format='png', size=1024))
        author_avatar = str(author.avatar_url_as(static_format='png', size=1024))
        image = await ctx.dagpi.image_process(ImageFeatures.why_are_you_gay(), member_avatar, url2=author_avatar)

        filename = f'why_are_you_gay.{image.format}'
        file = discord.File(fp=image.image, filename=filename)

        await ctx.send(file=file, image=f'attachment://{filename}')


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Fun(bot))