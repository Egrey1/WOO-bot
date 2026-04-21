from re import M

from ..library import deps, Cog, command, Context, CommandInteraction, slash_command, Embed, Param, Colour, Message

class RemoveShopItem(Cog):
    users: dict[int, list[deps.ShopItem]] = {}
    
    @command(name='remove_item', aliases=['remove-item'])
    async def remove_resource(self, ctx: Context, item_name: str = ''):
        if True:
            items = deps.ShopItem.all()
            items = [item for item in items if item_name in item.name]

            if len(items) == 0:
                await ctx.send('Не существует ресурса с таким названием!')

            elif len(items) == 1:
                # resources[0].delete():
                pass

            elif len(items) > 1:
                embed = Embed(
                    title='Выберите номер нужного ресурса',
                    description='\n'.join([f'{i + 1}. {item.name}' for i, item in enumerate(items)])
                )
                self.users[ctx.author.id] = items
                await ctx.send(embed=embed)
    
    @slash_command(name='remove_item')
    async def remove_resource_slash(self, interaction: CommandInteraction, item_name: str = Param(name='предмет', description='Название предмета, которое надо удалить')):
        if True: # Проверка прав
            flag = False
            for item in deps.ShopItem.all():
                if item_name == item.name:
                    # resource.delete()
                    flag = True
                    break
            
            if flag:
                embed = Embed(
                    title='item удалён!',
                    colour=Colour.green()
                )
                await interaction.response.send_message(embed=embed)
            else:
                embed = Embed(
                    title='item не был найден!',
                    description='Проверьте правильность написания',
                    colour=Colour.red()
                )
                await interaction.response.send_message('item не был найден!')
    
    @remove_resource_slash.autocomplete('предмет')
    async def remove_resource_slash_autocomplete(self, interaction: CommandInteraction, current: str):
        return [item.name for item in deps.ShopItem.all() if current.lower() in item.name.lower()][:25]
    
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
        
