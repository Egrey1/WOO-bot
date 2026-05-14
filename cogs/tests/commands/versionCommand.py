from ..library import Context, deps, command, Cog

class VersionCommand(Cog):

    @command(name='version')
    async def version(self, ctx: Context):
        await ctx.send(f'Версия бота: {deps.VERSION}')