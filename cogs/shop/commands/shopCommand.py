from email import message

from ..library import deps, command, Context, Embed, Cog, AllowedMentions, Colour, View, Button, MessageInteraction, Message

class ShopCommand(Cog):
    normal_shop = {}
    current_page = {}
    original_message: dict[int, Message] = {}

    @command(name='shop')
    async def shop(self, ctx: Context):
        self.all_items = deps.ShopItem.all()
        embed = Embed(title='Игровой магазин')
        self.normal_shop[ctx.author.id] = []

        total = 0
        for item in self.all_items:
            self.normal_shop[ctx.author.id] += [item]
            params = item.get_embed_field_params()
            if total < 10:
                embed.add_field(
                    name=(
                        params[0] + ' ' + str(item.cost_amount) +
                        (deps.Currency(item.cost_currency_id).symbol or '')
                    ), 
                    value=params[1],
                    inline=False
                )
            total+= 1

        if total == 0:
            embed.description = 'В магазине нет товаров'
            embed.colour = Colour.red()
            await ctx.send(embed=embed, allowed_mentions=AllowedMentions.none())
            return
        
        if total > 10:
            view = View()
            prev_page = Button(emoji='⏮️', disabled=True)
            next_page = Button(emoji='⏭️')

            prev_page.callback = lambda inter: self.prev_button_pressed1(inter, ctx.author.id)
            next_page.callback = lambda inter: self.next_button_pressed1(inter, ctx.author.id)

            view.add_item(prev_page)
            view.add_item(next_page)

            self.current_page[ctx.author.id] = 0

            self.original_message[ctx.author.id] = await ctx.send(embed=embed, view=view, allowed_mentions=AllowedMentions.none())
        else:
            await ctx.send(embed=embed, allowed_mentions=AllowedMentions.none())

    async def next_button_pressed1(self, interaction: MessageInteraction, author_id: int):
        if author_id != interaction.author.id:
            await interaction.response.send_message('Это не ваше окно взаимодействия', ephemeral=True)
            return
        await interaction.response.defer()
        
        embed = Embed(title=f'Игровой магазин')
        self.current_page[author_id] += 1
        for item in self.normal_shop[author_id][
            (self.current_page[author_id] * 10):((self.current_page[author_id] + 1) * 10)]:
            embed.add_field(
                name= item.get_embed_field_params()[0] + ' ' +
                str(item.cost_amount) + 
                (deps.Currency(item.cost_currency_id).symbol or ''),
                value=item.get_embed_field_params()[1],
                inline=False
            )
        
        view = View(timeout=None)
        prev_page = Button(emoji='⏮️')
        next_page = Button(
            emoji='⏭️', 
            disabled=(
                len(self.normal_shop[author_id]) - 
                (self.current_page[author_id] + 1) * 10) <= 0)

        prev_page.callback = lambda inter: self.prev_button_pressed1(inter, author_id)
        next_page.callback = lambda inter: self.next_button_pressed1(inter, author_id)

        view.add_item(prev_page)
        view.add_item(next_page)

        message = self.original_message.get(author_id)

        if message:
            await message.edit(embed=embed, view=view)
        else:
            await interaction.edit_original_response(embed=embed, view=view)


    async def prev_button_pressed1(self, interaction: MessageInteraction, author_id: int):
        if author_id != interaction.author.id:
            await interaction.response.send_message('Это не ваше окно взаимодействия', ephemeral=True)
            return
        await interaction.response.defer()
        
        embed = Embed(title=f'Игровой магазин')
        self.current_page[author_id] -= 1
        for item in self.normal_shop[author_id][
            (self.current_page[author_id] * 10):((self.current_page[author_id] + 1) * 10)]:
            embed.add_field(
                name= item.get_embed_field_params()[0] + ' ' +
                str(item.cost_amount) + 
                (deps.Currency(item.cost_currency_id).symbol or ''),
                value=item.get_embed_field_params()[1],
                inline=False
            )
        
        view = View(timeout=None)
        prev_page = Button(emoji='⏮️', disabled=self.current_page[author_id] == 0)
        next_page = Button(emoji='⏭️')

        prev_page.callback = lambda inter: self.prev_button_pressed1(inter, author_id)
        next_page.callback = lambda inter: self.next_button_pressed1(inter, author_id)

        view.add_item(prev_page)
        view.add_item(next_page)

        message = self.original_message.get(author_id)

        if message:
            await message.edit(embed=embed, view=view)
        else:
            await interaction.edit_original_response(embed=embed, view=view)

