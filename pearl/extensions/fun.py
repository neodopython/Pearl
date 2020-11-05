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

import discord
import emoji
from discord.ext import commands
from pyfiglet import Figlet, FigletFont

from utils.errors import ResponseError
from utils.menus import Menu


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
    async def cowboy(self, ctx: commands.Context, target: typing.Union[discord.Emoji, str]):
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

        menu = Menu(', '.join(fonts))
        await menu.start(ctx)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Fun(bot))