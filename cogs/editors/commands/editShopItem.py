from ..library import Cog, deps, command, Context, slash_command, CommandInteraction, Embed, Message, Colour, MessageInteraction, View, Button, ButtonStyle, Param, Role
from ..modals import EditShopItemModal

class EditShopItem(Cog):
    users: dict[int, list[deps.ShopItem]] = {}
    resource_messages: list[int] = []

    @command('edit-item', aliases=['edit_item'])
    async def edit_shop_item(self, ctx: Context, name: str = ''):
        self.users[ctx.author.id] = [item for item in deps.ShopItem.all() if name.lower() in item.name.lower()]

        if len(self.users[ctx.author.id]) == 0:
            embed = Embed(
                title='Ошибка',
                description='Такого предмета не существует',
                color=Colour.red()
            )
            await ctx.send(embed=embed)
        elif len(self.users[ctx.author.id]) == 1:
            item = self.users[ctx.author.id][0]
            required_role = None
            if ctx.guild is not None and item.required_role_id is not None:
                required_role = ctx.guild.get_role(item.required_role_id)

            async def callback(interaction: MessageInteraction):
                if interaction.user.id == ctx.author.id:
                    modal = EditShopItemModal(resource=item, required_role=required_role)
                    await interaction.response.send_modal(modal)
                    return
                await interaction.response.send_message('Это не ваша интеракция', ephemeral=True)

            view = View()
            button = Button(label='👆', style=ButtonStyle.green)
            button.callback = callback
            view.add_item(button)

            await ctx.send(
                f'Для редактирования предмета {item.name} нажмите на кнопку ниже',
                view=view,
            )
        else:
            self.resource_messages.append(ctx.author.id)

            embed = Embed(
                title='Выберите предмет',
                description='\n'.join(f'{i}. {item.name}' for i, item in enumerate(self.users[ctx.author.id], start=1))
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
        items = self.users.get(message.author.id, [])
        if index < 1 or index > len(items):
            embed = Embed(
                title='Неверные данные',
                description=f'Слишком большое число, ожидалось число от 1 до {len(items)}',
                color=Colour.red()
            )
            await message.channel.send(embed=embed, delete_after=10)
            self.resource_messages.remove(message.author.id)
            return

        self.resource_messages.remove(message.author.id)
        item = items[index - 1]
        required_role = None
        if message.guild is not None and item.required_role_id is not None:
            required_role = message.guild.get_role(item.required_role_id)

        async def callback(interaction: MessageInteraction):
            if interaction.user.id == message.author.id:
                modal = EditShopItemModal(resource=item, required_role=required_role)
                await interaction.response.send_modal(modal)
                return
            await interaction.response.send_message('Это не ваша интеракция', ephemeral=True)

        view = View()
        button = Button(label='👆', style=ButtonStyle.green)
        button.callback = callback
        view.add_item(button)

        await message.channel.send(
            f'Для редактирования предмета {item.name} нажмите на кнопку ниже',
            view=view,
        )

    @slash_command(name='edit-item')
    async def edit_shop_item_slash(
        self,
        interaction: CommandInteraction,
        item_name: str = Param(name='предмет', description='Название предмета, которое нужно отредактировать'),
    ):
        items = [item for item in deps.ShopItem.all() if item_name.lower() in item.name.lower()]
        if not items:
            await interaction.response.send_message('Предмет не найден', ephemeral=True)
            return

        item = items[0]
        required_role = None
        if interaction.guild is not None and item.required_role_id is not None:
            required_role = interaction.guild.get_role(item.required_role_id)

        modal = EditShopItemModal(resource=item, required_role=required_role)
        await interaction.response.send_modal(modal)

    @edit_shop_item_slash.autocomplete('предмет')
    async def edit_shop_item_autocomplete(self, interaction: CommandInteraction, current: str):
        return [item.name for item in deps.ShopItem.all() if current.lower() in item.name.lower()][:25]
