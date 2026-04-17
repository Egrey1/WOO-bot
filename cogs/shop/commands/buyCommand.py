from ..library import command, Context, Cog, deps, User, Member, Embed, Colour, AllowedMentions, Message, slash_command, CommandInteraction, Param

class BuyCommand(Cog):
    items: dict[int, list[deps.ShopItem]] = {}
    count: dict[int, int] = {}

    @command(name='buy')
    async def buy(self, ctx: Context, item_name: str, count: int = 1):
        self.items[ctx.author.id] = []

        if count < 1:
            embed = Embed(
                title='Неверные данные!',
                description='Вы ввели неверное количество покупаемых предметов!',
                colour=Colour.red()
            )
            await ctx.send(embed=embed, allowed_mentions=AllowedMentions.none())
            return

        for item in deps.ShopItem.all():
            if item_name in item.name:
                self.items[ctx.author.id] += [item]

        if len(self.items[ctx.author.id]) == 1:
            embed = self._buy_process(ctx.author, self.items[ctx.author.id][0], count)
        elif len(self.items[ctx.author.id]) == 0:
            embed = Embed(
                title='Не найдено!',
                description='Такого предмета нет в магазине!', 
                colour=Colour.red()
            )
        else:
            form_s = ''
            for i in range(len(self.items[ctx.author.id])):
                item = self.items[ctx.author.id][i]
                form_s += f'{i + 1}. {item.name} - {item.cost_amount}{deps.Currency(deps.MAIN_CURRENCY_ID).symbol}\n'
            embed = Embed(
                title='Выберите предмет!', 
                description=form_s,
                colour= Colour.greyple() 
            )
            self.count[ctx.author.id] = count
        
        await ctx.send(embed=embed, allowed_mentions=AllowedMentions.none())

    @slash_command(name='buy')
    async def buy_slash(
        self, 
        interaction: CommandInteraction, 
        item: str = Param(name='предмет', description='Название предмета'), # type: ignore
        count: int = Param(1, name='количество', description='количетво покупаемых предметов')
        ):
        try:
            item: deps.ShopItem = [item for item in deps.ShopItem.all() if item.name == item][0]
            embed = self._buy_process(interaction.user, item, count)
        except:
            embed = Embed(
                title='Неверные данные',
                description='Такого предмета нет в магазине!', 
                colour=Colour.red()
            )
        await interaction.response.send_message(embed=embed, allowed_mentions=AllowedMentions.none())
    
    @buy_slash.autocomplete('предмет')
    async def buy_slash_autocomplete(self, interaction: CommandInteraction, current: str):
        return [item.name for item in deps.ShopItem.all() if current in item.name][:25]

    def _buy_process(self, author: User | Member, item: deps.ShopItem, count: int) -> Embed:
        balance = author.get_balance()[deps.MAIN_CURRENCY_ID].amount
        price = self.items[author.id][0].cost_amount * count
        required_role_id = self.items[author.id][0].required_role_id
        if not balance or balance < price:
            return Embed(
                title='Недостаточно средств!', 
                description=f'Вам не хватает {price}{deps.Currency(deps.MAIN_CURRENCY_ID).symbol}',
                colour=Colour.red())
        
        flag = True
        for role in author.roles: # type: ignore
            if role.id == required_role_id:
                flag = False
                break
        if flag:
            return Embed(
                title='У вас нет нужной роли!',
                description=f'Для покупки вам необходима роль <&{required_role_id}>', 
                colour=Colour.red())
        
        author.get_inventory()[item.id] += count
        author.get_balance()[deps.MAIN_CURRENCY_ID] -= item.cost_amount * count
        return Embed(
            title='Успешно куплено!',
            description= f'Вы успешно купили `{item.name}` в количестве `{count}` штук за `{item.cost_amount * count}{deps.Currency(deps.MAIN_CURRENCY_ID).symbol}`',
            colour=Colour.green()) 
    
    @Cog.listener()
    async def on_message(self, message: Message):
        if not (message.author.id in self.items.keys()):
            return
    
        if message.content.isdigit():
            i = int(message.content) - 1
            if i < 0 or i >= len(self.items[message.author.id]):
                embed = Embed(
                    title='Неверные данные!',
                    description='Такого номера нет в списке!',
                    colour=Colour.red()
                )
                await message.reply(embed=embed)
                self.items[message.author.id].clear()
                return
            
            embed = self._buy_process(message.author, self.items[message.author.id][i], self.count[message.author.id])
            self.items[message.author.id].clear()
            await message.reply(embed=embed, allowed_mentions=AllowedMentions.none())
            return
        embed = Embed(
            title='Неверные данные!',
            description='Ожидалось число, но оно получено не было!',
            colour=Colour.red()
        )