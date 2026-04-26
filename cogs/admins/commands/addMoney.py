from ..library import Cog, command, Context, deps, Member, Embed, Colour

class AddMoney(Cog):
    
    @command('add-money', aliases=['add_money', 'money_add', 'item-money'])
    async def add_money(self, ctx: Context, member: Member, amount: str):
        amount = amount.replace(',', '')
        amount = amount.split('e')
        amount = int(amount[0]) * (10 ** ((int(amount[1]) or 0) if len(amount) >= 2 else 0))
        rights = deps.Rights()
        moderator_mode = (
                ctx.author.guild_permissions.administrator or  # type: ignore
                rights.is_administrator(ctx.author) or  
                rights.is_manage_rincomes(ctx.author))
        if not moderator_mode:
            await ctx.send(embed= Embed(
                title='Ошибка прав',
                description='У вас недостаточно прав для выполнения этой команды',
                colour=Colour.red()
            ))
            return
        
        balance = member.get_balance()
        balance[deps.MAIN_CURRENCY_ID] += int((amount ** 2) ** 0.5) # type: ignore
        await ctx.send('Операция выполнена успешно!')
