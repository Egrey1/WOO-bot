from ..library import Context, deps, command, Cog

class VersionCommand(Cog):

    @command(name='version')
    async def version(self, ctx: Context):
        import random
        import logging
        await ctx.send(f'Версия бота: {deps.VERSION}')
        if random.randint(0, 100) <= 25:
            await ctx.send('25`.`', delete_after=3)
            logging.info('Сработало случайное событие для ' + ctx.author.name)