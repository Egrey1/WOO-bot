from ..library import Cog, deps, command, Context, Message, asyncio, ButtonStyle, MessageFlags, Embed, Colour, MessageInteraction, Modal, TextInput, ModalInteraction, ActionRow, Button, View, Role

class ItemCommands(Cog):
    find_items: dict[int, tuple[list[deps.ShopItem], bool]] = {}
    waiting_users: dict[int, tuple[int, asyncio.Task]] = {}  # user_id: (channel_id, timeout_task)
    original_messages: dict[int, Message] = {}
    creates: list[int] = []

    def _error_embed(self, title: str, description: str):
        return Embed(
            title=title,
            description=description,
            color=Colour.red()
        )

    class EditsModal(Modal):
        def __init__(
                self, 
                item: deps.ShopItem, 
                option_name: str, 
                message_to_edit: Message,
                components: list[ActionRow],
                name: bool = False, 
                desc: bool = False, 
                cost: bool = False, 
                role: bool = False
                ):
            self.item = item
            self.name = name
            self.desc = desc
            self.cost = cost
            self.role = role
            self.message = message_to_edit
            self.acti = components # type: ignore

            self.option = TextInput(
                label=option_name, 
                required=not role, 
                custom_id='option', 
                max_length=32 if name else 1024 if desc else 20,
                placeholder= 'Введите ID роли' if role else None
            )
            super().__init__(title=f'Изменение {option_name}', components=[self.option])
        
        async def callback(self, interaction: ModalInteraction):
            value = interaction.text_values.get(self.option.custom_id)

            if self.name:
                value = value.strip() # type: ignore
                if not value:
                    await interaction.response.send_message('Отмена, ожидалось название', ephemeral=True)
                    return
                self.item.edit(name=value)
            elif self.desc:
                value = value.strip()  # type: ignore
                if not value:
                    await interaction.response.send_message('Отмена, ожидалось описание', ephemeral=True)
                    return
                self.item.edit(description=value) 
            elif self.cost:
                try:
                    self.item.edit(cost=int(value)) # type: ignore
                except:
                    await interaction.response.send_message('Отмена, ожидалось число', ephemeral=True)
                    return
            elif self.role:
                try:
                    if not value:
                        self.item.edit(required_role=-1)
                    elif interaction.guild.get_role(int(value)):  # type: ignore
                        self.item.edit(required_role=int(value))  
                    else:
                        await interaction.response.send_message('Отмена, роль не найдена', ephemeral=True)
                        return
                except:
                    await interaction.response.send_message('Отмена, ожидалось число', ephemeral=True)
                    return
            
            components = self.item.get_v2component(True) + self.acti 
            await interaction.response.edit_message(
                components=components,  # type: ignore
                flags=MessageFlags(is_components_v2=True)
            )

    class BuyModal(Modal):
        def __init__(self, item: deps.ShopItem, balance: int = 0):
            self.item = item

            self.count = TextInput(
                label='Введите количество', 
                placeholder='0..'+ str((balance // item.cost_amount) if item.cost_amount else 'inf'), 
                required=True,
                custom_id='count'
            )
            super().__init__(title='Покупка предмета', components=[self.count])
        
        async def callback(self, interaction: ModalInteraction) -> None:
            count = interaction.text_values['count']

            if not count.isdigit():
                await interaction.response.send_message('Ошибка, ожидалось число', ephemeral=True)
                return
            count = (int(count) ** 2) ** 0.5
            balance = interaction.user.get_balance()[deps.MAIN_CURRENCY_ID].amount or 0

            if self.item.cost_amount and (count > (balance // (self.item.cost_amount))):
                await interaction.response.send_message('Слишком дорого', ephemeral=True)
                return
            
            interaction.user.get_balance()[deps.MAIN_CURRENCY_ID] -= count * self.item.cost_amount
            inventory = interaction.user.get_inventory()
            inventory[self.item.id] = inventory.get(self.item.id, 0) + count
            
            await interaction.response.send_message(f'Вы успешно приобрели {int(count)} {self.item.name}', ephemeral=True) 

    @command(name='item', aliases=['items'])
    async def item_command(self, ctx: Context, *, name: str = ''):
        items = [item for item in deps.ShopItem.all() if name.lower() in item.name.lower()]
        rights = deps.Rights()
        moderator_mode = (
                ctx.author.guild_permissions.administrator or  # type: ignore
                rights.is_administrator(ctx.author) or  
                rights.is_manage_items(ctx.author)
        )
        components = items[0].get_v2component(moderator_mode) if items else []

        if len(items) <= 1:
            if (not items or items[0].name != name) and moderator_mode and name: 
                components += [
                    ActionRow(
                        Button(
                            label='Создать новый предмет',
                            custom_id=f'item_create {name}',
                            emoji='👆'
                        )
                    )
                ]

            if components:
                await ctx.send(
                    components=components,  # type: ignore
                    flags=MessageFlags(is_components_v2=True)) 
            else:
                await ctx.send(embed=self._error_embed('Ошибка', 'Предмет не найден'))
            

        else:
            self.find_items[ctx.author.id] = (items, moderator_mode)
            embed = Embed(
                title="Выберите предмет",
                description='\n'.join(f'{i + 1}. {item.name}' for i, item in enumerate(self.find_items[ctx.author.id][0][:50]))
            )
            if name and moderator_mode and not any(name == role.name for role in items):
                view = View()
                but = Button(
                    label='Создать новый предмет',
                    custom_id=f'item_create {name}',
                    emoji='👆'
                )
                view.add_item(but)
                self.original_messages[ctx.author.id] = await ctx.send(embed=embed, view=view)
            else:
                self.original_messages[ctx.author.id] = await ctx.send(embed=embed)

            timeout_task = asyncio.create_task(self._timeout_handler(ctx))
            self.waiting_users[ctx.author.id] = (ctx.channel.id, timeout_task)

    @command(name='iteminfo', aliases=['item-info', 'item_info'])
    async def iteminfo_command(self, ctx: Context, *, name: str = ''):
        items = [item for item in deps.ShopItem.all() if name.lower() in item.name.lower()]
        components = items[0].get_v2component() if items else []

        if len(items) <= 1:
            if components:
                await ctx.send(
                    components=components,  # type: ignore
                    flags=MessageFlags(is_components_v2=True)) 
            else:
                await ctx.send(embed=self._error_embed('Ошибка', 'Предмет не найден'))
        else:
            self.find_items[ctx.author.id] = (items, False)
            embed = Embed(
                title="Выберите предмет",
                description='\n'.join([f'{i + 1}. {item.name}' for i, item in enumerate(self.find_items[ctx.author.id][0])][:50])
            )
            self.original_messages[ctx.author.id] = await ctx.send(embed=embed)

            timeout_task = asyncio.create_task(self._timeout_handler(ctx))
            self.waiting_users[ctx.author.id] = (ctx.channel.id, timeout_task)

    
    async def _timeout_handler(self, ctx: Context):
        await asyncio.sleep(30)
        if ctx.author.id in self.waiting_users:
            del self.waiting_users[ctx.author.id]
            self.find_items.pop(ctx.author.id, None)
            embed = Embed(
                title='Отмена',
                description='Вы не выбрали предмет в течении 30 секунд',
                color=Colour.red()
            )
            await self.original_messages[ctx.author.id].edit(embed=embed, view=None)
            self.original_messages.pop(ctx.author.id, None)
    
    @Cog.listener()
    async def on_message(self, message: Message):
        if message.author.bot or message.author.id not in self.waiting_users:
            return
        
        channel_id, timeout_task = self.waiting_users[message.author.id]
        if message.channel.id != channel_id:
            return
        
        moderator_mode = self.find_items.get(message.author.id, [[], False])[1]
        
        if not message.content.isdigit():
            embed = Embed(
                title='Неверные данные',
                description='Ожидалось число',
                color=Colour.red()
            )
            await message.channel.send(embed=embed)
            del self.waiting_users[message.author.id]
            self.find_items.pop(message.author.id, None)
            self.original_messages.pop(message.author.id, None)
            return
        
        index = int(message.content) - 1
        items = self.find_items.get(message.author.id, [[]])[0]
        if index < 0 or index >= len(items):
            embed = Embed(
                title='Неверные данные',
                description=f'Слишком большое число, ожидалось число от 1 до {len(items)}',
                color=Colour.red()
            )
            del self.waiting_users[message.author.id]
            self.find_items.pop(message.author.id, None)
            self.original_messages.pop(message.author.id, None)
            return
        
        # Отменяем таймаут
        timeout_task.cancel()
        
        # Обработка выбора
        selected_item = items[index]
        try:
            await self.original_messages[message.author.id].edit(
                components=selected_item.get_v2component(moderator_mode), # type: ignore
                flags=MessageFlags(is_components_v2=True), 
                embed=None, view=None
            )
        except:
            mes = self.original_messages[message.author.id]
            self.original_messages[message.author.id] = await mes.channel.send(
                components=selected_item.get_v2component(moderator_mode), # type: ignore
                flags=MessageFlags(is_components_v2=True)
            )
            await mes.delete()
        
        # Очищаем данные
        del self.waiting_users[message.author.id]
        self.find_items.pop(message.author.id, None)

    @Cog.listener()
    async def on_button_click(self, interaction: MessageInteraction):
        if not interaction.component.custom_id:
            return
        custom_id = interaction.component.custom_id
        option = custom_id.split()[0]
        rights = deps.Rights()

        if not custom_id.startswith('item'):
            return
        
        rights = deps.Rights()
        moderator_mode = (
                interaction.user.guild_permissions.administrator or  # type: ignore
                rights.is_administrator(interaction.user) or  
                rights.is_manage_items(interaction.user))

        if option == 'item_buy':
            item = deps.ShopItem(custom_id.split()[1])
            flag = False
            if item.required_role_id is not None:
                for role in interaction.user.roles:  # type: ignore
                    flag = flag or (role.id == item.required_role_id)
                if not flag:
                    await interaction.response.send_message('У вас нет необходимой роли!', ephemeral=True)
                    return
            modal = self.BuyModal(item, int(interaction.user.get_balance()[deps.MAIN_CURRENCY_ID].amount or 0))
            await interaction.response.send_modal(modal)

        if not moderator_mode:
            await interaction.response.send_message(embed=self._error_embed('Ошибка прав', 'У вас нет прав для выполнения этой команды'), ephemeral=True)
            # await interaction.response.defer(with_message=False)
            return

        if 'item_edit' in option:
            item = deps.ShopItem(custom_id.split()[1])
            components = [
                ActionRow(
                    Button(
                        label='Завершить создание',
                        style=ButtonStyle.green,
                        custom_id=f'item_create_complete {item.id}',
                        emoji='✅'
                    ),
                    Button(
                        label='Отменить создание',
                        style=ButtonStyle.red,
                        custom_id=f'item_delete  {item.id}',
                        emoji='❎'
                    )
                )
            ]
            if 'name' in option:
                modal = self.EditsModal(item, 'Название', interaction.message, [] if not (item.id in self.creates) else components, name=True)
                await interaction.response.send_modal(modal)

            elif 'description' in option:
                modal = self.EditsModal(item, 'Описание', interaction.message, [] if not (item.id in self.creates) else components, desc=True)
                await interaction.response.send_modal(modal)

            elif 'price' in option:
                modal = self.EditsModal(item, 'Стоимость', interaction.message, [] if not (item.id in self.creates) else components, cost=True)
                await interaction.response.send_modal(modal)

            elif 'role' in option:
                modal = self.EditsModal(item, 'Требуемая роль', interaction.message, [] if not (item.id in self.creates) else components, role=True)
                await interaction.response.send_modal(modal)
            
        
        elif option == 'item_delete':
            item = deps.ShopItem(custom_id.split()[1])
            item.delete()
            await interaction.message.delete()
            await interaction.response.send_message('Предмет удален', ephemeral=True)

        elif option == 'item_create':
            await interaction.response.defer()
            name = ' '.join(custom_id.split()[1:])
            item = deps.ShopItem.create(name, 'Описание', 0, None, deps.MAIN_CURRENCY_ID, is_active=False)
            self.creates.append(item.id)
            components = item.get_v2component(True)
            components += [
                ActionRow(
                    Button(
                        label='Завершить создание',
                        style=ButtonStyle.green,
                        custom_id=f'item_create_complete {item.id}',
                        emoji='✅'
                    ),
                    Button(
                        label='Отменить создание',
                        style=ButtonStyle.red,
                        custom_id=f'item_delete  {item.id}',
                        emoji='❎'
                    )
                )
            ]

            if interaction.message.flags.is_components_v2:
                await interaction.message.edit(
                    components=components, # type: ignore 
                    flags=MessageFlags(is_components_v2=True)
                )
            else:
                await interaction.message.delete()
                await interaction.send(
                    components=components, # type: ignore 
                    flags=MessageFlags(is_components_v2=True)
                )

        elif option == 'item_create_complete':
            item = deps.ShopItem(custom_id.split()[1])
            item.edit(is_active=True)
            self.creates.remove(item.id)
            await interaction.message.edit(
                components=item.get_v2component(), # type: ignore
                flags=MessageFlags(is_components_v2=True)
            )


    @Cog.listener()
    async def on_dropdown(self, interaction: MessageInteraction):
        custom_id = interaction.component.custom_id
        if not custom_id or not custom_id.startswith('item'):
            return
        
        if 'item_edit' in custom_id:
            if 'role' in custom_id:
                await interaction.response.defer(with_message=False)
                value: Role = interaction.resolved_values[0]  # type: ignore
                item = deps.ShopItem(custom_id.split()[1])
                item.edit(required_role=value)
                await interaction.message.edit(
                    components=item.get_v2component(True), # type: ignore
                    flags=MessageFlags(is_components_v2=True)
                )

