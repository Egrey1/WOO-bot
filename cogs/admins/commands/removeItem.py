from ..library import Cog, command, Context, Member, deps, Embed, Colour, asyncio, Message

class RemoveItem(Cog):

    def _remove_item(self, member: Member, item: deps.ShopItem, count: int):
        inventory = member.get_inventory()
        current_count = inventory[item.id].amount if inventory.get(item.id, None) else 0 
        count = min(count, current_count)
        inventory[item.id] = current_count - count 

    
    find_items: dict[int, tuple[list[deps.ShopItem], Member, int]] = {}
    waiting_users: dict[int, tuple[int, asyncio.Task]] = {}  # user_id: (channel_id, timeout_task)
    original_messages: dict[int, Message] = {}

    def _error_embed(self, title: str, description: str):
        return Embed(
            title=title,
            description=description,
            color=Colour.red()
        )

    @command(name='remove-item', aliases=['remove_item', 'item_remove', 'item-remove'])
    async def remove_item(self, ctx: Context,  member: Member, count: str, *, name: str):
        count = count.replace(',', '')
        count = count.split('e') # type: ignore
        count = int(count[0]) * (10 ** ((int(count[1]) or 0) if len(count) >= 2 else 0))
        rights = deps.Rights()
        moderator_mode = (
                ctx.author.guild_permissions.administrator or  # type: ignore
                rights.is_administrator(ctx.author) or  
                rights.is_manage_items(ctx.author))

        if not (ctx.author.guild_permissions.administrator or moderator_mode): # type: ignore
            await ctx.send(embed=self._error_embed('Ошибка', 'У вас нет прав на выполнение этой команды'))

        items = [item for item in deps.ShopItem.all() if name.lower() in item.name.lower()]
        count = (((count ** 2) ** 0.5) // 1) # type: ignore

        if len(items) <= 1:
            if items:
                self._remove_item(member, items[0], count) # type: ignore
                await ctx.send('Операция выполнена успешно!')
            else:
                await ctx.send(embed=self._error_embed('Ошибка', 'Предмет не найден'))
            

        else:
            self.find_items[ctx.author.id] = (items, member, count) # type: ignore
            embed = Embed(
                title="Выберите предмет",
                description='\n'.join(f'{i + 1}. {item.name}' for i, item in enumerate(self.find_items[ctx.author.id][0]))
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
        items: list[deps.ShopItem] = self.find_items.get(message.author.id, [[]])[0] 
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
        self._remove_item(
            self.find_items[message.author.id][1], 
            selected_item, 
            self.find_items[message.author.id][2]
        ) 
        await message.channel.send('Операция выполнена успешно!')

        # Очищаем данные
        del self.waiting_users[message.author.id]
        self.find_items.pop(message.author.id, None)