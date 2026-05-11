from ..library import command, Context, deps, Cog, Member, Message, Role, Embed

class GiveRole(Cog):
    give_role_searches: dict[int, tuple[deps.Search, Member]] = {}

    async def on_search_add_completed(self, message: Message, role: Role, member_id: int):
        member = self.give_role_searches.pop(member_id)[1]
        if role in member.roles:
            await message.reply('У пользователя уже есть эта роль')
            return

        await member.add_roles(role) # pyright: ignore[reportAttributeAccessIssue]
        await message.reply(f'Роль {role.mention} выдана')

    async def on_search_remove_completed(self, message: Message, role: Role, member_id: int):
        member = self.give_role_searches.pop(member_id)[1]
        if role not in member.roles:
            await message.reply('У пользователя уже нет этой роли')
            return
        
        await member.remove_roles(role) # pyright: ignore[reportAttributeAccessIssue]
        await message.reply(f'Роль {role.mention} Убрана')
    
    async def on_search_cancelled(self, message: Message, embed: Embed):
        await message.reply(embed=embed)
        self.give_role_searches.pop(message.author.id)
    
    @Cog.listener()
    async def on_message(self, message):
        for search in self.give_role_searches.values():
            await search[0].on_message_handler(message)

    @command('give_role', aliases=['massrole', 'giverole', 'give-role', 'addrole', 'add-role', 'add_role'])
    async def give_role(self, ctx: Context, member: Member | str, *, role_name: str = ''):
        if isinstance(member, str):
            role_name = (member + ' ' + role_name).strip()
            member = ctx.author # type: ignore
        if not ctx.me.guild_permissions.manage_roles: # type: ignore
            await ctx.send('У меня нет прав выдавать роли!')
            return
        
        if not (ctx.author.guild_permissions.manage_roles or ctx.author.guild_permissions.administrator or deps.Rights().is_manage_roles(ctx.author)): # type: ignore
            await ctx.send('У вас нет прав на выполнение этой команды')
            return
        
        roles = [
            role for role in ctx.guild.roles  # type: ignore
            if (role_name.lower() in role.name.lower()) and 
            (ctx.author.top_role.position > role.position) and  # type: ignore
            (ctx.me.top_role.position > role.position) # type: ignore
        ]

        if len(roles) == 0:
            await ctx.send('Роль не найдена')
            return
        
        elif len(roles) == 1:
            await member.add_roles(roles[0]) # pyright: ignore[reportAttributeAccessIssue]
            await ctx.send(f'Роль {roles[0].mention} выдана')
            return
        else:
            d = {}
            for role in roles:
                d[role.name] = role
            
            self.give_role_searches[ctx.author.id] = (deps.Search( # type: ignore
                'Выберите роль', d, 
                ctx.author.id, 
                complete_handler=deps.EventHandler(coro_event=self.on_search_add_completed),
                error_handler=deps.EventHandler(coro_event=self.on_search_cancelled)
                ), member)
            await self.give_role_searches[ctx.author.id][0].send_label(ctx)

    @command('remove_role', aliases=['removerole', 'remove-role'])
    async def remove_role(self, ctx: Context, member: Member | str, *, role_name: str = ''):
        if isinstance(member, str):
            role_name = (member + ' ' + role_name).strip()
            member = ctx.author # type: ignore
        if not ctx.me.guild_permissions.manage_roles: # type: ignore
            await ctx.send('У меня нет прав удалять роли!')
            return
        
        if not (ctx.author.guild_permissions.manage_roles or ctx.author.guild_permissions.administrator or deps.Rights().is_manage_roles(ctx.author)): # type: ignore
            await ctx.send('У вас нет прав на выполнение этой команды')
            return
        
        roles = [role for role in ctx.guild.roles if (role_name.lower() in role.name.lower()) and (ctx.author.top_role.position > role.position) and (ctx.me.top_role.position > role.position)] # type: ignore

        if len(roles) == 0:
            await ctx.send('Роль не найдена')
            return
        
        elif len(roles) == 1:
            await member.add_roles(roles[0]) # pyright: ignore[reportAttributeAccessIssue]
            await ctx.send(f'Роль {roles[0].mention} была удалена')
            return
        else:
            d = {}
            for role in roles:
                d[role.name] = role
            
            self.give_role_searches[ctx.author.id] = (deps.Search( # type: ignore
                'Выберите роль', d, 
                ctx.author.id, 
                complete_handler=deps.EventHandler(coro_event=self.on_search_add_completed),
                error_handler=deps.EventHandler(coro_event=self.on_search_cancelled)
                ), member)
            await self.give_role_searches[ctx.author.id][0].send_label(ctx)