from ..library import Cog, command, Context, Member, deps, Embed, Colour, Message

class RemoveItem(Cog):

    searches: dict[int, tuple[deps.Search, Member, int]] = {}

    def _remove_item(self, member: Member, item: deps.ShopItem, count: int):
        inventory = member.get_inventory()
        current_count = inventory[item.id].amount if inventory.get(item.id, None) else 0
        count = min(count, current_count)
        inventory[item.id] = current_count - count

    def _error_embed(self, title: str, description: str):
        return Embed(
            title=title,
            description=description,
            color=Colour.red()
        )

    async def remove_item_command(self, message_or_ctx: Message | Context, item: deps.ShopItem, member_id: int):
        if member_id not in self.searches:
            return

        _, member, count = self.searches[member_id]
        self._remove_item(member, item, count)
        await message_or_ctx.reply(embed=Embed(
            title='Успех',
            description=f'Операция выполнена успешно! {count} \'{item.name}\' удалено.',
            colour=Colour.green()
        ))
        self.searches.pop(member_id, None)

    async def remove_item_error(self, message: Message, embed: Embed, member_id: int):
        await message.reply(embed=embed)
        self.searches.pop(member_id, None)

    @command(name='remove-item', aliases=['remove_item', 'item_remove', 'item-remove'])
    async def remove_item(self, ctx: Context, member: Member, count: str, *, name: str):
        count = count.replace(',', '')
        count = count.split('e')  # type: ignore
        count = int(count[0]) * (10 ** ((int(count[1]) or 0) if len(count) >= 2 else 0))
        rights = deps.Rights()
        moderator_mode = (
            ctx.author.guild_permissions.administrator or  # type: ignore
            rights.is_administrator(ctx.author) or  
            rights.is_manage_items(ctx.author))

        if not (ctx.author.guild_permissions.administrator or moderator_mode):  # type: ignore
            await ctx.send(embed=self._error_embed('Ошибка', 'У вас нет прав на выполнение этой команды'))
            return

        items = [item for item in deps.ShopItem.all() if name.lower() in item.name.lower()]
        count= int((count ** 2) ** 0.5) # type: ignore

        if len(items) <= 1:
            if items:
                self._remove_item(member, items[0], count) # type: ignore
                await ctx.send('Операция выполнена успешно!')
            else:
                await ctx.send(embed=self._error_embed('Ошибка', 'Предмет не найден'))
            return

        use = deps.EventHandler(coro_event=self.remove_item_command)
        error = deps.EventHandler(coro_event=self.remove_item_error)
        items_map = {item.name: item for item in items}
        self.searches[ctx.author.id] = (deps.Search('Поиск предмета', items_map, ctx.author.id, use, error), member, count) # type: ignore
        await self.searches[ctx.author.id][0].send_label(ctx)

    @Cog.listener('on_message')
    async def on_message1(self, message: Message):
        for search in self.searches.values():
            await search[0].on_message_handler(message)
