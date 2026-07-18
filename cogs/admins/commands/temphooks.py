from ..library import Cog, deps, command, Context, Embed, Colour, View, Button, MessageInteraction, Message, tasks

class TempHooks(Cog):
    temphooks: list[int] = []

    async def get_link(self, interaction: MessageInteraction, url: str, author_id: int):
        if interaction.author.id != author_id: return await interaction.response.defer(with_message=False)
        await interaction.response.send_message(url, ephemeral=True)



    @command('temphook', aliases=['temphooks', 'времхук', 'времхуки'])
    async def temphook(self, ctx: Context):
        rights = (
            deps.Rights().is_manage_webhooks(ctx.author) or # type: ignore
            deps.Rights().is_administrator(ctx.author) or
            ctx.author.guild_permissions.administrator # type: ignore
        )
        if not rights:
            return await ctx.send(embed=Embed(
                title='Ошибка прав',
                description='Вы не имеете права пользоваться этой командой',
                colour=Colour.red()
            ))
        
        try:
            temphook = await ctx.channel.create_webhook(name=ctx.author.global_name, avatar=ctx.author.avatar, reason='Пользователь ' + str(ctx.author.name) + ' (' + str(ctx.author.id) + ') создал времхук') # type: ignore
            self.temphooks.append(temphook.id)
            try:
                embed = Embed(
                    title='Запрос на создание времхука',
                    description='Времхук был успешно создан. Получите ссылку ' + temphook.url
                )
                embed.set_footer(text='Внимание, ссылка сообщение удалится через 10 минут после отправки')
                await ctx.author.send(embed=embed, delete_after=600)
                await ctx.send(embed=Embed(
                    title='Успешно',
                    description='Ваш времхук успешно был создан. Проверьте личные сообщения с ботом'
                ))
            except:
                view = View()
                button = Button(label='Посмотреть', emoji='👆')
                button.callback = lambda inter: self.get_link(inter, temphook.url, ctx.author.id)
                view.add_item(button)
                await ctx.send(embed=Embed(
                    title='Внимание',
                    description='Произошла ошибка при попытке отправить ссылку в ЛС. Получите ее в виде эфимерного сообщения',
                    colour=Colour.yellow()
                ), view=view)
                
        except:
            return await ctx.send(embed=Embed(
                title='Ошибка',
                description='Произошла неизвестная ошибка. Скорее всего вы попытались создать времхук там, где этого сделать нельзя. Например, в форумном канале',
                color=Colour.red()
            ))

    @Cog.listener('on_message')
    async def on_webhook_sended(self, message: Message):
        webhook_id = message.webhook_id
        if webhook_id is None: return

        for hook in await message.channel.webhooks(): # type: ignore
            if hook.id == webhook_id:
                await hook.delete()
                break
        if not webhook_id in self.temphooks:
            if (message.mention_everyone) or len(message.mentions) > 25 or ('@here' in message.content):
                await message.delete()
                return await message.channel.send('Сработала антирейд система', delete_after=30)

    @tasks.loop(hours=2)
    async def cheker(self):
        for webhook in await deps.main_guild.webhooks():
            if webhook.id not in self.temphooks: await webhook.delete()
