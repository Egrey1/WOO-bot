from ..library import deps, command, Context, Embed, Cog, Member

class BalCommand(Cog):
    @command(name='bal') 
    async def bal(self, ctx: Context, member: Member | None = None):
        author = member if member is not None else ctx.author
        embed = Embed(
            title=f'Баланс {deps.bamount(int(author.get_balance()[deps.MAIN_CURRENCY_ID]))}{deps.Currency(deps.MAIN_CURRENCY_ID).symbol}',
            description='\n'.join(f'{resource.name} {resource.amount}' for resource in author.get_resources().values() if resource.amount) 
        )
        await ctx.send(embed=embed)