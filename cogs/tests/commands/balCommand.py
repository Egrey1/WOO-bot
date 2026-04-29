from ..library import deps, command, Context, Cog, Member, MessageFlags, MessageInteraction, Modal, TextInput, ModalInteraction

class BalCommand(Cog):
    class EditBalance(Modal):
        def __init__(self, user: Member, name: str, withdraw: bool = False, deposit: bool = False, moderator_mode: bool = False):
            self.withdraw = withdraw
            self.deposit = deposit
            self.user = user
            balance = user.get_balance()[deps.MAIN_CURRENCY_ID]
            self.moneys = balance.amount or 0
            self.bank = 0
            self.moderator_mode = moderator_mode
            a = TextInput(
                label=name, 
                custom_id='balance', 
                placeholder=(str(balance.amount) if deposit else str(self.bank)) if not moderator_mode else 'Вы настраиваете чужой баланс', 
                value= (str(balance.amount) if deposit else str(self.bank)) if not moderator_mode else None
            )
            super().__init__(title='Редактирование баланса', components=[a])
        
        async def callback(self, interaction: ModalInteraction):
            value = interaction.text_values['balance']
            try:
                if value != 'all':
                    value = value.replace(',', '')
                    value = int(value.split('e')[0]) * (10 ** int(value.split('e')[1])) if 'e' in value else int(value)
                    if self.withdraw:
                        if self.moderator_mode:
                            value = self.moneys if value < -self.moneys else value
                            self.user.get_balance()[deps.MAIN_CURRENCY_ID] += value
                    elif self.deposit:
                        pass
                else:
                    if self.withdraw:
                        if self.moderator_mode:
                            value = -self.moneys
                            self.user.get_balance()[deps.MAIN_CURRENCY_ID] += value
                    elif self.deposit:
                        pass
                await interaction.message.edit(components=self.user.get_v2balance(), flags=MessageFlags(is_components_v2=True)) # type: ignore
            except:
                await interaction.response.send_message('Неверное значение', ephemeral=True)



    @command(name='bal') 
    async def bal(self, ctx: Context, member: Member | None = None):
        author = member if member is not None else ctx.author
        components = author.get_v2balance()
        await ctx.send(components=components, flags=MessageFlags(is_components_v2=True)) # type: ignore
    
    @Cog.listener()
    async def on_button_click(self, interaction: MessageInteraction):
        custom_id = interaction.component.custom_id

        if not custom_id or not custom_id.startswith('balance'):
            return
        
        if 'withdraw' in custom_id:
            if custom_id.split()[1] != str(interaction.user.id):
                if not interaction.user.guild_permissions.administrator: # type: ignore
                    await interaction.response.send_message('Вы не имеете права управлять чужим балансом', ephemeral=True)
                    return
                modal = self.EditBalance(interaction.user, 'Сумма', withdraw=True, moderator_mode=True) # type: ignore
                await interaction.response.send_modal(modal)
            modal = self.EditBalance(interaction.user, 'Сумма', withdraw=True) # type: ignore
            await interaction.response.send_modal(modal)
            # await interaction.response.send_message('Это заглушка к грядущему обновлению', ephemeral=True)

        elif 'deposit' in custom_id:
            if custom_id.split()[1] != str(interaction.user.id):
                if not interaction.user.guild_permissions.administrator: # type: ignore
                    await interaction.response.send_message('Вы не имеете права управлять чужим балансом', ephemeral=True)
                    return
                modal = self.EditBalance(interaction.user, 'Сумма', deposit=True, moderator_mode=True) # type: ignore
                await interaction.response.send_modal(modal)
            modal = self.EditBalance(interaction.user, 'Сумма', deposit=True) # type: ignore
            await interaction.response.send_modal(modal)
