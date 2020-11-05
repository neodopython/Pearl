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

import contextlib
import logging
import os
import re
import asyncio
import typing
import importlib
from datetime import datetime

import discord
import asyncpg
import humanize
import aiohttp
import asyncdagpi
from discord.ext import commands

import config
from utils.context import Context


async def get_prefix(bot: commands.Bot, message: discord.Message) -> typing.Tuple[str]:
    """Returns a tuple with guild's custom prefix and global prefix."""
    query = 'SELECT prefix FROM settings WHERE guild_id = $1'
    fetch = await bot.pool.fetchrow(query, message.guild.id)

    if not fetch:
        insert_query = 'INSERT INTO settings (guild_id) VALUES ($1)'
        await bot.pool.execute(insert_query, message.guild.id)

        # re-fetch data
        fetch = await bot.pool.fetchrow(query, message.guild.id)
    
    return (fetch['prefix'], 'pearl ', 'hey pearl pls ')


class Pearl(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=get_prefix, intents=discord.Intents.all())
        run = self.loop.run_until_complete

        self.pool = run(create_pool(config.postgres, loop=self.loop))
        self.session = run(create_session(self.http.connector, loop=self.loop))
        self.dagpi = asyncdagpi.Client(config.dagpi, loop=self.loop, session=self.session)

        self.logger = logging.getLogger('pearl')
        self.all_extensions = []

        for root, _, items in os.walk('extensions'):
            files = filter(lambda f: f.endswith('.py'), items)

            for f in files:
                file_name, _ = os.path.splitext(f)
                path = os.path.join(root, file_name)

                self.all_extensions.append(re.sub(r'\\|\/', '.', path))

    @property
    def constants(self):
        return importlib.import_module('utils.constants')

    async def on_message(self, message: discord.Message) -> None:
        """Event overwritten to ignore guilds."""
        if not message.guild:
            return

        await self.process_commands(message)

    async def on_ready(self) -> None:
        """Loads all extensions when bot is ready."""
        if not hasattr(self, 'uptime'):
            self.uptime = datetime.utcnow()

        for extension in self.all_extensions:
            try:
                self.load_extension(extension)
            except:
                self.logger.exception('The extension \'%s\' could not be loaded' % extension)
            else:
                self.logger.info('The extension \'%s\' has been loaded' % extension)

        print(f'Logged-in with {len(self.guilds)} guilds and {len(self.users)} users')

    async def process_commands(self, message: discord.Message) -> None:
        """Event overwritten for adding some checks."""
        ctx = await self.get_context(message, cls=Context)

        if not ctx.command:
            return

        if ctx.author.bot:
            return

        await ctx.trigger_typing()
        await self.invoke(ctx)

    async def close(self) -> None:
        """Closes the aiohttp session and then closes bot."""
        await self.session.close()
        await super().close()


async def create_pool(uri: str, *, loop: asyncio.BaseEventLoop) -> asyncpg.pool.Pool:
    """Creates a PostgreSQL pool."""
    def _encode_jsonb(value: dict) -> str:
        return json.dumps(value)

    def _decode_jsonb(value: str) -> dict:
        return json.loads(value)

    async def _init(conn: asyncpg.Connection):
        await conn.set_type_codec('jsonb', schema='pg_catalog', encoder=_encode_jsonb, decoder=_decode_jsonb)

    return await asyncpg.create_pool(uri, init=_init, loop=loop)


async def create_session(connector: aiohttp.BaseConnector, *, loop: asyncio.BaseEventLoop) -> aiohttp.ClientSession:
    """Creates an aiohttp session to make web requests."""
    return aiohttp.ClientSession(loop=loop)


@contextlib.contextmanager
def setup_logging() -> None:
    """Setup a file-based logging."""
    try:
        # __enter__
        dt_format = '%Y-%m-%d %H:%M:%S'

        logging.getLogger('discord').setLevel(logging.INFO)
        logging.getLogger('discord.http').setLevel(logging.WARN)
    
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)

        handler = logging.FileHandler(filename='logs/pearl.log', encoding='utf-8', mode='w')
        formatter = logging.Formatter('[{asctime}] [{levelname}] {name}: {message}', dt_format, style='{')
    
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        yield
    finally:
        # __exit__
        for handler in logger.handlers:
            handler.close()
            logger.removeHandler(handler)


def main() -> None:
    humanize.i18n.activate('pt_BR')
    
    pearl = Pearl()
    pearl.run(config.token)


if __name__ == '__main__':
    with setup_logging():
        main()