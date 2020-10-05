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
import textwrap
from io import StringIO
from contextlib import redirect_stdout

from discord.ext import commands

from utils.codeblocks import codeblock_converter
from utils.repl import ExceptionReactor
from utils.menus import Menu


class Owner(commands.Cog):
    def __init__(self, bot: commands.Cog):
        self.bot = bot
        self._last_result = None

    def get_env(self, ctx: commands.Context) -> typing.Dict[str, typing.Any]:
        env = {
            'ctx': ctx,
            'bot': ctx.bot,
            'pool': ctx.pool,
            '_': self._last_result
        }

        env.update(globals())
        return env

    async def cog_check(self, ctx: commands.Context):
        if await ctx.bot.is_owner(ctx.author):
            return True

        raise commands.NotOwner('You do not own this bot')

    @commands.group(aliases=['wd'], invoke_without_command=True, ignore_extra=True)
    async def watchdog(self, ctx: commands.Context):
        pass

    @watchdog.command(name='python', aliases=['py'])
    async def watchdog_python(self, ctx: commands.Context, *, code: codeblock_converter):
        env = self.get_env(ctx)
        stdout = StringIO()

        code = re.sub(r';\s?', '\n', code.content).split('\n')
        
        cannot_starts_with = ('return', 'import', 'from', '  ')
        invalid_startswith = False

        for word in cannot_starts_with:
            if code[-1].startswith(word):
                invalid_startswith = True

        if not invalid_startswith:
            code[-1] = f'return {code[-1]}'

        body = textwrap.indent('\n'.join(code), '  ')

        async with ExceptionReactor(ctx):
            exec(f'async def coro():\n{body}', env)

            with redirect_stdout(stdout):
                coro = env['coro']
                ret = await coro()

            if ret is not None:
                self._last_result = ret

            value = stdout.getvalue()

            output = str(value or ret).replace(ctx.bot.http.token, '[token omitted]')
            fields = [{'name': 'Retornou', 'value': f'```css\n{type(ret)}```'}]

            menu = Menu(output, fields=fields, codeblock=True)
            await menu.start(ctx)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Owner(bot))