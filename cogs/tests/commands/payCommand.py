from ..library import Cog, command, Context, Member, deps, Embed, Colour, MessageInteraction, View, Button, ButtonStyle

class PayCommand(Cog):

    async def otkat(self, interaction: MessageInteraction, member1: Member, member2: Member, amount: int):
        rights = deps.Rights()
        mod_mode = (
            interaction.author.guild_permissions.administrator or  # type: ignore
            rights.is_administrator(interaction.author) or
            rights.is_manage_rincomes(interaction.author)
        )
        if not mod_mode:
            await interaction.send(embed=Embed(
                title='Ошибка прав',
                description='У вас недостаточно прав для выполнения этой команды',
                colour=Colour.red()
                ), ephemeral=True)
            return
        
        balance1 = member1.get_balance()
        balance2 = member2.get_balance()
        if balance2[deps.MAIN_CURRENCY_ID].amount < amount: # type: ignore
            balance1[deps.MAIN_CURRENCY_ID] += balance2[deps.MAIN_CURRENCY_ID].amount # type: ignore
            balance2[deps.MAIN_CURRENCY_ID] = 0
        else:
            balance1[deps.MAIN_CURRENCY_ID] += amount 
            balance2[deps.MAIN_CURRENCY_ID] -= amount
        await interaction.send(embed=Embed(
                title='Успешно!',
                description=interaction.author.mention + ' успешно откатил перевод',
                colour=Colour.green()
                ))
        await interaction.message.edit(view=None)

    @command('pay')
    async def pay(self, ctx: Context, member: Member, amount: str):
        if member == ctx.author:
            await ctx.send(embed=Embed(
                    title='Ошибка',
                    description='Нельзя переводить самому себе',
                    colour=Colour.red()
            ))
            return
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
        
        old = balance1[deps.MAIN_CURRENCY_ID].amount
        balance1[deps.MAIN_CURRENCY_ID] -= amount # type: ignore
        balance2[deps.MAIN_CURRENCY_ID] += amount # type: ignore
        await ctx.send(embed=Embed(
            title='Успешно!',
            description='Вы успешно передали ' + deps.bamount(amount) + (deps.Currency(deps.MAIN_CURRENCY_ID).symbol or '') + ' ' + member.mention,
            colour=Colour.green()
        ))

        if amount > (int(ctx.author.get_balance()[deps.MAIN_CURRENCY_ID]) * 0.5): # type: ignore
            channel = ctx.guild.get_channel(1110119508192014402) # type: ignore
            embed = Embed(
                title='Подозрительный перевод',
                description=ctx.author.mention + ' передал ' + member.mention + ' ' + deps.bamount(amount) + (deps.Currency(deps.MAIN_CURRENCY_ID).symbol or '') + ' (' + str(int((amount * 100) / old)) + '%)', # type: ignore
                colour=Colour.yellow()
            )
            view = View()
            bt = Button(label='Откатить', style=ButtonStyle.danger)
            bt.callback = lambda i: self.otkat(i, ctx.author, member, amount) # type: ignore
            view.add_item(bt)
            await channel.send(embed=embed, view=view) # type: ignore

    @Cog.listener()
    async def on_button_click(self, interaction):
        pass