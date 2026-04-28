from ..library import Cog, deps, command, Context, asyncio, Role, Embed, Colour, ActionRow, Button, ButtonStyle, MessageInteraction, MessageFlags, Modal, TextInput, ModalInteraction 

class RolesCommands(Cog):
    creates: list[int] = []
    
    class EditRolesModal(Modal):
        def __init__(
                self, 
                roleincome: deps.RoleIncome, 
                option_name: str,
                lists: list[ActionRow],
                cooldown: bool = False, 
                income: bool = False,
                add_tag: bool = False,
                remove_tag: bool = False
        ):
            self.roleincome = roleincome
            self.cooldown = cooldown
            self.income = income
            self.lists = lists
            self.add_tag = add_tag
            self.remove_tag = remove_tag

            self.option = TextInput(
                label=option_name,
                placeholder=('1s; 2m; 3h - одна секунда, две минуты, три часа' if cooldown else None),
                custom_id='role_edit',
                max_length=20 if (add_tag or remove_tag) else None
            )
            super().__init__(title=f'Редактирование {option_name}', components=[self.option])
        
        async def callback(self, interaction: ModalInteraction):
            value = interaction.text_values['role_edit']
            if self.cooldown:
                if value[-1] not in 'smh':
                    value += 'h'
                if not value[:-1].isdigit():
                    await interaction.response.send_message('Ожидалось число!', ephemeral=True)
                    return

                if value[-1] == 's':
                    self.roleincome.edit(cooldown_seconds=int(value[:-1]))
                elif value[-1] == 'm':
                    self.roleincome.edit(cooldown_seconds=int(value[:-1]) * 60)
                elif value[-1] == 'h':
                    self.roleincome.edit(cooldown_seconds=int(value[:-1]) * 3600)
            
            elif self.income:
                if (not value.isdigit()) and ((value[-1] != '%') and (not value[:-1].isdigit())):
                    await interaction.response.send_message('Ожидалось число или процент!', ephemeral=True)
                    return
                if value[-1] != '%':
                    self.roleincome.edit(currency_amount=int(value))
                    self.roleincome.remove_tag('percentageI')
                    self.roleincome.remove_tag('ignorecooldown')
                else:
                    self.roleincome.edit(currency_amount=int(value[:-1]))
                    self.roleincome.add_tag('percentageI')
                    self.roleincome.add_tag('ignorecooldown')
            
            elif self.add_tag:
                value = value.replace(';', ',')
                if value in self.roleincome.tags:
                    await interaction.response.send_message('Этот тег уже присутствует', ephemeral=True)
                    return
                self.roleincome.add_tag(value)
            
            elif self.remove_tag:
                if value not in self.roleincome.tags:
                    await interaction.response.send_message('Этого тега и так не было в заработной роли', ephemeral=True)
                    return
                self.roleincome.remove_tag(value)

            components = self.roleincome.get_v2component(True) + self.lists
            await interaction.response.defer(with_message=False)
            await interaction.message.edit( # type: ignore
                components= components,  # type: ignore
                flags=MessageFlags(is_components_v2=True)) 


    
    
    @command('role-income', aliases=['role_income', 'role', 'income'])
    async def role_income(self, ctx: Context, role: Role | int | None = None):
        rights = deps.Rights()
        moderator_mode = (
                ctx.author.guild_permissions.administrator or  # type: ignore
                rights.is_administrator(ctx.author) or  
                rights.is_manage_rincomes(ctx.author))
        
        if isinstance(role, int):
            role = ctx.guild.get_role(role) # type: ignore
            if not role:
                await ctx.send(embed=Embed(
                    title='Роль не найдена',
                    description='Убедитесь, что вы указали ID роли',
                    colour=Colour.red()
                ))
                return
        if role:
            roleincome = role.get_role_information()
            if not roleincome:
                if moderator_mode: 
                    components = [
                        ActionRow(
                            Button(
                                label='Создать роль заработка',
                                custom_id='role_create_role ' + str(role.id),
                                emoji='👆'
                            )
                        )
                    ]
                    await ctx.send(components=components, flags=MessageFlags(is_components_v2=True))
                    return
                else:
                    await ctx.send(embed=Embed(
                        title='Ошибка',
                        description='Эта роль ни к чему не привязана или у вас нет прав создавать новую роль для заработка',
                        colour=Colour.red()
                    ))

            await ctx.send(components=roleincome.get_v2component(moderator_mode), flags=MessageFlags(is_components_v2=True)) # type: ignore
    

    @Cog.listener()
    async def on_button_click(self, interaction: MessageInteraction):
        if not interaction.component.custom_id:
            return
        if  not interaction.component.custom_id.startswith('role'):
            return
        
        custom_id = interaction.component.custom_id.split()
        option = custom_id[0]
        rights = deps.Rights()
        moderator_mode = (
                interaction.user.guild_permissions.administrator or  # type: ignore
                rights.is_administrator(interaction.user) or  
                rights.is_manage_rincomes(interaction.user))

        if not moderator_mode:
            await interaction.response.send_message(embed=Embed(
                title='Ошибка прав',
                description='У вас нет прав для выполнения этой команды',
                colour=Colour.red()
            ), ephemeral=True)
            # await interaction.response.defer(with_message=False)
            return
        

        if 'role_edit' in option:
            roleincome = deps.RoleIncome(int(custom_id[1]))
            components = [
                ActionRow(
                    Button(
                        label='Завершить создание',
                        style=ButtonStyle.green,
                        custom_id='role_create_role_complete ' + str(roleincome.id),
                        emoji='✅'
                    ),
                    Button(
                        label='Отменить создание',
                        style=ButtonStyle.red,
                        custom_id='role_delete  ' + str(roleincome.id),
                        emoji='❎'
                    )
                )
            ]
            if 'cooldown' in option:
                modal = self.EditRolesModal(roleincome, 'Кулдаун', [] if not (roleincome.id in self.creates) else components, cooldown=True)
                await interaction.response.send_modal(modal)

            elif 'income' in option:
                modal = self.EditRolesModal(roleincome, 'Заработок', [] if not (roleincome.id in self.creates) else components, income=True)
                await interaction.response.send_modal(modal)
            
            elif 'add_tag' in option:
                modal = self.EditRolesModal(roleincome, 'Добавить тег', [] if not (roleincome.id in self.creates) else components, add_tag=True)
                await interaction.response.send_modal(modal)
            
            elif 'remove_tag' in option:
                modal = self.EditRolesModal(roleincome, 'Удалить тег', [] if not (roleincome.id in self.creates) else components, remove_tag=True)
                await interaction.response.send_modal(modal)
            

        if option == 'role_create_role':
            roleincome = deps.RoleIncome.create(
                int(custom_id[1]),
                1,
                deps.MAIN_CURRENCY_ID,
                0,
                None,
                False
            )
            self.creates.append(roleincome.id)
            components = roleincome.get_v2component(True)
            components.append(
                ActionRow(
                    Button(
                        label='Завершить создание',
                        style=ButtonStyle.green,
                        custom_id='role_create_role_complete ' + str(roleincome.id),
                        emoji='✅'
                    ),
                    Button(
                        label='Отменить создание',
                        style=ButtonStyle.red,
                        custom_id='role_delete  ' + str(roleincome.id),
                        emoji='❎'
                    )
                )
            )
            await interaction.message.edit(components=components, flags=MessageFlags(is_components_v2=True)) # type: ignore
        
        if option == 'role_create_role_complete':
            if True:
                roleincome = deps.RoleIncome(int(custom_id[1]))
                roleincome.edit(is_active=True)
                self.creates.remove(roleincome.id)
                await interaction.message.edit(components=roleincome.get_v2component(), flags=MessageFlags(is_components_v2=True)) # type: ignore
        
        if option == 'role_delete':
            if True:
                roleincome = deps.RoleIncome(int(custom_id[1]))
                roleincome.delete()
                await interaction.message.delete()
                await interaction.response.send_message('Роль удалена')
        
            