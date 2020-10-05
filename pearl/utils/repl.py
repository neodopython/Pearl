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
MIT License

Copyright (c) 2020 Devon (Gorialis) R

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
import traceback

from discord.ext import commands

from .menus import Menu

async def send_traceback(ctx: commands.Context, verbosity: int, *exception_info):
    type_, value, trace = exception_info
    
    content = ''.join(traceback.format_exception(type_, value, trace, verbosity))
    content = content.replace('``', '`\u200b`').replace(ctx.bot.http.token, '[token omitted]')

    paginator = commands.Paginator(prefix='```py')
    for line in content.split('\n'):
        paginator.add_line(line)

    menu = Menu(paginator.pages)
    await menu.start(ctx) 


class ExceptionReactor:
    def __init__(self, ctx: commands.Context):
        self.ctx = ctx
        self.raised = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, type_, value, traceback):
        if not value:
            return await self.ctx.message.add_reaction('checkmark:762675626582736927')

        self.raised = True

        if isinstance(value, (SyntaxError, asyncio.TimeoutError)):
            verbosity = 0
        else:
            verbosity = 8

        await send_traceback(self.ctx, verbosity, type_, value, traceback)
        return True