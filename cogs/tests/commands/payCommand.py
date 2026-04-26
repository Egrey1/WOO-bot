from ..library import Cog, command, Context, Member, deps, Embed, Colour

class PayCommand(Cog):
    @command('pay')
    async def pay(self, ctx: Context, member: Member, amount: str):
        amount = amount.replace(',', '')
        amount = amount.split('e')
        amount = int(amount[0]) * (10 ** ((int(amount[1]) or 0) if len(amount) >= 2 else 0))
        amount = (int(amount) ** 2) ** 0.5
        balance1 = ctx.author.get_balance()
        balance2 = member.get_balance()
        
        if balance1[deps.MAIN_CURRENCY_ID].amount < amount: # type: ignore
            await ctx.send(embed=Embed(
                title='Ошибка',
                description='У вас недостаточно средств для перевода',
                colour=Colour.red()
            ))
            return
        
        balance1[deps.MAIN_CURRENCY_ID] -= amount
        balance2[deps.MAIN_CURRENCY_ID] += amount
        await ctx.send(embed=Embed(
            title='Успешно!',
            description='Вы успешно передали ' + deps.bamount(amount) + ' ' + member.mention,
            colour=Colour.green()
        ))