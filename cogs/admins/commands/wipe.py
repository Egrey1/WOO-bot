import dependencies as deps
import disnake.ext.commands as commands
from disnake import ui
import disnake as ds
import asyncio

class WipeCommand(commands.Cog):
    reg = 1365405287137280082
    unreg = 1365405287128764432
    reg_pos = 0
    
    @commands.command(name='wipe')
    async def wipe(self, ctx: commands.Context):
        if ctx.author.id != 820595582027956247:
            return
        reg = await ctx.guild.fetch_role(self.reg)
        unreg = await ctx.guild.fetch_role(self.unreg)
        self.reg_pos = reg.position
        members = reg.members
        roles = []
        for role in ctx.guild.roles:
            if role.position <= self.reg_pos:
                roles.append(role)
        
        cancel = False
        async def on_bt_click(inter):
            nonlocal cancel
            cancel = True
            await inter.response.edit_message(
                content="Отмена вайпа",
                view=None
            )
        
        view = ui.View()
        bt = ui.Button(label='Отменить')
        bt.callback = on_bt_click
        view.add_item(bt)
        await ctx.send('Роли будут сняты с зарегистрированных: ' + '\n'.join([r.mention for r in roles]) + '\n Вайп начнется через 5 минут', view=view)
        await asyncio.sleep(5 * 60)
        
        if cancel:
            return
        ctx.send('идет процесс вайпа')
        for member in members:
            try:
                await member.edit(nick=None)
                await member.remove_roles(*roles, reason='Вайп')
                await member.add_roles(unreg)
            except:
                continue
        
        await ctx.send('Вайп завершился')