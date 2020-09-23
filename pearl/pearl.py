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

import discord
from discord.ext import commands

import config


async def get_prefix(bot: commands.Bot, message: discord.Message) -> str:
    """Get bot's prefix."""
    return '?'


class Pearl(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=get_prefix)
        
        self.logger = logging.getLogger()
        self.all_extensions = []

        for root, _, items in os.walk('extensions'):
            files = filter(lambda f: f.endswith('.py'), items)

            for f in files:
                file_name, _ = os.path.splitext(f)
                path = os.path.join(root, file_name)

                self.all_extensions.append(re.sub(r'\\|\/', '.', path))

    def run(self, token: str) -> None:
        """Loads all extensions and then runs the bot."""
        for extension in self.all_extensions:
            try:
                self.load_extension(extension)
            except:
                self.logger.exception('The extension \'%s\' could not be loaded' % extension)
            else:
                self.logger.info('The extension \'%s\' has been loaded' % extension)

        super().run(token)


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

        handler = logging.FileHandler(filename='pearl.log', encoding='utf-8', mode='w')
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
    pearl = Pearl()
    pearl.run(config.token)


if __name__ == '__main__':
    with setup_logging():
        main()