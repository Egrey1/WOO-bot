from ..library import Context, Cog, command, asyncio

class Clear(Cog):
    @command(name='clear', aliases=['очистить'], description='Очистить чат') # type: ignore
    async def clear(self, ctx: Context, amount: int | None = None):
        target_message_id = ctx.message.reference.message_id if ctx.message.reference else None
        if amount is None and target_message_id is None:
            await ctx.send('Выберите целевое сообщение для удаления или введите общее количество удаляемых сообщений')
            return
        
        if not (ctx.author.guild_permissions.manage_messages or ctx.author.guild_permissions.administrator): # type: ignore
            await ctx.send('У вас нет прав на использование этой команды')
            return
        
        if amount:
            async for message in ctx.channel.history(limit=amount):
                try:
                    await message.delete()
                    await asyncio.sleep(0.5)
                except:
                    await ctx.send('Не удалось удалить сообщения! Была вызвана неизвестная ошибка')
                    return
            await ctx.send('Сообщения были успешно удалены! ' + f'({amount})')
            return
        if target_message_id:
            flag = False
            flag2 = False
            try:
                mes = await ctx.send('Ожидайте, команда в процессе выполнения')
                counter = 0
                async for message in ctx.channel.history(limit=250):
                    if flag2:
                        id_ = message.id
                        await message.delete()
                        counter += 1
                        if id_ == target_message_id:
                            flag = True
                            break
                        await asyncio.sleep(0.5)
                    else:
                        flag2 = True
                if flag:
                    await mes.edit('Сообщения были успешно удалены! ' + f'({amount})')
                else:
                    await mes.edit('По какой-то причине целевое сообщение не было удалено')
            except:
                if 'mes' in locals():
                    await mes.edit('Не удалось удалить сообщения! Была вызвана неизвестная ошибка')
                else:
                    await ctx.send('Не удалось удалить сообщения! Была вызвана неизвестная ошибка')
