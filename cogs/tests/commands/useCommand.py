from ..library import Cog, command, Context, deps, Embed, Colour, Message

class UseCommand(Cog):
    searches: dict[int, tuple[deps.Search, int]] = {}

    async def use_command(self, message_or_ctx: Message | Context, item: deps.ShopItem, amount: int | None = None):
        amount = amount or self.searches[message_or_ctx.author.id][1]
        amount = int((amount ** 2) ** 0.5)
        inventory = message_or_ctx.author.get_inventory()
        count = inventory.get(item.id, 0)
        count = count if isinstance(count, int) else count.amount
        if count < amount:
            await message_or_ctx.reply(embed=Embed(
                title='Ошибка',
                description='У вас недостаточно предметов',
                colour=Colour.red()
            ))
            return
        
        inventory[item.id] = count - amount
        await message_or_ctx.reply(embed=Embed(
            title='Успех',
            description=f'Вы успешно использовали {amount} {item.name}',
            colour=Colour.green()
        ))
        if message_or_ctx.author.id in self.searches:
            self.searches.pop(message_or_ctx.author.id)
    
    async def use_error(self, message: Message, embed: Embed):
        await message.reply(embed=embed)
        self.searches.pop(message.author.id)



    @command('use')
    async def use(self, ctx: Context, amount: int | str, *, item_name: str = ''):
        item_name = ((amount + ' ' + item_name) if isinstance(amount, str) else item_name).strip()
        amount = amount if isinstance(amount, int) else 1
        items = [item for item in deps.ShopItem.all() if item_name.lower() in item.name.lower()][:50]

        if not items:
            await ctx.send(embed=Embed(
                title='Ошибка',
                description='Предмет не найден',
                colour=Colour.red()
            ))
            return
        elif len(items) == 1:
            await self.use_command(ctx, items[0], amount)
        
        else:
            use = deps.EventHandler(coro_event=self.use_command)
            error = deps.EventHandler(coro_event=self.use_error)
            d = {}
            for item in items:
                d[item.name] = item
            self.searches[ctx.author.id] = (deps.Search('Поиск предмета', d, ctx.author.id, use, error), amount)
            await self.searches[ctx.author.id][0].send_label(ctx)
    
    @Cog.listener('on_message')
    async def on_message2(self, message: Message):
        for search in self.searches.values():
            await search[0].on_message_handler(message)
