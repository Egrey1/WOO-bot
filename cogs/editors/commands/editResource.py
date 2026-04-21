from ..library import Cog, deps, command, Context, slash_command, CommandInteraction, View, Button, ButtonStyle, Embed, Colour, MessageInteraction, Message, Param
from ..modals import EditResourceModal

class EditResource(Cog):
    users: dict[int, list[deps.Resource]] = {}
    resource_messages: list[int] = []
    
    @command('edit-resource', aliases=['edit_resource'])
    async def edit_resource(self, ctx: Context, name: str = ''):
        self.users[ctx.author.id] = [resource for resource in deps.Resource.all() if name.lower() in resource.name.lower()]
        
        if len(self.users[ctx.author.id]) == 0:
            embed = Embed(
                title='Ошибка',
                description='Такого ресурса не сущетсвует',
                color=Colour.red()
            )
            await ctx.send(embed=embed)
        
        elif len(self.users[ctx.author.id]) == 1:
            async def callback(interaction: MessageInteraction):
                if interaction.user.id == ctx.author.id:
                    modal = EditResourceModal(resource=self.users[ctx.author.id][0])
                    await interaction.response.send_modal(modal=modal)
                    return
                await interaction.response.send_message('Это не ваша интеракция', ephemeral=True)
            
            view = View()
            button = Button(label='👆', style=ButtonStyle.green)
            button.callback = callback
            view.add_item(button)

            await ctx.send(
                f'Для редактирования ресурса {self.users[ctx.author.id][0].name} нажмите на кнопку ниже',
                view=view,
            )
        
        else: 
            self.resource_messages.append(ctx.author.id)

            embed = Embed(
                title='Выберите ресурс',
                description='\n'.join(f'{i+1}. {resource.name}' for i, resource in enumerate(self.users[ctx.author.id]))
            )
            await ctx.send(embed=embed)
    
    @Cog.listener()
    async def on_message(self, message: Message):
        if not message.author.id in self.resource_messages:
            return
        
        if not message.content.isdigit():
            embed = Embed(
                title='Неверные данные',
                description='Ожидалось число',
                color=Colour.red()
            )
            await message.channel.send(embed=embed, delete_after=10)
            self.resource_messages.remove(message.author.id)
            return

        index = int(message.content)
        resources = self.users.get(message.author.id, [])
        if index < 1 or index > len(resources):
            embed = Embed(
                title='Неверные данные',
                description=f'Слишком большое число, ожидалось число от 1 до {len(resources)}',
                color=Colour.red()
            )
            await message.channel.send(embed=embed, delete_after=10)
            self.resource_messages.remove(message.author.id)
            return

        self.resource_messages.remove(message.author.id)

        async def callback(interaction: MessageInteraction):
            if interaction.user.id == message.author.id:
                modal = EditResourceModal(resource=resources[index - 1])
                await interaction.response.send_modal(modal=modal)
                return
            await interaction.response.send_message('Это не ваша интеракция', ephemeral=True)
        
        view = View()
        button = Button(label='👆', style=ButtonStyle.green)
        button.callback = callback
        view.add_item(button)

        await message.channel.send(
            f'Для редактирования ресурса {resources[index - 1].name} нажмите на кнопку ниже',
            view=view,
        )


    @slash_command(name='edit-resource')
    async def edit_resource_slash(self, interaction: CommandInteraction, resource_name: str = Param(name='ресурс', description='Название ресурса который нужно отредактировать')):
        matches = [resource for resource in deps.Resource.all() if resource_name.lower() in resource.name.lower()]
        if not matches:
            await interaction.response.send_message('Ресурс не найден', ephemeral=True)
            return

        modal = EditResourceModal(resource=matches[0])
        await interaction.response.send_modal(modal)

    @edit_resource_slash.autocomplete('ресурс')
    async def edit_resource_autocomplete(self, interaction: CommandInteraction, current: str):
        return [resource.name for resource in deps.Resource.all() if current.lower() in resource.name.lower()][:25]
    