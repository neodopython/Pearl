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

import functools

import discord
from discord.ext import commands

from utils.errors import *
from utils.menus import Menu


def not_empty():
    def wrapper(func):
        @functools.wraps(func)
        async def wrapped(self, ctx: commands.Context, *args, **kwargs):
            query = 'SELECT list FROM todos WHERE user_id = $1'
            fetch = await ctx.pool.fetchrow(query, ctx.author.id)

            if not fetch['list']:
                return await ctx.send('Sua lista já está vazia, não há nada o que deletar.')

            return await func(self, ctx, *args, **kwargs)
        return wrapped
    return wrapper


class Reminders(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.limit = 165

    async def insert_into(self, ctx: commands.Context, *, member: discord.Member = None):
        member = member or ctx.author

        query = 'INSERT INTO todos (user_id) VALUES ($1) ON CONFLICT (user_id) DO NOTHING'
        await ctx.pool.execute(query, member.id)

    @commands.group()
    @commands.before_invoke(insert_into)
    async def todo(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(self.todo)

    @todo.command(name='add')
    async def todo_add(self, ctx: commands.Context, *, to_do: str):
        if len(to_do) >= self.limit:
            return await ctx.send(f'Seu lembrete não pode ter mais que `{self.limit}` caracteres.')

        query = 'UPDATE todos SET list = array_append(list, $2) WHERE user_id = $1'
        await ctx.pool.execute(query, ctx.author.id, to_do)

        await ctx.send(f'Adicionado para sua lista: **{to_do}**')

    @todo.command(name='list', aliases=['all'])
    async def todo_list(self, ctx: commands.Context, *, member: discord.Member = None):
        member = member or ctx.author
        await self.insert_into(ctx, member=member)

        query = 'SELECT list FROM todos WHERE user_id = $1'
        fetch = await ctx.pool.fetchrow(query, member.id)

        values = [f'`{i}.` {value}' for i, value in enumerate(fetch['list'], start=1)]

        if not values:
            return await ctx.send('Não há nada para ver aqui.')

        menu = Menu(values, per_page=12)
        await menu.start(ctx)

    @todo.command(name='remove', aliases=['delete'])
    @not_empty()
    async def todo_remove(self, ctx: commands.Context, index: int):
        query = 'SELECT list FROM todos WHERE user_id = $1'
        fetch = await ctx.pool.fetchrow(query, ctx.author.id)

        indexes = dict(enumerate(fetch['list'], start=1))
        value = indexes.get(index, None)

        if not value:
            return await ctx.send(f'Não há um ID `{index}` na sua lista.')

        query = '''
            UPDATE todos
                SET list = list[:$2 - 1] || list[$2 + 1:]
            WHERE user_id = $1
        '''
        await ctx.pool.execute(query, ctx.author.id, index)

        await ctx.send(f'O ID `{index}` foi removido da lista.')

    @todo.command(name='clear')
    @not_empty()
    async def todo_clear(self, ctx: commands.Context):
        result = await ctx.prompt('Você tem certeza que quer deletar toda sua lista?')
        if not result:
            return

        query = 'DELETE FROM todos WHERE user_id = $1'
        await ctx.pool.execute(query, ctx.author.id)

        await ctx.send('Sua lista foi limpa com sucesso.')


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Reminders(bot))