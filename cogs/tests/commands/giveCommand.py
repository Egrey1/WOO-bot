from ..library import Cog, deps, command, Context, Message, asyncio, Member, Embed, Colour, MessageInteraction, Button, View, CommandInteraction

class GiveCommand(Cog):
    find_items: dict[int, tuple[list[deps.ShopItem], Member, int]] = {}
    waiting_users: dict[int, tuple[int, asyncio.Task]] = {}  # user_id: (channel_id, timeout_task)
    original_messages: dict[int, Message] = {}
    creates: list[int] = []

    def _error_embed(self, title: str, description: str):
        return Embed(
            title=title,
            description=description,
            color=Colour.red()
        )
        
    async def give(self, interaction: MessageInteraction, member1: Member, member2: Member, amount: str, item: deps.ShopItem):
        amount = amount.replace(',', '')
        amount = amount.split('e')
        amount = int(amount[0]) * (10 ** ((int(amount[1]) or 0) if len(amount) >= 2 else 0))
        if interaction.user.id != member1.id:
            await interaction.response.send_message('Это не ваше интерактивное окно', ephemeral=True)
            return
        inv1 = member1.get_inventory()
        inv2 = member2.get_inventory()
        amount = (int(amount) ** 2) ** 0.5
        
        try:
            if inv1[item.id].amount < amount:
                await interaction.message.edit(embed=Embed(
                    title= 'Ошибка',
                    description='Недостаточно предметов',
                    colour= Colour.red()
                ), view=None)
                await interaction.response.defer(with_message=False)
                return
        except:
            await interaction.message.edit(embed=Embed(
                title= 'Ошибка',
                description='Недостаточно предметов',
                colour=Colour.red()
            ), view=None)
            await interaction.response.defer(with_message=False)
            return
        inv1[item.id] -= amount
        inv2[item.id] = inv2.get(item.id, 0) + amount # type: ignore
        await interaction.message.edit(embed=Embed(
            title='Операция прошла успешно',
            description='Вы передали `' + item.name + '` в количестве ' + str(amount),
            colour=Colour.green()
        ), view=None)
        await interaction.response.defer(with_message=False)
        
    async def deleter(self, interaction: MessageInteraction, member: Member):
        if interaction.user.id != member.id:
            await interaction.response.send_message('Это не ваше интерактивное окно', ephemeral=True)
            return
        await interaction.message.delete()
        
            

    @command(name='give')
    async def item_command(self, ctx: Context, member: Member, amount: int, *, name: str = ''):
        items = [item for item in deps.ShopItem.all() if name.lower() in item.name.lower()]

        if len(items) <= 1:
            if items:
                view = View()
                button = Button(label='Подтвердить', emoji='✅') # Эмодзи поставить надо
                cancel = Button(label='Отменить', emoji='❎') # Эмодзи поставить надо
                button.callback = lambda inter: self.give(inter, ctx.author, member, amount, items[0]) # type: ignore
                cancel.callback = lambda inter: self.deleter(inter, ctx.author) # type: ignore
                view.add_item(button)
                view.add_item(cancel)
                
                await ctx.send(embed=Embed(
                    title='Подтвердите передачу',
                    description='Подтвердите передачу предмета `' + items[0].name + '` в количестве ' + str(amount) 
                ), view=view)
            else:
                await ctx.send(embed=self._error_embed('Ошибка', 'Предмет не найден'))
            

        else:
            self.find_items[ctx.author.id] = (items, member, amount)
            embed = Embed(
                title="Выберите предмет",
                description='\n'.join(f'{i + 1}. {item.name}' for i, item in enumerate(items))
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
            await self.original_messages[ctx.author.id].edit(embed=embed)
            self.original_messages.pop(ctx.author.id, None)
    
    @Cog.listener()
    async def on_message(self, message: Message):
        if message.author.bot or message.author.id not in self.waiting_users:
            return
        
        channel_id, timeout_task = self.waiting_users[message.author.id]
        if message.channel.id != channel_id:
            return
        
        rights = deps.Rights()
        moderator_mode = (
                message.author.guild_permissions.administrator or  # type: ignore
                rights.is_administrator(message.author) or  
                rights.is_manage_items(message.author))
        
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
        selected_item, member, amount = items[index], self.find_items[message.author.id][1], self.find_items[message.author.id][2]
        view = View()
        button = Button(label='Подтвердить', emoji='✅') # Эмодзи поставить надо
        cancel = Button(label='Отменить', emoji='❎') # Эмодзи поставить надо
        button.callback = lambda inter: self.give(inter, message.author, member, amount, selected_item) # type: ignore
        cancel.callback = lambda inter: self.deleter(inter, message.author) # type: ignore
        view.add_item(button)
        view.add_item(cancel)
        
        await self.original_messages[message.author.id].edit(embed=Embed(
            title='Подтвердите передачу',
            description='Подтвердите передачу предмета `' + items[0].name + '` в количестве ' + str(amount)
        ), view=view)
        
        # Очищаем данные
        del self.waiting_users[message.author.id]
        self.find_items.pop(message.author.id, None)