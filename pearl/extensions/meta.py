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
'''
The MIT License (MIT)

Copyright (c) 2015 Rapptz

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
'''

import inspect
import os

import discord
from discord.ext import commands


class Meta(commands.Cog):
    """Comandos relacionados ao Discord ou ao próprio bot."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def source(self, ctx: commands.Context, *, command: str = None):
        source_url = 'https://github.com/webkaiyo/Pearl'
        branch = 'master'

        if not command:
            return await ctx.send(source_url)

        if command == 'help':
            source = type(ctx.bot.help_command)
            module = source.__module__
            filename = inspect.getsourcefile(source)
        else:
            obj = ctx.bot.get_command(command.replace('.', ' '))
            if not obj:
                return await ctx.send('Comando não encontrado.')

            source = obj.callback.__code__
            module = obj.callback.__module__
            filename = source.co_filename

        lines, first_line = inspect.getsourcelines(source)
        if not module.startswith('discord'):
            location = 'pearl/' + os.path.relpath(filename).replace('\\', '/')
        else:
            location = module.replace('.', '/') + '.py'
            source_url = 'https://github.com/Rapptz/discord.py'

        final_url = f'{source_url}/blob/{branch}/{location}#L{first_line}-L{first_line + len(lines) - 1}'
        await ctx.send(final_url)

    @commands.command()
    async def avatar(self, ctx: commands.Context, member: discord.Member = None):
        member = member or ctx.author

        avatar = str(member.avatar_url_as(static_format='png'))
        content = f'Faça o download dessa imagem clicando [aqui]({avatar}).'

        await ctx.send(content, image=avatar)

def setup(bot: commands.Bot) -> None:
    bot.add_cog(Meta(bot))