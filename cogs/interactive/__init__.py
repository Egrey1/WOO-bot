from disnake.ext.commands import Cog, command
from . import objects

class InteractiveEvents(Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @command('интерактив')
    async def interactive(self, ctx):
        ep = objects.EventPlayer(ctx.author.id)
        # ep.tags = list(set(ep.tags + ['enabled']))
        await ctx.send('На данный момент никаких событий нет')
        

def setup(bot):
    bot.add_cog(InteractiveEvents(bot))