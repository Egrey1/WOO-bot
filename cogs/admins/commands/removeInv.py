from ..library import command, deps, Cog, Context, Member, Embed, Colour, User, MessageInteraction, View, Button

class RemoveInvCommand(Cog):
    @staticmethod
    async def accept(interaction: MessageInteraction, member: Member | User, author: Member | User):
        if interaction.user.id != author.id:
            await interaction.response.defer(with_message=False)
            return
        member.get_inventory().clear()
        await interaction.message.edit(embed=Embed(
            title='Операция выполнена успешно!',
            description='Инвентарь пользователя ' + member.mention + ' очищен',
            colour=Colour.green()
        ), view=None)
        await interaction.response.defer(with_message=False)
    
    @command('removeinv')
    async def remove_inv(self, ctx: Context, member: Member | User | None = None):
        rights = deps.Rights()
        moderator_mode = (
            ctx.author.guild_permissions.administrator or  # type: ignore
            rights.is_administrator(ctx.author) or  
            rights.is_manage_items(ctx.author))
        if not moderator_mode:
            if member is not None:
                await ctx.send(embed=Embed(
                    title='Ошибка прав',
                    description='У вас недостаточно прав для выполнения этой команды',
                    colour=Colour.red()
                ))
            else:
                await ctx.send(embed=Embed(
                    title='Ошибка прав',
                    description='Для удаления своего инвентаря все равно нужно иметь соответсвующее право',
                    colour=Colour.red()
                ))
            return
        member = member or ctx.author
        
        view = View()
        bt = Button(label='Подтвердить', emoji='✅', custom_id='RemoveInv ' + str(member.id))
        bt.callback = lambda i: self.accept(i, member, ctx.author)
        view.add_item(bt)

        await ctx.send(embed=Embed(
            title='Подтверждение',
            description='Вы уверены, что хотите очистить инвентарь пользователя ' + member.mention + '?',
            colour=Colour.yellow()
        ), view=view)
        