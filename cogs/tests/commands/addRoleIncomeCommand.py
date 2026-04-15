from ..library import Context, CommandInteraction, Role, dt, command, slash_command, Param, deps, Embed

class AddRoleIncome:
    def __init__(self) -> None:
        resources = deps.Resource.all()
        self.dict = {resource.name: resource.id for resource in resources} # type: ignore Потом надо исправить в dependencies

    def add_role_income(
            self, 
            role: Role, 
            amount: int, 
            time: str, 
            currency: int | None = None, 
            resource: str | None = None):
        if not any([currency, resource]):
            raise ValueError('Неправильно указаны параметры')
        
        newtime = dt.time(
            second=int(time[:-1] if time[-1] == 's' else 0),
            minute=int(time[:-1] if time[-1] == 'm' else 0),
            hour=int(time[:-1] if time[-1] == 'h' else 0)
        )
        time = newtime.isoformat()
        role.create_role_information(
            newtime, 
            amount if not resource else None, 
            currency, 
            resource + ':' + str(amount) if resource is not None else None
        )
    

    @slash_command(name='role_income', description='Взаимодействие с ролями для заработка')
    async def role_income_slash_command(self):
        pass


    @role_income_slash_command.sub_command(name='add', description='Добавить новую роль для заработка')
    async def add_role_income_slash_command(self,
                                      interaction: CommandInteraction,
                                      role: Role = Param(name='Роль', description='Роль, которую нужно создать'),
                                      amount: int = Param(name='Сумма', description='Сколько будет приносить роль'),
                                      resource: str | None = Param(None, name='Ресурс', description='Какой ресурс будет приносить роль. Пусто, если ничего'),
                                      time: str = Param(name='Время', description='Кулдаун для коллекта')
                                      ):
        if time[-1] not in 'smh':
            time += 'h'
        
        self.add_role_income(role, amount, time, None if resource is not None else deps.MAIN_CURRENCY_ID, resource)
        await interaction.response.send_message('Роль успешно добавлена!', ephemeral=True)
    

    @add_role_income_slash_command.autocomplete('resource')
    async def add_role_income_slash_command_autocomplete(self, interaction: CommandInteraction, current: str):
        return [k for k in self.dict.keys() if current in k][:25]


    @role_income_slash_command.sub_command(name='list', description='Просмотреть роли и их ID для хаработка')
    async def list_role_income_slash_command(self, interaction: CommandInteraction):
        

    # @command('role_income') # type: ignore
    # async def add_role_income_command(self, ctx: Context, role: Role, amount: int, time: str, resource: str | None = None):
    #     if time[-1] not in 'smh':
    #         time += 'h'
    #     self.add_role_income(role, amount, time, None if resource is not None else deps.MAIN_CURRENCY_ID, resource)
    #     await ctx.send('Роль успешно добавлена!')