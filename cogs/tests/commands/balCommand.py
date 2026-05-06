from re import S

from ..library import deps, command, Context, Cog, Member, MessageFlags, MessageInteraction, Modal, TextInput, ModalInteraction

class BalCommand(Cog):
    class EditBalance(Modal):
        def __init__(self, user: Member, name: str, withdraw: bool = False, deposit: bool = False, moderator_mode: bool = False):
            self.withdraw = withdraw
            self.deposit = deposit
            self.user = user
            self.balance = user.get_balance()[deps.MAIN_CURRENCY_ID]
            self.moneys = self.balance.amount or 0
            self.moderator_mode = moderator_mode
            a = TextInput(
                label=name, 
                custom_id='balance', 
                placeholder=(str(self.balance.amount) if deposit else str(self.balance.bank)) if not moderator_mode else 'Вы настраиваете чужой баланс', 
                value= (str(self.balance.amount) if deposit else str(self.balance.bank)) if not moderator_mode else None
            )
            super().__init__(title='Редактирование баланса', components=[a])
        
        async def callback(self, interaction: ModalInteraction):
            value = interaction.text_values['balance']
            try:
                if value != 'all':
                    value = value.replace(',', '')
                    value = int(int(value.split('e')[0]) * (10 ** int(value.split('e')[1])) if 'e' in value else int(value))
                    value = int((value ** 2) ** 0.5)
                    if self.withdraw:
                        if self.moderator_mode:
                            value = self.moneys if value < -self.moneys else value
                            self.user.get_balance()[deps.MAIN_CURRENCY_ID] += value
                        else:
                            value = min(value, self.balance.amount or 0) if value > 0 else max(value, self.balance.amount or 0)
                            self.balance += value
                            self.balance.bank = int((self.balance.bank or 0) - value )
                            self.user.get_balance()[deps.MAIN_CURRENCY_ID] = self.balance

                    elif self.deposit:
                        if self.moderator_mode:
                            self.balance.bank = (self.balance.bank or 0) + value
                            self.balance.bank = max(0, self.balance.bank)
                            self.user.get_balance()[deps.MAIN_CURRENCY_ID] = self.balance
                        else:
                            value = min(value, self.balance.amount or 0) if value > 0 else max(value, self.balance.amount or 0)
                            self.balance -= value
                            self.balance.bank = (self.balance.bank or 0) + int(value)
                            self.user.get_balance()[deps.MAIN_CURRENCY_ID] = self.balance

                else:
                    if self.withdraw:
                        if self.moderator_mode:
                            self.user.get_balance()[deps.MAIN_CURRENCY_ID] = 0
                        else:
                            value = self.balance.bank or 0
                            self.balance += value
                            self.balance.bank = 0
                            self.user.get_balance()[deps.MAIN_CURRENCY_ID] = self.balance 
                    elif self.deposit:
                        if self.moderator_mode:
                            self.balance.bank = 0
                            self.user.get_balance()[deps.MAIN_CURRENCY_ID] = self.balance
                        else:
                            value = self.balance.amount or 0
                            self.balance.bank = (self.balance.bank or 0) + value # type: ignore
                            self.balance.amount = 0
                            self.user.get_balance()[deps.MAIN_CURRENCY_ID] = self.balance

                await interaction.message.edit(components=self.user.get_v2balance(), flags=MessageFlags(is_components_v2=True)) # type: ignore
            except:
                await interaction.response.send_message('Неверное значение', ephemeral=True)
            
            await interaction.response.defer(with_message=False)



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
                await interaction.response.send_message('Это заглушка к грядущему обновлению', ephemeral=True)
            #     modal = self.EditBalance(interaction.user, 'Сумма', withdraw=True, moderator_mode=True) # type: ignore
            #     await interaction.response.send_modal(modal)
            # modal = self.EditBalance(interaction.user, 'Сумма', withdraw=True) # type: ignore
            # await interaction.response.send_modal(modal)
            await interaction.response.send_message('Это заглушка к грядущему обновлению', ephemeral=True)

        elif 'deposit' in custom_id:
            if custom_id.split()[1] != str(interaction.user.id):
                if not interaction.user.guild_permissions.administrator: # type: ignore
                    await interaction.response.send_message('Вы не имеете права управлять чужим балансом', ephemeral=True)
                    return
                await interaction.response.send_message('Это заглушка к грядущему обновлению', ephemeral=True)
            #     modal = self.EditBalance(interaction.user, 'Сумма', deposit=True, moderator_mode=True) # type: ignore
            #     await interaction.response.send_modal(modal)
            # modal = self.EditBalance(interaction.user, 'Сумма', deposit=True) # type: ignore
            # await interaction.response.send_modal(modal)
            await interaction.response.send_message('Это заглушка к грядущему обновлению', ephemeral=True)
