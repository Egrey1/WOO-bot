from ..library import deps, command, Context, Embed, Cog

class BalCommand(Cog):
    @command(name='bal')  # type: ignore
    async def bal(self, ctx: Context):
        author = ctx.author
        embed = Embed(
            title=f'Баланс {author.get_balance()[deps.MAIN_CURRENCY_ID]}{deps.Currency(deps.MAIN_CURRENCY_ID).symbol}',
            description='\n'.join(f'{deps.Resource(id_).name} {value}' for id_, value in author.get_resources().items()) # type: ignore
        )
        await ctx.send(embed=embed)