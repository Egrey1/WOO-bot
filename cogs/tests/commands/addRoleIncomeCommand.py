from ..library import Context, CommandInteraction, Role, dt, command, slash_command, Param, deps, Embed, Cog

class AddRoleIncome(Cog):
    dict = {}
    def _update_dict(self):
        resources = deps.Resource.all()
        self.dict = {resource.name: resource.id for resource in resources}

    def __init__(self) -> None:
        self._update_dict()

    def _add_role_income(
            self, 
            role: Role, 
            amount: int, 
            time: str, 
            currency: int | None = None, 
            resource: int | None = None):
        if not any([currency, resource]):
            raise ValueError('Неправильно указаны параметры')
        
        newtime = dt.timedelta(
            seconds=int(time[:-1] if time[-1] == 's' else 0),
            minutes=int(time[:-1] if time[-1] == 'm' else 0),
            hours=int(time[:-1] if time[-1] == 'h' else 0)
        )
        newtime = int(newtime.total_seconds())
        role.create_role_information(
            newtime, 
            amount if not resource else None, 
            currency, 
            (str(resource) + ':' + str(amount)) if resource is not None else None
        )
    

    @slash_command(name='role_income', description='Взаимодействие с ролями для заработка')
    async def role_income_slash_command(self, interaction: CommandInteraction):
        pass


    @role_income_slash_command.sub_command(name='add', description='Добавить новую роль для заработка')
    async def add_role_income_slash_command(self,
                            interaction: CommandInteraction,
                            role: Role = Param(name='роль', description='Роль, которую нужно создать'),
                            amount: int = Param(name='сумма', description='Сколько будет приносить роль'),
                            resource: str | None = Param(None, name='ресурс', description='Какой ресурс будет приносить роль. Пусто, если ничего'),
                            time: str = Param(name='время', description='Кулдаун для коллекта')
    ):
        if time[-1] not in 'smh':
            time += 'h'
        
        self._add_role_income(
            role, 
            amount, 
            time, 
            None if resource is not None else deps.MAIN_CURRENCY_ID, 
            self.dict.get(str(resource))
        )
        await interaction.response.send_message('Роль успешно добавлена!', ephemeral=True)
    

    @add_role_income_slash_command.autocomplete('ресурс')
    async def add_role_income_slash_command_autocomplete(self, interaction: CommandInteraction, current: str):
        self._update_dict()
        return [k for k in self.dict.keys() if current in k][:25]



    # @role_income_slash_command.sub_command(name='list', description='Просмотреть роли и их ID для хаработка')
    # async def list_role_income_slash_command(self, interaction: CommandInteraction):
        

    # @command('role_income') # type: ignore
    # async def add_role_income_command(self, ctx: Context, role: Role, amount: int, time: str, resource: str | None = None):
    #     if time[-1] not in 'smh':
    #         time += 'h'
    #     self.add_role_income(role, amount, time, None if resource is not None else deps.MAIN_CURRENCY_ID, resource)
    #     await ctx.send('Роль успешно добавлена!')