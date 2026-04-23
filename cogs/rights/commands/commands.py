from ..library import Cog, deps, Context, Embed, Colour, group, Role

class RightsControl(Cog):
    
    @group(name='rights')
    async def rights(self, ctx: Context): pass

    @rights.command(name='help')
    async def rights_help(self, ctx: Context):
        if (not ctx.author.guild_permissions.administrator) and not (deps.Rights().is_administrator(ctx.author)): # type: ignore
            embed = Embed(
                title='Ошибка',
                description='Вы не имеете право использовать эту команду',
                colour=Colour.red()
            )
            await ctx.send(embed=embed)
            return
        
        embed1 = Embed(
            title='Справка',
            description='Для выполнены команды нужно ввести ее опцию и указать ее атрибуты. \n```!rights add manage_items @role```'
        )
        embed1.add_field(
            'add',
            'Добавить в список прав новую роль'
        )
        embed1.add_field(
            'remove',
            'Убрать из списка прав определенную роль'
        )
        embed1.add_field(
            'list',
            'Просмотреть список всех настроенных прав'
        )

        embed2 = Embed(
            title='Справка',
            description='Названия групп прав'
        )
        embed2.add_field(
            'manage_items',
            'Позволяет управлять настройками предметов игрового магазина. Удалять, редактировать, добавлять'
        )
        embed2.add_field(
            'manage_rincomes',
            'Позволяет управлять ролями для заработка. Удалять, редактировать, добавлять'
        )
        embed2.add_field(
            'administrator',
            'Администратору предоставляются все права а так же возможность назначать другие роли на другие области'
        )
        await ctx.send(embeds=[embed1, embed2])
    
    @rights.command(name='add')
    async def rights_add(self, ctx: Context, option: str, role: Role):
        if ctx.author.guild_permissions.administrator or deps.Rights().is_administrator(ctx.author): # type: ignore
            if option == 'manage_items':
                deps.Rights().add_manage_items(role.id) 
                await ctx.send('Теперь эта роль может управлять настройками предметов игрового магазина')
            
            elif option == 'manage_rincomes':
                 deps.Rights().add_manage_rincomes(role.id)
                 await ctx.send('Теперь эта роль может настраивать роли для заработка')

            elif option == 'administrator':
                if ctx.author.guild_permissions.administrator: # type: ignore
                    deps.Rights().add_administrator(role.id)
                    await ctx.send('Теперь эта роль может управлять всеми правами бота')
                else:
                    await ctx.send('У вас нет права назначать администраторов')
        else:
            await ctx.send('У вас нет прав для выполнения этой команды')
    
    @rights.command(name='remove')
    async def rights_remove(self, ctx: Context, option: str, role: Role):

        if ctx.author.guild_permissions.administrator or deps.Rights().is_administrator(ctx.author): # type: ignore
            option = option.lower()
            if option == 'manage_items':
                deps.Rights().remove_manage_items(role.id) 
                await ctx.send('Эта роль больше не может управлять настройками предметов игрового магазина')
            
            elif option == 'manage_rincomes':
                 deps.Rights().remove_manage_rincomes(role.id)
                 await ctx.send('Эта роль больше может настраивать роли для заработка')

            elif option == 'administrator':
                if ctx.author.guild_permissions.administrator: # type: ignore
                    deps.Rights().remove_administrator(role.id)
                    await ctx.send('Эта роль больше не может управлять всеми правами бота')
                else:
                    await ctx.send('У вас нет права удалять администраторов')

            else:
                await ctx.send('Параметра с таким названием нет! Попробуйте эти: \n ```manage_items manage_rincomes administrator```')
        else:
            await ctx.send('У вас нет прав для выполнения этой команды')
    
    @rights.command(name='list')
    async def rights_list(self, ctx: Context):
        embed = Embed(
            title='Текущая настройка прав'
        )
        embed.add_field(
            'Управление предметами',
            '\n'.join([f'<@&' + str(role) + '>' for role in deps.Rights().get_manage_items()] or ['Нет ролей']) 
        )
        embed.add_field(
            'Управление ролями для заработка',
            '\n'.join([f'<@&' + str(role) + '>' for role in deps.Rights().get_manage_rincomes()] or ['Нет ролей']) 
        )
        embed.add_field(
            'Администратор',
            '\n'.join([f'<@&' + str(role) + '>' for role in deps.Rights().get_administrator()] or ['Нет ролей']) 
        )
        await ctx.send(embed=embed)
