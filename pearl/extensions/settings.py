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

from discord.ext import commands


class Settings(commands.Cog, name='Configurações'):
    """Configurações do servidor ou do próprio bot."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.limit = 6

    @commands.group(invoke_without_command=True)
    async def prefix(self, ctx: commands.Context):
        """Mostra o prefixo do servidor."""
        query = 'SELECT prefix FROM settings WHERE guild_id = $1'
        fetch = await ctx.pool.fetchrow(query, ctx.guild.id)

        prefix = fetch['prefix']
        await ctx.send(f'O prefixo deste servidor é `{prefix}`.')

    @prefix.command(name='set')
    @commands.has_permissions(manage_guild=True)
    async def prefix_set(self, ctx: commands.Context, prefix: str):
        """Muda o prefixo do servidor."""
        if len(prefix) > self.limit:
            return await ctx.send(f'Prefixo muito grande, o limite é `{self.limit}` caracteres.')

        query = 'SELECT prefix FROM settings WHERE guild_id = $1'
        fetch = await ctx.pool.fetchrow(query, ctx.guild.id)

        if prefix == fetch['prefix']:
            return await ctx.send('Este já é o prefixo atual do servidor.')

        query = 'UPDATE settings SET prefix = $2 WHERE guild_id = $1'
        await ctx.pool.execute(query, ctx.guild.id, prefix)

        await ctx.send(f'Você alterou o prefixo do servidor para `{prefix}`.')


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Settings(bot))