from ..library import Cog, deps, command, Context, slash_command, Param, Message, Embed, Colour, CommandInteraction

class RemoveResource(Cog):
    users: dict[int, list[deps.Resource]]
    
    @command(name='remove_resource', aliases=['remove-resource'])
    async def remove_resource(self, ctx: Context, resource_name: str = ''):
        if True: # Проверка прав 
            resources = deps.Resource.all()
            resources = [resource for resource in resources if resource_name in resource.name]

            if len(resources) == 0:
                await ctx.send('Не существует ресурса с таким названием!')

            elif len(resources) == 1:
                # if resources[0].delete():
                pass

            elif len(resources) > 1:
                embed = Embed(
                    title='Выберите номер нужного ресурса',
                    description='\n'.join([f'{i + 1}. {resource.name}' for i, resource in enumerate(resources)])
                )
                self.users[ctx.author.id] = resources
                await ctx.send(embed=embed)
    
    @slash_command(name='remove_resource')
    async def remove_resource_slash(self, interaction: CommandInteraction, resource_name: str = Param(name='ресурс', description='Название ресурса, которое надо удалить')):
        if True: # Проверка прав 
            flag = False
            for resource in deps.Resource.all():
                if resource_name == resource.name:
                    # resource.delete()
                    flag = True
                    break
            
            if flag:
                embed = Embed(
                    title='Ресурс удалён!',
                    colour=Colour.green()
                )
                await interaction.response.send_message(embed=embed)
            else:
                embed = Embed(
                    title='Ресурс не был найден!',
                    description='Проверьте правильность написания',
                    colour=Colour.red()
                )
                await interaction.response.send_message('Ресурс не был найден!')
    
    @remove_resource_slash.autocomplete('ресурс')
    async def remove_resource_slash_autocomplete(self, interaction: CommandInteraction, current: str):
        return [resource.name for resource in deps.Resource.all() if current.lower() in resource.name.lower()][:25]
    
    @Cog.listener()
    async def on_message(self, message: Message):
        if not message.author.id in self.users.keys():
            return

        if not message.content.isdigit():
            embed = Embed(
                title='Ошибка!',
                description='Нужно ввести число!',
                colour=Colour.red()
            )
            await message.reply(embed=embed)
            self.users.pop(message.author.id)
            return
        
        if int(message.content) > len(self.users[message.author.id]):
            embed = Embed(
                title='Ошибка!',
                description=f'Нужно ввести число от 1 до {len(self.users[message.author.id])}!',
                colour=Colour.red()
            )
            await message.reply(embed=embed)
            self.users.pop(message.author.id)
            return
        
        # self.users[message.author.id][int(message.content) - 1].delete():
        embed = Embed(
            title='Успешно удалено!',
            colour=Colour.green()
        )
        await message.reply(embed=embed)
        
