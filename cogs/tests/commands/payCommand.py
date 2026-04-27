from ..library import Cog, command, Context, Member, deps, Embed, Colour

class PayCommand(Cog):
    @command('pay')
    async def pay(self, ctx: Context, member: Member, amount: str):
        if amount == 'all':
            amount = str(int(ctx.author.get_balance()[deps.MAIN_CURRENCY_ID]))

        amount = amount.replace(',', '')
        amount = amount.split('e') # type: ignore
        amount = int(amount[0]) * (10 ** ((int(amount[1]) or 0) if len(amount) >= 2 else 0))
        amount = int((int(amount) ** 2) ** 0.5) # type: ignore
        balance1 = ctx.author.get_balance()
        balance2 = member.get_balance()
        
        if balance1[deps.MAIN_CURRENCY_ID].amount < amount: # type: ignore
            await ctx.send(embed=Embed(
                title='Ошибка',
                description='У вас недостаточно средств для перевода',
                colour=Colour.red()
            ))
            return
        
        balance1[deps.MAIN_CURRENCY_ID] -= amount # type: ignore
        balance2[deps.MAIN_CURRENCY_ID] += amount # type: ignore
        await ctx.send(embed=Embed(
            title='Успешно!',
            description='Вы успешно передали ' + deps.bamount(amount) + (deps.Currency(deps.MAIN_CURRENCY_ID).symbol or '') + ' ' + member.mention,
            colour=Colour.green()
        ))