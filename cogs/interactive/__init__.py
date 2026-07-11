from disnake.ext.commands import Cog, command, Context, Bot
from disnake import Embed, ButtonStyle, MessageFlags, MessageInteraction
from disnake import ui
from . import objects
import logging

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
        if not bool(objects.Config.get('started')):
            return await ctx.send('На данный момент никаких событий нет')
        ep = objects.EventPlayer(ctx.author.id)
        ep.tags = list(set(ep.tags + ['enabled']))

        if objects.Config.get('stage') == 1:
            await ctx.author.send(components=[self.construct_container()], flags=MessageFlags(is_components_v2=True))
        elif objects.Config.get('stage') == 2:
            if ep.group:
                return await ctx.author.send(components= await ep.group.get_v2_info(ep.group.leader_id == ctx.author.id), flags=MessageFlags(is_components_v2=True))
            else:
                all_groups = objects.Group.all()
                if all_groups:
                    view = ui.View()
                    options = {}
                    for group in all_groups:
                        options[group.name] = str(group.id)
                    sl = ui.StringSelect(placeholder='Выберите подпольную организацию для вступления', options=options)
                    sl.callback= self.sl_callback
                    button = ui.Button(label='Создать свою организацию', custom_id='Group create')
                    view.add_item(sl)
                    view.add_item(button)
                    await ctx.author.send(embed=Embed(
                        title='Доступные организации',
                        description='\n'.join([group.name for group in all_groups])
                    ), view=view)
                else:
                    await ctx.send(components=[
                        ui.Container(
                            ui.TextDisplay('Доступных группировок нет'), 
                            ui.ActionRow(
                                ui.Button(label='Создать свою организацию', custom_id='Group create')
                            )
                        )
                    ], flags=MessageFlags(is_components_v2=True))
                    
    async def sl_callback(self, interaction: MessageInteraction):
        data = interaction.values[0]
        author_id = interaction.author.id
        try:
            with deps.interactive as connect:
                cursor = connect.cursor()
                cursor.execute("""
                                SELECT *
                                FROM groups
                                WHERE requests LIKE ?
                """, ('%' + str(author_id) + '%', ))
                fetch = cursor.fetchone()
                if not fetch:
                    Group(int(data)).requests += [author_id]
                    await ctx.send('Ваш запрос отправлен!')
                else:
                    await ctx.send('Вы уже отправляли запрос. Дождитесь ответа от лидера группировки')
        except Exception as e:
            logging.error(e)
        
    async def create_callback(self, interaction: ModalInteraction):
        group = Group.create(interaction.text_values['group_name'])
        group.edit(leader_id=interaction.author.id)
        group.members_id += [interaction.author.id]
        await interaction.message.edit(components= await group.get_v2_info(True))
        await interaction.response.send('Успешно создано!')
    
    @command('interactive_event')
    async def event_interactive(self, ctx: Context):
        if (ctx.author.id != 820595582027956247) and (ctx.author.id != 642766756699570196):
            return
        if not bool(objects.Config.get('started')):
            return await ctx.send('Ивент еще не начался. Измените его состояние через !interactive_change')
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
        if (ctx.author.id != 820595582027956247) and (ctx.author.id != 642766756699570196):
            return
        pos = bool(objects.Config.get('started'))
        objects.Config.set('started', int(not pos))
        await ctx.send('Интерактив ' + ('запущен!' if not pos else 'остановлен!'))
    
    @command('interactive_next_stage')
    async def next_stage(self, ctx: Context):
        if (ctx.author.id != 820595582027956247) and (ctx.author.id != 642766756699570196):
            return
        current_stage = int(objects.Config.get('stage'))
        if current_stage >= 2:
            return await ctx.send('Этап изменить невозможно. Дальнешие элементы не разработаны. Текущий этап: ' + str(current_stage))
        objects.Config.set('stage', current_stage + 1)
        await ctx.send('Этап изменен. Текущий этап: ' + str(current_stage + 1))
        
    @command('interactive_prev_stage')
    async def prev_stage(self, ctx: Context):
        if (ctx.author.id != 820595582027956247) and (ctx.author.id != 642766756699570196):
            return
        current_stage = int(objects.Config.get('stage'))
        if current_stage <= 1:
            return await ctx.send('Этап изменить невозможно. Если хотите отключить интерактив используйте !interactive_change. Текущий этап: ' + str(current_stage))
        objects.Config.set('stage', current_stage - 1)
        await ctx.send('Этап изменен. Текущий этап: ' + str(current_stage - 1))
    
    @Cog.listener('on_button_click')
    async def group_handler(self, interaction: MessageInteraction):
        data = interaction.data.custom_id
        if data.split()[0] != 'Group':
            return
        
        data_splited = data.split()
        if data_splited[1] == 'create':
            modal = ui.Modal(label='Название группы')
            modal.add_item(ui.TextInput(
                label='Введите название',
                max_length=64,
                custom_id='group_name'
            ))
            await interaction.response.send_modal(modal=modal)
            
        if data_splited[1] == 'requests':
            group = objects.Group(int(data_splited[2]))
            if group.leader_id != interaction.author.id:
                return await interaction.response.send_message('Вы не являетесь владельцем этой подпольной организации', ephemeral=True)
            
    @Cog.listener('on_interaction')
    async def group_dropdowns(self, interaction: MessageInteraction):
        data = interaction.data.custom_id
        if data.split()[0] != 'Group':
            return
            
        data_splited = data.split()
        if (data_splited[1] in ('accept', 'reject')) and (data_splted[2] == 'request'):
            group = objects.Group(int(data_splited[3]))
            if group.leader_id != interaction.author.id:
                return await interaction.response.send_message('Вы не являетесь владельцем этой подпольной организации', ephemeral=True)
            member_id = int(interaction.values[0])
            group.requests = [member for member in group.requests if member != member_id]
            if data_splited[1] == 'accept':
                group.members_id += [member_id]
                member = await group.get_members(custom_members=[member_id])[0]
                await member.send(components= await group.get_v2_info())
                await member.send('Ваша заявка была принята!')
            else:
                member = await group.get_members(custom_members=[member_id])[0]
                await member.send('Ваша заявка, к сожалению, была отклонена!')
    
    @Cog.listener('on_button_click')
    async def vote_handler(self, interaction: MessageInteraction):
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