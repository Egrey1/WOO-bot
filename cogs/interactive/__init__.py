from disnake.ext.commands import Cog, command, Context
from disnake import Embed
from . import objects

class InteractiveEvents(Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @command('интерактив')
    async def interactive(self, ctx):
        ep = objects.EventPlayer(ctx.author.id)
        # ep.tags = list(set(ep.tags + ['enabled']))
        await ctx.send('На данный момент никаких событий нет')
    
    @command('interactive_event')
    async def event_interactive(self, ctx: Context):
        if (ctx.author.id != 820595582027956247) and (not ctx.permissions.administrator):
            return
        mes = await ctx.send(embed=Embed(
            title='Текущие итоги голосов',
            description=(f'{vote.name} - {len(vote.votes)}' for vote in objects.Vote.all())
        ))

        objects.Vote.set_message_id(mes.id)

        

def setup(bot):
    bot.add_cog(InteractiveEvents(bot))