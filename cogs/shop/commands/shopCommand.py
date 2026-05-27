from ..library import deps, command, Context, Embed, Cog, AllowedMentions, Colour, View, Button, MessageInteraction, Message, Container, Section, ButtonStyle, Separator, MessageFlags, ActionRow, TextDisplay

class ShopCommand(Cog):
    normal_shop: dict[int, list] = {}
    current_page = {}
    original_message: dict[int, Message] = {}
    max_page_size = 9

    @command(name='shop')
    async def shop(self, ctx: Context, param: str = '', *, filter: str = ''):
        if param == 'tag':
            self.all_items = (item for item in deps.ShopItem.all() if any(filter.lower() in tag.lower() for tag in item.tags))
        else:
            filter = (param + ' ' + filter).strip()
            self.all_items = (item for item in deps.ShopItem.all() if (filter.lower() in item.name.lower()))
        self.normal_shop[ctx.author.id] = []

        total = 0
        page = []
        for item in self.all_items:
            params = item.get_embed_field_params()
            section = Section(
                "### " + (
                params[0] + ' — ' + deps.bamount(item.cost_amount) +
                (deps.Currency(item.cost_currency_id).symbol or '') +
                (' ❌' if not item.is_active else '')
                ) + "\n" + params[1],
                accessory=Button(label="Выбрать", style=ButtonStyle.blurple, custom_id=params[2] + ' ' + str(ctx.author.id))
            )
            self.normal_shop[ctx.author.id].append(section)
            if total < self.max_page_size:
                page += [section, Separator()]
            total+= 1

        if total == 0:
            c = Container(TextDisplay('В магазине нет товаров'), accent_colour= Colour.red())
            await ctx.send(components=[c], allowed_mentions=AllowedMentions.none(), flags=MessageFlags(is_components_v2=True))
            return
        
        if total > self.max_page_size:
            prev_page = Button(emoji='⏮️', disabled=True)
            next_page = Button(emoji='⏭️', custom_id="Shop next " + str(ctx.author.id))

            prev_page.callback = lambda inter: self.prev_button_pressed1(inter, ctx.author.id)
            next_page.callback = lambda inter: self.next_button_pressed1(inter, ctx.author.id)

            page += [ActionRow(prev_page, next_page)]
            components = [Container(*page)]

            self.current_page[ctx.author.id] = 0

            self.original_message[ctx.author.id] = await ctx.send(components=components, allowed_mentions=AllowedMentions.none(), flags=MessageFlags(is_components_v2=True))
        else:
            components = [Container(*page)]
            await ctx.send(components=components, allowed_mentions=AllowedMentions.none(), flags=MessageFlags(is_components_v2=True))

    async def next_button_pressed1(self, interaction: MessageInteraction, author_id: int):
        if author_id != interaction.author.id:
            await interaction.response.send_message('Это не ваше окно взаимодействия', ephemeral=True)
            return
        await interaction.response.defer()
        
        page = []
        self.current_page[author_id] += 1
        for item in self.normal_shop[author_id][
            (self.current_page[author_id] * self.max_page_size):((self.current_page[author_id] + 1) * self.max_page_size)]:
            page += [item, Separator()]
        
        prev_page = Button(emoji='⏮️', custom_id="Shop prev " + str(author_id), disabled= self.current_page[author_id] == 0)
        next_page = Button(
            emoji='⏭️', 
            disabled=(
                len(self.normal_shop[author_id]) - 
                (self.current_page[author_id] + 1) * self.max_page_size) <= 0, 
                custom_id="Shop next " + str(author_id))

        prev_page.callback = lambda inter: self.prev_button_pressed1(inter, author_id)
        next_page.callback = lambda inter: self.next_button_pressed1(inter, author_id)

        page += [ActionRow(prev_page, next_page)]
        components = [Container(*page)]

        message = self.original_message.get(author_id)

        if message:
            await message.edit(components=components)
        else:
            await interaction.edit_original_response(components=components)


    async def prev_button_pressed1(self, interaction: MessageInteraction, author_id: int):
        if author_id != interaction.author.id:
            await interaction.response.send_message('Это не ваше окно взаимодействия', ephemeral=True)
            return
        await interaction.response.defer()
        
        page = []
        self.current_page[author_id] -= 1
        for item in self.normal_shop[author_id][
            (self.current_page[author_id] * self.max_page_size):((self.current_page[author_id] + 1) * self.max_page_size)]:
            page += [item, Separator()]
        
        prev_page = Button(emoji='⏮️', disabled=self.current_page[author_id] == 0, custom_id="Shop prev " + str(author_id))
        next_page = Button(emoji='⏭️', custom_id="Shop next " + str(author_id))

        prev_page.callback = lambda inter: self.prev_button_pressed1(inter, author_id)
        next_page.callback = lambda inter: self.next_button_pressed1(inter, author_id)

        page += [ActionRow(prev_page, next_page)]
        components = [Container(*page)]

        message = self.original_message.get(author_id)

        if message:
            await message.edit(components=components)
        else:
            await interaction.edit_original_response(components=components)
    
    @Cog.listener()
    async def on_button_click(self, interaction: MessageInteraction):
        if not interaction.component.custom_id:
            return
        custom_id = interaction.component.custom_id
        option = custom_id.split()[1]
        params = custom_id.split()[2:] if len(custom_id.split()) >= 2 else ''

        if not custom_id.startswith('Shop'):
            return
        
        if option == "prev":
            await self.prev_button_pressed1(interaction, int(params[0]))
        elif option == "next":
            await self.next_button_pressed1(interaction, int(params[0]))
        elif option == "view":
            self.current_page[int(params[1])] -= 1
            item = deps.ShopItem(int(params[0]))
            components = item.get_v2component() + [ActionRow(Button(label="Вернуться", style=ButtonStyle.blurple, custom_id="Shop next " + params[1]))]
            await interaction.message.edit(components=components) # type: ignore
            await interaction.response.defer(with_message=False)
        
    @command(name='shop_items_count')
    async def shop_items_count(self, ctx: Context):
        await ctx.send(
            f'В магазине {len(deps.ShopItem.all())} товаров', 
            allowed_mentions=AllowedMentions.none())    

class ModShopCommand(Cog):
    normal_shop = {}
    current_page = {}
    original_message: dict[int, Message] = {}

    @command(name='shop')
    async def shop(self, ctx: Context, param: str = '', *, filter: str = ''):
        if param == 'tag':
            self.all_items = (item for item in deps.ShopItem.all() if any(filter.lower() in tag.lower() for tag in item.tags))
        else:
            filter = (param + ' ' + filter).strip()
            self.all_items = (item for item in deps.ShopItem.all() if (filter.lower() in item.name.lower()))
        embed = Embed(title='Игровой магазин')
        self.normal_shop[ctx.author.id] = []

        total = 0
        for item in self.all_items:
            self.normal_shop[ctx.author.id] += [item]
            params = item.get_embed_field_params()
            if total < 10:
                embed.add_field(
                    name=(
                        params[0] + ' — ' + deps.bamount(item.cost_amount) +
                        (deps.Currency(item.cost_currency_id).symbol or '') + 
                        (' ❌' if not item.is_active else '')
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
            view = View(timeout=None)
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
                name= item.get_embed_field_params()[0] + ' — ' +
                deps.bamount(item.cost_amount) + 
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
                name= item.get_embed_field_params()[0] + ' — ' +
                deps.bamount(item.cost_amount) + 
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
