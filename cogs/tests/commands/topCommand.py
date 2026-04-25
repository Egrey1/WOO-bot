from ..library import deps, Cog, command, Context, Embed

class TopCommand(Cog):
    @command('top')
    async def top(self, ctx: Context):
        all_balances = deps.get_all_balances()[:20]
        all_balances = [(balance.id, balance[deps.MAIN_CURRENCY_ID].amount) for balance in all_balances]
        symbol = deps.Currency(deps.MAIN_CURRENCY_ID).symbol
        await ctx.send(embed=Embed(
            title='Топ 20',
            description='\n'.join(str(i + 1) + '. <@' + str(balance[0]) + '> - ' + str(balance[1]) + (symbol or '') for i, balance in enumerate(all_balances))
        ))