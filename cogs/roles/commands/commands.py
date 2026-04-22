from ..library import Cog, deps, command, Context, asyncio, Role, Embed, Colour, ActionRow, Button, ButtonStyle, MessageInteraction, MessageFlags

class RolesCommands(Cog):
    
    @command('role-income', aliases=['role_income'])
    async def role_income(self, ctx: Context, role: Role | None = None):
        if role:
            roleincome = role.get_role_information()
            if not roleincome:
                if True: # Проверка прав
                    components = [
                        ActionRow(
                            Button(
                                label='Создать роль',
                                style=ButtonStyle.green,
                                custom_id='role_create_role ' + str(role.id),
                                emoji='✅'
                            )
                        )
                    ]
                    await ctx.send(components=components, flags=MessageFlags(is_components_v2=True))
                    return

            await ctx.send(components=roleincome.get_v2component(True), flags=MessageFlags(is_components_v2=True)) # type: ignore
    

    @Cog.listener()
    async def on_button_click(self, interaction: MessageInteraction):
        if not interaction.component.custom_id:
            return
        
        custom_id = interaction.component.custom_id.split()
        option = custom_id[0]

        if 'role_edit' in option:
            if '_role' in option:
                pass
            elif 'cooldown' in option:
                pass
            elif 'income' in option:
                pass
            

        if option == 'role_create_role':
            if True: # Проверка прав
                roleincome = deps.RoleIncome.create(
                    int(custom_id[1]),
                    0,
                    deps.MAIN_CURRENCY_ID,
                    0,
                    None,
                    False
                )
                components = roleincome.get_v2component(True)
                components += [
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
                            custom_id='role_delete ' + str(roleincome.id),
                            emoji='❎'
                        )
                    )
                ]
                await interaction.message.edit(components=components, flags=MessageFlags(is_components_v2=True)) # type: ignore
        
        if option == 'role_create_role_complete':
            if True:
                roleincome = deps.RoleIncome(int(custom_id[1]))
                roleincome.edit(is_active=True)
                await interaction.message.edit(components=roleincome.get_v2component(), flags=MessageFlags(is_components_v2=True)) # type: ignore
        
        if option == 'role_delete':
            if True:
                roleincome = deps.RoleIncome(int(custom_id[1]))
                # roleincome.delete()
                await interaction.message.delete()
        
            