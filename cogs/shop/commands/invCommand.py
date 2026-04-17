from ..library import deps, command, Cog, Context, Embed, AllowedMentions, Colour, View, Button, MessageInteraction

class InvCommand(Cog):
    normal_inv = {}
    current_page = {}

    @command(name='inv')
    async def inv(self, ctx: Context):
        inventory = ctx.author.get_inventory()
        embed = Embed(title=f'Инвентарь пользователя {ctx.author.mention}')
        total_count = 0
        self.normal_inv[ctx.author.id] = []
        self.current_page[ctx.author.id] = 0

        for item in inventory.values():
            if item.amount > 0:
                self.normal_inv[ctx.author.id] = self.normal_inv[ctx.author.id] + [item]
                if total_count != 10:
                    shop_item = deps.ShopItem(item.shop_item_id)
                    embed.add_field(
                        name=(shop_item.get_embed_field_params()[0]) + str(item.amount),
                        value=shop_item.get_embed_field_params()[1]
                    )
                    total_count += item.amount
        
        embed.set_footer(text=ctx.author.global_name, icon_url=ctx.author.avatar.url) # type: ignore
        if total_count != 0:
            if len(self.normal_inv[ctx.author.id]) <= 10:
                await ctx.send(embed=embed, allowed_mentions=AllowedMentions.none())
            else:
                view = View(timeout=None)
                next_page = Button(emoji='⏭️')
                prev_page = Button(emoji='⏮️', disabled=True)

                next_page.callback = lambda inter: self.next_button_pressed(inter, ctx.author.id)
                prev_page.callback = lambda inter: self.prev_button_pressed(inter, ctx.author.id)

                view.add_item(next_page)
                view.add_item(prev_page)

                self.current_page[ctx.author.id] = 0

                await ctx.send(embed=embed, view=view, allowed_mentions=AllowedMentions.none())

        else:
            embed = Embed(
                title=f'Инвентарь пользователя {ctx.author.mention}', 
                description='Пусто', 
                colour=Colour.red()
            )
            embed.set_footer(text=ctx.author.global_name, icon_url=ctx.author.avatar.url) # type: ignore
            await ctx.send('У вас нет предметов в инвентаре', allowed_mentions=AllowedMentions.none())


    async def next_button_pressed(self, interaction: MessageInteraction, author_id: int):
        if author_id != interaction.author.id:
            await interaction.response.send_message('Это не ваш инвентарь', ephemeral=True)
            return
        
        embed = Embed(title=f'Инвентарь пользователя {interaction.user.mention}')
        self.current_page[author_id] += 1
        for item in self.normal_inv[author_id][
            (self.current_page[author_id] * 10):((self.current_page[author_id] + 1) * 10)]:
            shop_item = deps.ShopItem(item.shop_item_id)
            embed.add_field(
                name= shop_item.get_embed_field_params()[0] + str(item.amount), 
                value=shop_item.get_embed_field_params()[1]
            )
        
        view = View(timeout=None)
        next_page = Button(
            emoji='⏭️', 
            disabled=(
                len(self.normal_inv[author_id]) - 
                (self.current_page[author_id] + 1) * 10) > 0)
        prev_page = Button(emoji='⏮️')

        next_page.callback = lambda inter: self.next_button_pressed(inter, author_id)
        prev_page.callback = lambda inter: self.prev_button_pressed(inter, author_id)

        view.add_item(next_page)
        view.add_item(prev_page)

        await interaction.edit_original_response(embed=embed, view=view)


    async def prev_button_pressed(self, interaction: MessageInteraction, author_id: int):
        if author_id != interaction.author.id:
            await interaction.response.send_message('Это не ваш инвентарь', ephemeral=True)
            return
        
        embed = Embed(title=f'Инвентарь пользователя {interaction.user.mention}')
        self.current_page[author_id] -= 1
        for item in self.normal_inv[author_id][
            (self.current_page[author_id] * 10):((self.current_page[author_id] + 1) * 10)]:
            shop_item = deps.ShopItem(item.shop_item_id)
            embed.add_field(
                name= shop_item.get_embed_field_params()[0] + str(item.amount),
                value=shop_item.get_embed_field_params()[1]
            )
        
        view = View(timeout=None)
        next_page = Button(emoji='⏭️', disabled=self.current_page[author_id] == 0)
        prev_page = Button(emoji='⏮️')

        next_page.callback = lambda inter: self.next_button_pressed(inter, author_id)
        prev_page.callback = lambda inter: self.prev_button_pressed(inter, author_id)

        view.add_item(next_page)
        view.add_item(prev_page)

        await interaction.edit_original_response(embed=embed, view=view)
    

