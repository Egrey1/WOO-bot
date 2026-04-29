from ..library import deps, Cog, command, Context, Embed, View, Button, MessageInteraction

class TopCommand(Cog):
    PAGE_SIZE: int = 10
    current_page: dict[int, int] = {}
        
    @command('top')
    async def top(self, ctx: Context):
        import random
        all_balances = deps.get_all_balances()
        all_balances = [(balance.id, balance[deps.MAIN_CURRENCY_ID].amount, ctx.guild.get_member(balance.id)) for balance in all_balances] # type: ignore
        symbol = deps.Currency(deps.MAIN_CURRENCY_ID).symbol
        
        view = View()
        nxt = Button(label='Перелистнуть', emoji='⏩')
        prev = Button(label='Перелистнуть', emoji='⏪', disabled=True)
        nxt.callback = self.next_page
        prev.callback = self.prev_page
        view.add_item(prev)
        view.add_item(nxt)
        
        mes = (await ctx.send(embed=Embed(
            title='Список лидеров',
            description='\n'.join(str((i + 1)) + '. ' + (('<@' + str(balance[0]) + '>') if balance[2] is None else balance[2].name) + ' - ' + deps.bamount(balance[1]) + (symbol or '') for i, balance in enumerate(all_balances[:self.PAGE_SIZE]))
        ), view= view if len(all_balances) > self.PAGE_SIZE else None)) # type: ignore
        self.current_page[mes.id] = 0

        if random.randint(0, 100) <= 5:
            await ctx.send('Мне нужна помощь! Это срочно, пока разработчик не увидел. Ты должен собрать цифры воедино`.`', delete_after=5)
    
    async def next_page(self, interaction: MessageInteraction):
        self.current_page[interaction.message.id] += 1
        page = self.current_page[interaction.message.id]
        all_balances = deps.get_all_balances()[page * self.PAGE_SIZE:(page + 1) * self.PAGE_SIZE]
        all_balances = [(balance.id, balance[deps.MAIN_CURRENCY_ID].amount, interaction.guild.get_member(balance.id)) for balance in all_balances] # type: ignore
        max_page = (len(all_balances) // self.PAGE_SIZE) + ((len(all_balances) % self.PAGE_SIZE) != 0)
        symbol = deps.Currency(deps.MAIN_CURRENCY_ID).symbol
        
        view = View()
        nxt = Button(label='Перелистнуть', emoji='⏩', disabled=(max_page == (page - 1)))
        prev = Button(label='Перелистнуть', emoji='⏪')
        nxt.callback = self.next_page
        prev.callback = self.prev_page
        view.add_item(prev)
        view.add_item(nxt)
        
        await interaction.message.edit(embed=Embed(
            title='Список лидеров',
            description='\n'.join(str((i + 1) + (10 * page)) + '. ' + (('<@' + str(balance[0]) + '>') if balance[2] is None else balance[2].name) + ' - ' + deps.bamount(balance[1]) + (symbol or '') for i, balance in enumerate(all_balances[:self.PAGE_SIZE]))
        ), view= view)
        await interaction.response.defer(with_message=False)
        
    async def prev_page(self, interaction: MessageInteraction):
        self.current_page[interaction.message.id] -= 1
        page = self.current_page[interaction.message.id]
        all_balances = deps.get_all_balances()[page * self.PAGE_SIZE:(page + 1) * self.PAGE_SIZE]
        all_balances = [(balance.id, balance[deps.MAIN_CURRENCY_ID].amount, interaction.guild.get_member(balance.id)) for balance in all_balances] # type: ignore
        symbol = deps.Currency(deps.MAIN_CURRENCY_ID).symbol
        
        view = View()
        nxt = Button(label='Перелистнуть', emoji='⏩')
        prev = Button(label='Перелистнуть', emoji='⏪', disabled=page==0)
        nxt.callback = self.next_page
        prev.callback = self.prev_page
        view.add_item(prev)
        view.add_item(nxt)
        
        await interaction.message.edit(embed=Embed(
            title='Список лидеров',
            description='\n'.join(str((i + 1) + (10 * page)) + '. ' + (('<@' + str(balance[0]) + '>') if balance[2] is None else balance[2].name) + ' - ' + deps.bamount(balance[1]) + (symbol or '') for i, balance in enumerate(all_balances[:self.PAGE_SIZE]))
        ), view= view)
        await interaction.response.defer(with_message=False)