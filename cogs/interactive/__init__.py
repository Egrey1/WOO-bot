from disnake.ext.commands import Cog, command, Context, Bot
from disnake import Embed, ButtonStyle, MessageFlags, MessageInteraction
from disnake import ui
from . import objects

class InteractiveEvents(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @staticmethod
    def construct_container(buttons_enabled: bool = True):
        cont = []
        for vote in objects.Vote.all()[::-1]:
            cont.append(ui.Section(
                ui.TextDisplay(vote.name or ''),
                accessory=ui.Button(
                    label='Проголосовать', 
                    style=ButtonStyle.green if vote.name == 'Эрнесто' else ButtonStyle.secondary,
                    custom_id='Vote vote ' + str(vote.name),
                    disabled=not buttons_enabled
                )
            ))
            cont.append(ui.TextDisplay(vote.description))
            cont.append(ui.Separator())
        return ui.Container(
                ui.TextDisplay(f'На сервере проходит голосование за нового владельца проекта **Starlight**! Выберите себе подходящего кандидата'), ui.Separator(), ui.Separator(),
                *cont
            )
    
    @staticmethod
    def get_votes_embed():
        return Embed(
            title='Текущие итоги голосов',
            description='\n'.join([f'{vote.name} - {len(vote.votes)}' for vote in objects.Vote.all()[::-1]])
        )
    
    @command('интерактив')
    async def interactive(self, ctx: Context):
        ep = objects.EventPlayer(ctx.author.id)
        ep.tags = list(set(ep.tags + ['enabled']))
        # await ctx.send('На данный момент никаких событий нет')

        await ctx.author.send(components=[self.construct_container()], flags=MessageFlags(is_components_v2=True))
    
    @command('interactive_event')
    async def event_interactive(self, ctx: Context):
        if (ctx.author.id != 820595582027956247) and (ctx.author.id != 642766756699570196) and (not ctx.permissions.administrator):
            return
        mes = await ctx.send(embed=self.get_votes_embed())
        old_mes_id = objects.Vote.get_message_id()
        if old_mes_id is not None:
            try:
                await self.bot.get_message(old_mes_id).delete() # type: ignore
            except:
                pass
        objects.Vote.set_message_id(mes.id)
    
    @command('interactive_change')
    async def run(self, ctx: Context): 
        if (ctx.author.id != 820595582027956247) and (ctx.author.id != 642766756699570196) and (not ctx.permissions.administrator):
            return
        pos = bool(objects.Config.get('started'))
        objects.Config.set('started', int(not pos))
        await ctx.send('Интерактив ' + ('запущен!' if not pos else 'остановлен!'))
    
    @Cog.listener('on_button_click')
    async def button_handler(self, interaction: MessageInteraction):
        data = interaction.data.custom_id
        if data.split()[0] != 'Vote':
            return
        
        data_splited = data.split()
        if data_splited[1] == 'vote':
            vote = objects.Vote(data_splited[2])
            if interaction.author.id in vote.votes:
                await interaction.response.send_message('Ты уже голосовал!', ephemeral=True)
            else:
                vote.votes += [interaction.author.id]
                if vote.name != 'Другой':
                    await interaction.response.send_message('Ваш голос в пользу ' + str(vote.name) + ' был учтён!', ephemeral=True)
                else:
                    await interaction.response.send_message('Учтено', ephemeral=True)
                try:
                    old_mes = objects.Vote.get_message_id()
                    if old_mes is not None:
                        await (self.bot.get_message(old_mes)).edit(embed=self.get_votes_embed()) # type: ignore
                except:
                    pass
            await interaction.message.edit(components=[self.construct_container(False)])
            
                
def setup(bot: Bot):
    bot.add_cog(InteractiveEvents(bot))