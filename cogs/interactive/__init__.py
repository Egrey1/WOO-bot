from disnake.ext.commands import Cog, command, Context, Bot
from disnake import Embed, ButtonStyle, MessageFlags, MessageInteraction, ModalInteraction
from disnake import ui
from . import objects
from .objects import modals
import logging
import dependencies as deps
import random

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
                    sl = ui.StringSelect(placeholder='Выберите организацию для вступления', options=options)
                    sl.callback = self.sl_callback
                    button = ui.Button(label='Создать свою организацию', custom_id='Group create')
                    view.add_item(sl)
                    view.add_item(button)
                    await ctx.author.send(embed=Embed(
                        title='Доступные организации',
                        description='\n'.join([group.name for group in all_groups])
                    ), view=view)
                else:
                    await ctx.author.send(components=[
                        ui.Container(
                            ui.TextDisplay('Доступных группировок нет'), 
                            ui.ActionRow(
                                ui.Button(label='Создать свою организацию', custom_id='Group create')
                            )
                        )
                    ], flags=MessageFlags(is_components_v2=True))
                    
    async def sl_callback(self, interaction: MessageInteraction):
        data = interaction.values[0] if interaction.values else ''
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
                    group = objects.Group(int(data))
                    group.requests += [author_id]
                    leader = (await group.get_members(custom_members=[group.leader_id or 0]))[0]
                    await interaction.response.send_message('Ваш запрос отправлен!', ephemeral=True)
                    await leader.send(components=[
                        ui.Container(
                            ui.Section(
                                ui.TextDisplay('У вас появился новый запрос на вступление в вашу подпольную организацию!'),
                                accessory=ui.Button(label='Посмотреть запросы', custom_id='Group requests ' + str(group.id))
                            )
                        )
                    ])
                else:
                    await interaction.response.send_message('Вы уже отправляли запрос. Дождитесь ответа от лидера группировки', ephemeral=True)
        except Exception as e:
            logging.error(e)
    
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
        current_stage = int(objects.Config.get('stage') or 0)
        if current_stage >= 2:
            return await ctx.send('Этап изменить невозможно. Дальнешие элементы не разработаны. Текущий этап: ' + str(current_stage))
        objects.Config.set('stage', current_stage + 1)
        await ctx.send('Этап изменен. Текущий этап: ' + str(current_stage + 1))
        
    @command('interactive_prev_stage')
    async def prev_stage(self, ctx: Context):
        if (ctx.author.id != 820595582027956247) and (ctx.author.id != 642766756699570196):
            return
        current_stage = int(objects.Config.get('stage') or 0)
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
            modal = modals.CreateGroupModal()
            await interaction.response.send_modal(modal=modal)
            
        elif data_splited[1] == 'requests':
            group = objects.Group(int(data_splited[2]))
            if group.leader_id != interaction.author.id:
                return await interaction.response.send_message('Вы не являетесь владельцем этой подпольной организации', ephemeral=True)
            await interaction.message.edit(components= await group.get_requests_menu())
            await interaction.response.defer(with_message=False)
        
        elif data_splited[1] == 'view':
            group = objects.Group(int(data_splited[2]))
            await interaction.message.edit(components=await group.get_v2_info(group.leader_id == interaction.author.id))
            await interaction.response.defer(with_message=False)
        
        elif data_splited[1] == 'edit':
            if data_splited[2] == 'name':
                modal = modals.EditGroup(objects.Group(int(data_splited[3])))
                await interaction.response.send_modal(modal)
        
        elif data_splited[1] == 'ask':
            if data_splited[2] == 'delete':
                group = objects.Group(int(data_splited[3]))
                await interaction.message.edit(components= await group.get_v2_info(True, False)) 
                await interaction.response.defer(with_message=False)
        
        elif data_splited[1] == 'delete':
            objects.Group(int(data_splited[2])).delete()
            try:
                await interaction.message.delete()
            except:
                pass
            await interaction.response.send_message('Успешно удалено', ephemeral=True)
            
            
    @Cog.listener('on_interaction')
    async def group_dropdowns(self, interaction: MessageInteraction):
        data = interaction.data.custom_id
        if data.split()[0] != 'Group':
            return
            
        data_splited = data.split()
        if (data_splited[1] in ('accept', 'reject')) and (data_splited[2] == 'request'):
            group = objects.Group(int(data_splited[3]))
            if group.leader_id != interaction.author.id:
                return await interaction.response.send_message('Вы не являетесь владельцем этой подпольной организации', ephemeral=True)
            member_id = int((interaction.values or [''])[0])
            group.requests = [member for member in group.requests if member != member_id]
            if data_splited[1] == 'accept':
                group.members_id += [member_id]
                member = (await group.get_members(custom_members=[member_id]))[0]
                await member.send(components= await group.get_v2_info(), flags=MessageFlags(is_components_v2=True))
                await member.send('Ваша заявка была принята!')
            else:
                member = (await group.get_members(custom_members=[member_id]))[0]
                await member.send('Ваша заявка, к сожалению, была отклонена!')
            await interaction.message.edit(components= (await group.get_requests_menu()))
            await interaction.response.defer(with_message=False)
    
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

    @Cog.listener('on_button_click')
    async def tasks_handler(self, interaction: MessageInteraction):
        data = interaction.data.custom_id
        if data.split()[0] != 'Task':
            return
        data_splited = data.split()

        if data_splited[1] == 'view':
            task = objects.Task(int(data_splited[2]))
            if len(data_splited) == 4:
                task.group = objects.Group(int(data_splited[3]))
            await interaction.message.edit(
                components=task.get_v2_info(
                        (task.group is not None) and 
                        (task.group.leader_id == interaction.author.id)
                    ) + ([ui.ActionRow(
                        ui.Button(label='Вернуться', custom_id='Group view ' + str(task.group.id))
                    )] if task.group else [])
                )
            await interaction.response.defer(with_message=False)
        
        elif data_splited[1] == 'choice':
            group = objects.Group(int(data_splited[2]))
            if group.leader_id != interaction.user.id:
                return await interaction.response.send_message('Вы не являетесь владельцем этой подпольной организации', ephemeral=True)
            await interaction.response.defer(with_message=False)
            if not any([tag.split()[0] == 'tasks_randoms' for tag in group.tags]):
                current_level = group.level + 1
                tasks = [t for t in objects.Task.all(current_level) if str(t.id) not in group.completed_tasks]
                while (len(tasks) == 0) and (current_level != 1):
                    current_level -= 1
                    tasks = [t for t in objects.Task.all(current_level) if (str(t.id) not in group.completed_tasks)]
                if len(tasks) == 1:
                    group.task = tasks[0]
                    return await interaction.message.edit(components= await group.get_v2_info())
                if len(tasks) == 0:
                    return await interaction.response.send_message('Вы выполнили все доступные задания! Ожидайте новых', ephemeral=True)
                t1 = random.choice(tasks).id
                tasks = [t for t in tasks if t.id != t1]
                t2 = random.choice(tasks).id
                group.tags += ['tasks_randoms ' + str(t1) + ' ' + str(t2)]
            for tag in group.tags:
                if tag.split()[0] == 'tasks_randoms':
                    t1, t2 = objects.Task(int(tag.split()[1])), objects.Task(int(tag.split()[2]))
                    return await interaction.message.edit(
                        components= [ 
                            ui.Container(
                                ui.TextDisplay('## Выберите задание'),
                                ui.Section(
                                    ui.TextDisplay('### ' + t1.name),
                                    accessory=ui.Button(label='Выбрать', custom_id='Task choiced ' + str(t1.id) + ' ' + str(group.id))
                                ),
                                ui.TextDisplay(t1.description or 'Описание отсутствует'),
                                ui.Separator(),
                                ui.Separator(),
                                ui.TextDisplay('# ИЛИ'),
                                ui.Separator(),
                                ui.Separator(),
                                ui.Section(
                                    ui.TextDisplay('### ' + t2.name),
                                    accessory=ui.Button(label='Выбрать', custom_id='Task choiced ' + str(t2.id) + ' ' + str(group.id))
                                ),
                                ui.TextDisplay(t2.description or 'Описание отсутствует'),
                            )
                        ]
                    )
            
        
        elif data_splited[1] == 'choiced':
            task, group = objects.Task(int(data_splited[2])), objects.Group(int(data_splited[3]))
            group.task = task
            group.tags = [tag for tag in group.tags if not tag.startswith('tasks_randoms')]
            await interaction.response.defer(with_message=False)
            await interaction.message.edit(components= await group.get_v2_info())
        
        elif data_splited[1] == 'complete':
            group = objects.Group(int(data_splited[2]))
            if not group.task: return
            await deps.egrey.send(components=(
                await group.get_v2_info() + group.task.get_v2_info() + [
                    ui.ActionRow(
                        ui.Button(
                            label='Принять выполнение', 
                            custom_id='Task realcomplete ' + str(group.id), 
                            emoji='✅', 
                            style=ButtonStyle.green
                        ),
                        ui.Button(
                            label='Отказать выполнение', 
                            custom_id='Task reject ' + str(group.id), 
                            emoji='❎', 
                            style=ButtonStyle.red
                        )
                    )
                ]
            ))
            await interaction.response.send_message('Выполнение вашего задания было отправлено на проверку модерации. Ожидайте ответа!', ephemeral=True)
        
        elif data_splited[1] == 'realcomplete':
            group = objects.Group(int(data_splited[2]))
            member = (await group.get_members(custom_members=[group.leader_id or 0]))[0]
            if not group.task: return
            if group.level < (group.task.level):
                group.completed_tasks += [str(group.task.id)]
                group.task = None
                group.level += 1
                await interaction.message.delete()
                if group.level == 1:
                    view = ui.View()
                    button = ui.Button(label='Как я могу это сделать?', custom_id='Ask ability 1')
                    view.add_item(button)
                    await member.send('Поздравляю! Ваша группа улучшилась. Теперь вы можете откатывать откаты Эрнесто', view=view)
                    await interaction.response.send_message('Отправлено!', ephemeral=True)
                else:
                    await interaction.response.send_message('Для этого уровня ответное сообщение не было прописано. Ответ не отправлен', ephemeral=True)
            else:
                group.completed_tasks += [str(group.task.id)]
                group.task = None
                group.upgrade_points += 1
                if group.level < 99:
                    random_answers = (
                        'Отлично! Вы молодцы. Выполнение задания, на самом деле, не требовалось, но вы смогли подорвать влияние Эрнесто. Не думайте, что это останется без награды',
                        'Очень хорошо, я доволен вами. Еще чуть-чуть и мы выведем его из себя, ха-ха! Ваша организация еще недостаточно развита, так что награда вы выполнение побочных заданий придет чуть позже',
                        'Вы и ваша команда хорошо работает. Влияние Эрнесто с каждым днем подрывается все больше и больше, мы победим. Не думайте, что выполнение побочных заданий вам ничего не даст. Вы еще недостаточно развили свою организацию чтобы ими воспользоваться'
                    )
                    await member.send(random.choice(random_answers))
                    await interaction.response.send_message('Отправлено!', ephemeral=True)
                    await interaction.message.delete()
                    return 
                
        elif data_splited[1] == 'reject':
            group = objects.Group(int(data_splited[2]))
            group.task = None
            member = (await group.get_members(custom_members=[group.leader_id or 0]))[0]
            await member.send('К сожалению вы не выполнили свое задание. Выберите новое заново!')
            await interaction.response.send_message('Отправлено!', ephemeral=True)
            await interaction.message.delete()

            

def setup(bot: Bot):
    bot.add_cog(InteractiveEvents(bot))