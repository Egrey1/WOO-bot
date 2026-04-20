from ..library import deps, Cog, command, Context, slash_command, CommandInteraction, Param, Embed, Message, Colour

class CreateResource(Cog):
    creater: dict[int, str] = {}
    messages: dict[int, Message] = {}

    @command('create-resource', aliases=['create_resource'])
    async def create_resource(self, ctx: Context, name: str, emoji: str | None = None, short_desc: str | None = None):
        if True: # Проверка прав
            deps.Resource.create(name=name, description=short_desc, emoji=emoji)
            await ctx.send(f'Успешно создан ресурс {name}')
        
    @slash_command(name='create-resource', aliases=['create_resource'])
    async def create_resource_slash(self, inter: CommandInteraction, name: str, emoji: str | None = None, short_desc: str | None = None):
        if True: # Проверка прав
            deps.Resource.create(name=name, description=short_desc, emoji=emoji)
            await inter.response.send_message(f'Успешно создан ресурс {name}')
    
    # @command('create-resource-long', aliases=['create_resource_long'])
    # async def create_resource_long(self, ctx: Context, name: str):
    #     if True: # Проверка прав
    #         resource = deps.Resource.create(name=name)
    #         self.creater[ctx.author.id] = f'{resource.id} emoji'
    #         embed = Embed(
    #             title=name + ' ?',
    #             description= 'Не указано'
    #         )
    #         embed.set_footer(text=ctx.author.name, icon_url=ctx.author.avatar.url)  # type: ignore
    #         self.messages[ctx.author.id] = (await ctx.send('Введите эмодзи', embed=embed))
    
    # @Cog.listener()
    # async def on_message(self, message: Message):
    #     if message.author.id in self.creater.keys():
    #         if self.creater[message.author.id].endswith('emoji'):
    #             resource = deps.Resource(self.creater[message.author.id].split(' ')[0])
    #             if message.content != 'skip':
    #                 if len(message.content) > 32:
    #                     embed = Embed(
    #                         title='Ошибка',
    #                         description='Эмодзи слишком длинное!',
    #                         color=Colour.red()
    #                     )
    #                     self.creater.pop(message.author.id)
    #                     await message.channel.send(embed=embed)
    #                     embed = Embed(
    #                         title=resource.name,
    #                         description= 'Отмена создания',
    #                         color=Colour.red()
    #                     )
    #                     resource.delete()
    #                     await self.messages[message.author.id].edit(None, embed=embed)
    #                     self.messages.pop(message.author.id)
    #                     return
                    
    #                 resource.edit(emoji=message.content)
    #             embed = Embed(
    #                 title=resource.name + ' ' + (resource.emoji or ''),
    #                 description=resource.description or 'Не указано'
    #             )
    #             self.creater[message.author.id] = f'{resource.id} desc'
    #             await self.messages[message.author.id].edit(None, embed=embed)
    #             await message.channel.send('Введите описание')
            
    #         if self.creater[message.author.id].endswith('desc'):
    #             resource = deps.Resource(self.creater[message.author.id].split(' ')[0])
    #             if message.content != 'skip':
    #                 if len(message.content) > 1024:
    #                     embed = Embed(
    #                         title='Ошибка',
    #                         description='Описание слишком длинное! Максимальный размер 1024 символа',
    #                         color=Colour.red()
    #                     )
    #                     self.creater.pop(message.author.id)
    #                     await message.channel.send(embed=embed)
    #                     embed = Embed(
    #                         title=resource.name + ' ' + (resource.emoji or ''),
    #                         description= 'Отмена создания',
    #                         color=Colour.red()
    #                     )
    #                     resource.delete()
    #                     await self.messages[message.author.id].edit(None, embed=embed)
    #                     self.messages.pop(message.author.id)
    #                     return
    #                 resource.edit(description=message.content)

    #             embed = Embed(
    #                 title=resource.name + ' ' + (resource.emoji or ''),
    #                 description=resource.description or 'Не указано',
    #                 colour=Colour.green()
    #             )
    #             self.creater.pop(message.author.id)
    #             await self.messages[message.author.id].edit(None, embed=embed)
    #             await message.channel.send('Успешно создан новый ресурс!')

            