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

import zlib
import re
import os
import discord
from typing import Optional, Dict
from io import BytesIO

from discord.ext import commands

from utils import fuzzy


class SphinxReader:
    BUFFER_SIZE = 16 * 1024

    def __init__(self, buffer: bytes):
        self.stream = BytesIO(buffer)

    def readline(self) -> str:
        return self.stream.readline().decode('utf-8')

    def read_compressed_chunks(self):
        decompressor = zlib.decompressobj()

        while True:
            chunk = self.stream.read(self.BUFFER_SIZE)
            if not len(chunk):
                break

            yield decompressor.decompress(chunk)
        yield decompressor.flush()

    def read_compressed_lines(self):
        buffer = b''

        for chunk in self.read_compressed_chunks():
            buffer += chunk
            position = buffer.find(b'\n')

            while position != -1:
                yield buffer[:position].decode('utf-8')
                buffer = buffer[position + 1:]
                position = buffer.find(b'\n')


class API(commands.Cog):
    """Comandos relacionados ao `discord.py`."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def parse_inv_objects(self, stream: SphinxReader, url: str):
        result = {}
        inv_version = stream.readline().rstrip()

        if inv_version != '# Sphinx inventory version 2':
            raise RuntimeError('Invalid objects.inv file version.')

        project_name = stream.readline().rstrip()[11:]
        version = stream.readline().rstrip()[11:]

        line = stream.readline()
        if 'zlib' not in line:
            raise RuntimeError('Invalid objects.inv file, not z-lib compatible.')

        entry_regex = re.compile(r'(?x)(.+?)\s+(\S*:\S*)\s+(-?\d+)\s+(\S+)\s+(.*)')
        for line in stream.read_compressed_lines():
            match = entry_regex.match(line.rstrip())
            if not match:
                return

            name, directive, prio, location, disp_name = match.groups()
            domain, _, subdirective = directive.partition(':')

            if directive == 'py:module' and name in result:
                continue

            if directive == 'std:doc':
                subdirective = 'label'

            if location.endswith('$'):
                location = location[:-1] + name

            key = name if disp_name == '-' else disp_name
            prefix = f'{subdirective}:' if domain == 'std' else ''

            if project_name == 'discord.py':
                key = key.replace('discord.ext.commands.', '').replace('discord.', '')

            result[f'{prefix}{key}'] = os.path.join(url, location)

        return result

    async def build_rtfm(self, pages: Dict[str, str]) -> None:
        cache = {}
        for key, page in pages.items():
            cache[key] = {}

            async with self.bot.session.get(page + '/objects.inv') as response:
                if response.status != 200:
                    raise RuntimeError('Cannot build RTFM lookup table, try again later')

                stream = SphinxReader(await response.read())
                cache[key] = self.parse_inv_objects(stream, page)

            self._rtfm_cache = cache

    async def do_rtfm(self, ctx: commands.Context, query: Optional[str], key: str) -> None:
        pages = {
            'latest': 'https://discordpy.readthedocs.io/en/latest',
            'python': 'https://docs.python.org/3'
        }

        if not query:
            return await ctx.send(pages[key])

        if not hasattr(self, '_rtfm_cache'):
            await ctx.trigger_typing()
            await self.build_rtfm(pages)

        query = re.sub(r'^(?:discord\.(?:ext\.)?)?(?:commands\.)?(.+)', r'\1', query)

        if key.startswith('latest'):
            obj = query.lower()
            for name in dir(discord.abc.Messageable):
                if name[0] == '_':
                    continue

                if obj == name:
                    query = f'abc.Messageable.{name}'
                    break

        cache = list(self._rtfm_cache[key].items())
        matches = fuzzy.finder(query, cache, key=lambda item: item[0], lazy=False)[:8]

        if len(matches) == 0:
            return await ctx.send('Nada encontrado, você digitou corretamente?')

        content = '\n'.join(f'[`{key}`]({url})' for key, url in matches)
        await ctx.send(content)

    @commands.group(aliases=['rtfd'], invoke_without_command=True)
    async def rtfm(self, ctx: commands.Context, *, query: str = None):
        await self.do_rtfm(ctx, query, 'latest')

    @rtfm.command(name='python', aliases=['py'])
    async def rtfm_python(self, ctx: commands.Context, *, query: str = None):
        await self.do_rtfm(ctx, query, 'python')


def setup(bot: commands.Bot) -> None:
    bot.add_cog(API(bot))