from ..library import deps, command, Context, Embed, Cog

class BalCommand(Cog):
    @command(name='bal') 
    async def bal(self, ctx: Context):
        author = ctx.author
        embed = Embed(
            title=f'Баланс {author.get_balance()[deps.MAIN_CURRENCY_ID]}{deps.Currency(deps.MAIN_CURRENCY_ID).symbol}',
            description='\n'.join(f'{resource.name} {resource.amount}' for resource in author.get_resources().values()) 
        )
        await ctx.send(embed=embed)