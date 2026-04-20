from ..library import Cog, deps, command, Context, Message, Embed, Colour

class CreateShopItem(Cog):
    users: dict[int, dict[str, str | int | None]] = {}
    messages: dict[int, Message] = {}

    def recreate_shopitem_embed(self, userid, username, useravatarurl, error_mode: bool = False, complete_mode: bool = False) -> Embed:
        embed = Embed(
            title=(self.users[userid].get('name', 'Не указано') if not error_mode else 'Отмена создания') + ' - ' + str(self.users[userid].get('cost', '0')) + (deps.Currency(deps.MAIN_CURRENCY_ID).symbol or ''), # type: ignore
            description=self.users[userid].get('description', 'Не указано'),
            colour=Colour.red() if error_mode else None if not complete_mode else Colour.green()
        )
        if self.users[userid].get('required_role', True):
            embed.add_field('Требуемая роль', f'<&{self.users[userid].get('required_role')}>' if self.users[userid].get('required_role') else 'Не указано')
        embed.set_footer(text=username, icon_url=useravatarurl)

        return embed

    @command(name='create-item', aliases=['create_item'])
    async def create_item(self, ctx: Context, *, name: str | None = None):
        if True: # Проверка прав
            if name is not None:
                self.users[ctx.author.id]['name'] = name
            
            deps.ShopItem

            self.messages[ctx.author.id] = await ctx.send(
                embed=self.recreate_shopitem_embed(
                    ctx.author.id, 
                    ctx.author.name, 
                    ctx.author.avatar.url # type: ignore
                )
            )
            await ctx.send('Введите стоимость' if name else 'Введите название')
    
    @Cog.listener()
    async def on_message(self, message: Message):
        if message.author.id not in self.users.keys():
            return
        
        uid = message.author.id
        uname = message.author.name
        uicon = message.author.avatar.url # type: ignore
        
        if self.users[message.author.id].get('name') is None:
            if len(message.content) > 32:
                embed = Embed(
                    title='Неверные данные',
                    description='Слишком длинное название. Максимальный размер 32 символа',
                    colour= Colour.red()
                )
                await message.channel.send(embed=embed)

                await self.messages[message.author.id].edit(
                    embed= self.recreate_shopitem_embed(
                        uid,
                        uname,
                        uicon,
                        True
                    )
                )

                self.users.pop(message.author.id)
                self.messages.pop(message.author.id)
                return

            self.users[uid]['name'] = message.content
            await self.messages[message.author.id].edit(
                embed=self.recreate_shopitem_embed(
                    message.author.id,
                    message.author.name,
                    message.author.avatar.url # type: ignore
                )
            )
            await message.channel.send('Введите стоимость')

        elif self.users[message.author.id].get('cost') is None:
            if (not message.content.isdigit()) or (len(message.content) > 20):
                embed = Embed(
                    title='Неверные данные',
                    description='Вы должны были ввести число' if not len(message.content) > 20 else 'Слишком большое число!',
                    colour=Colour.red()
                )

                await message.channel.send(embed=embed)

                await self.messages[uid].edit(
                    embed= self.recreate_shopitem_embed(
                        uid, 
                        uname, 
                        uicon,
                        True
                    )
                )
                self.users.pop(uid)
                self.messages.pop(uid)
                return
            
            self.users[uid]['cost'] = message.content
            await self.messages[uid].edit(
                embed=self.recreate_shopitem_embed(
                    uid,
                    uname,
                    uicon
                )
            )
            await message.channel.send('Введите описание')
        
        elif self.users[uid].get('description') is None:
            if len(message.content) > 1000:
                embed = Embed(
                    title='Неверные данные',
                    description='Слишком длинное описание. Максимальный размер 1000 символов'
                )

                await message.channel.send(embed=embed)
                
                await self.messages[uid].edit(
                    embed= self.recreate_shopitem_embed(
                        uid,
                        uname,
                        uicon,
                        True
                    )
                )
                self.users.pop(uid)
                self.messages.pop(uid)
            
            self.users[uid]['description'] = message.content
            await self.messages[uid].edit(
                embed= self.recreate_shopitem_embed(
                    uid,
                    uname, 
                    uicon
                )
            )

            await message.channel.send('Введите роль для покупки этого предмета. skip, если требований нет')
        
        elif self.users[uid].get('required_role') is None: 
            try:
                rid = message.role_mentions[0].id if len(message.role_mentions) else int(message.content)
                role = message.guild.get_role(int(rid)) # type: ignore
            except:
                embed = Embed(
                    title= 'Неверные данные',
                    description='Нужно ввести число или упомянуть роль'
                )

                await message.channel.send(embed=embed)

                await self.messages[uid].edit(
                    embed= self.recreate_shopitem_embed(
                        uid,
                        uname,
                        uicon,
                        True
                    )
                )
                self.users.pop(uid)
                self.messages.pop(uid)
                return
            if role is None and message.content.lower != 'skip':
                embed = Embed(
                    title='Неверные данные',
                    description='Роль не найдена',
                    color= Colour.red()
                )
                await message.channel.send(embed=embed)

                await self.messages[uid].edit(
                    embed = self.recreate_shopitem_embed(
                        uid,
                        uname,
                        uicon,
                        True
                    )
                )
                self.users.pop(uid)
                self.messages.pop(uid)
                return
            
            self.users[uid]['required_role'] = rid if message.content.lower() != 'skip' else None
            await self.messages[uid].edit(
                embed=self.recreate_shopitem_embed(
                    uid,
                    uname,
                    uicon,
                    False,
                    True
                )
            )
            embed = deps.ShopItem.create(self.users[uid]['name'], self.users[uid]['description'], self.users[uid]['cost'], self.users[uid]['required_role'], deps.MAIN_CURRENCY_ID).get_embed() # type: ignore

            await message.channel.send(embed=embed)
            self.users.pop(uid)
            self.messages.pop(uid)