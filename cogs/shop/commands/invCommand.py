from ..library import deps, command, Cog, Context, Embed, AllowedMentions, Colour, View, Button, MessageInteraction, Message, Member

class InvCommand(Cog):
    normal_inv = {}
    current_page = {}
    original_message: dict[int, Message] = {}

    @command(name='inv')
    async def inv(self, ctx: Context, member: Member | None = None): # type: ignore
        member: Member = member if member is not None else ctx.author # type: ignore
        inventory = member.get_inventory()
        embed = Embed(title=f'Инвентарь пользователя {member.name}')
        total_count = 0
        self.normal_inv[member.id] = []
        self.current_page[member.id] = 0

        for item in inventory.values():
            if item.amount > 0:
                self.normal_inv[member.id] = self.normal_inv[member.id] + [item]
                if total_count < 10:
                    shop_item = deps.ShopItem(item.shop_item_id)
                    embed.add_field(
                        name=(shop_item.get_embed_field_params()[0]) + ' | ' + deps.bamount(item.amount),
                        value=shop_item.get_embed_field_params()[1],
                        inline=False
                    )
                    total_count += 1
        
        if total_count != 0:
            if len(self.normal_inv[member.id]) <= 10:
                await ctx.send(embed=embed, allowed_mentions=AllowedMentions.none())
            else:
                view = View(timeout=None)
                prev_page = Button(emoji='⏮️', disabled=True)
                next_page = Button(emoji='⏭️')

                prev_page.callback = lambda inter: self.prev_button_pressed(inter, member.id, ctx.author.id)
                next_page.callback = lambda inter: self.next_button_pressed(inter, member.id, ctx.author.id)

                view.add_item(prev_page)
                view.add_item(next_page)

                self.current_page[member.id] = 0

                self.original_message[member.id] = await ctx.send(embed=embed, view=view, allowed_mentions=AllowedMentions.none())

        else:
            embed = Embed(
                title=f'Инвентарь пользователя {member.name}', 
                description='Пусто', 
                colour=Colour.red()
            )
            await ctx.send('У вас нет предметов в инвентаре' if ctx.author.id == member.id else 'У него нет предметов в ивентаре', allowed_mentions=AllowedMentions.none())


    async def next_button_pressed(self, interaction: MessageInteraction, author_id: int, member_id: int):
        if member_id != interaction.author.id:
            await interaction.response.send_message('Это не ваше интерактивное окно', ephemeral=True)
            return
        
        embed = Embed(title=f'Инвентарь пользователя <@{author_id}>')
        self.current_page[author_id] += 1
        for item in self.normal_inv[author_id][
            (self.current_page[author_id] * 10):((self.current_page[author_id] + 1) * 10)]:
            shop_item = deps.ShopItem(item.shop_item_id)
            embed.add_field(
                name= shop_item.get_embed_field_params()[0] + ' | ' + deps.bamount(item.amount), 
                value=shop_item.get_embed_field_params()[1],
                inline=False
            )
        
        view = View(timeout=None)
        prev_page = Button(emoji='⏮️')
        next_page = Button(
            emoji='⏭️', 
            disabled=(
                len(self.normal_inv[author_id]) - 
                (self.current_page[author_id] + 1) * 10) <= 0)

        prev_page.callback = lambda inter: self.prev_button_pressed(inter, author_id, member_id)
        next_page.callback = lambda inter: self.next_button_pressed(inter, author_id, member_id)

        view.add_item(prev_page)
        view.add_item(next_page)

        message = self.original_message.get(author_id)

        if message:
            await message.edit(embed=embed, view=view)
        else:
            await interaction.edit_original_response(embed=embed, view=view)


    async def prev_button_pressed(self, interaction: MessageInteraction, author_id: int, member_id: int):
        if member_id != interaction.author.id:
            await interaction.response.send_message('Это не ваше интерактивное окно', ephemeral=True)
            return
        
        embed = Embed(title=f'Инвентарь пользователя <@{author_id}>')
        self.current_page[author_id] -= 1
        for item in self.normal_inv[author_id][
            (self.current_page[author_id] * 10):((self.current_page[author_id] + 1) * 10)]:
            shop_item = deps.ShopItem(item.shop_item_id)
            embed.add_field(
                name= shop_item.get_embed_field_params()[0] + ' | ' + deps.bamount(item.amount),
                value=shop_item.get_embed_field_params()[1],
                inline=False
            )
        
        view = View(timeout=None)
        prev_page = Button(emoji='⏮️', disabled=self.current_page[author_id] == 0)
        next_page = Button(emoji='⏭️')

        prev_page.callback = lambda inter: self.prev_button_pressed(inter, author_id, member_id)
        next_page.callback = lambda inter: self.next_button_pressed(inter, author_id, member_id)

        view.add_item(prev_page)
        view.add_item(next_page)

        message = self.original_message.get(author_id)

        if message:
            await message.edit(embed=embed, view=view)
        else:
            await interaction.edit_original_response(embed=embed, view=view)
    

