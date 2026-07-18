from disnake import CategoryChannel, ForumChannel, MediaChannel, Message, MessageFlags, ModalInteraction, ui
import dependencies as deps
from . import EventPlayer, Group
import logging
import datetime as dt

class CreateGroupModal(ui.Modal):
    def __init__(self):
        super().__init__(
            title='Название группы', 
            components=ui.TextInput(
                label='Введите название',
                max_length=64,
                custom_id='group_name'
            )
        )
    
    async def callback(self, interaction: ModalInteraction):
        name = interaction.text_values['group_name']
        try:
            with deps.interactive as connect:
                cursor = connect.cursor()
                cursor.execute("""
                               SELECT *
                               FROM groups
                               WHERE name = ?
                               """, (name.strip(), ))
                fetch = cursor.fetchone()
                if fetch:
                    return await interaction.response.send_message('Такое название уже используется!')
        except Exception as e:
            logging.error(e)
        group = Group.create(name.strip())
        group.edit(leader_id=interaction.author.id)
        group.members_id += [interaction.author.id]
        if interaction.message: await interaction.message.edit(components= await group.get_v2_info(True))
        await interaction.response.send_message('Успешно создано!', ephemeral=True)

class EditGroup(ui.Modal):
    def __init__(self, group: Group):
        super().__init__(title='Изменение названия', components=ui.TextInput(
                label='Введите название',
                max_length=64,
                custom_id='group_name'
            ))
        self.group = group
    
    async def callback(self, interaction: ModalInteraction):
        name = interaction.text_values['group_name']
        try:
            with deps.interactive as connect:
                cursor = connect.cursor()
                cursor.execute("""
                               SELECT *
                               FROM groups
                               WHERE name = ?
                               """, (name.strip(), ))
                fetch = cursor.fetchone()
                if fetch:
                    return await interaction.response.send_message('Такое название уже используется!')
        except Exception as e:
            logging.error(e)
        self.group.edit(name=name)
        if interaction.message: await interaction.message.edit(components= await self.group.get_v2_info(True))
        await interaction.response.send_message('Успешно изменено!', ephemeral=True)

class GiveLink(ui.Modal):
    def __init__(self, group: Group):
        super().__init__(title='Использование первой способности', components=ui.TextInput(
            label='Ссылка',
            placeholder='Введите ссылку на сообщение Эрнесто с уведомлением об откате',
            custom_id='message_link'
        ))
        self.group = group

    async def callback(self, interaction: ModalInteraction):
        link = interaction.text_values['message_link'].split('/')
        try:
            mes_id, channel_id = int(link[-1]), int(link[-2])
            channel = await deps.main_guild.fetch_channel(channel_id)
        except:
            return await interaction.response.send_message('Неверный формат ссылки!', ephemeral=True)
        message: Message | None = None
        if isinstance(channel, ForumChannel) or isinstance(channel, MediaChannel):
            for thread in channel.threads:
                try:
                    message = await thread.fetch_message(mes_id)
                    break
                except:
                    pass
        elif isinstance(channel, CategoryChannel):
            pass
        else:
            try:
                message = await channel.fetch_message(mes_id)
            except:
                message = None
        
        if message is None:
            return await interaction.response.send_message('Вы указали неверную ссылку', ephemeral=True)
        
        if message.author.id != 642766756699570196:
        # if message.author.id != 820595582027956247:
            return await interaction.response.send_message('Автором должен быть обязательно Эрнесто, иначе ничего не удастся', ephemeral=True)

        if not message.content.lower().startswith('# откат'):
            return await interaction.response.send_message('Это не сообщение об откате. Нам нельзя удалять все подряд', ephemeral=True)
        
        try:
            ch = message.channel
            await message.delete()
            message = await ch.send('### Этот откат был откачен партизанской группировкой `' + self.group.name + '`! Ура! Ура! Ура!', delete_after=600)
            await interaction.response.send_message('Отлично! Все прошло хорошо! Вы молодцы ' + message.jump_url + f'\nВ следующий раз вы сможете повторить <t:{int((60 * 60 * 2) + dt.datetime.now().timestamp())}:R>')
            d = self.group.last_use_ability
            d[1] = dt.datetime.now()
            self.group.last_use_ability = d
        
        except Exception as e:
            await interaction.response.send_message('Что-то помешало мне удалить сообщение. Это ужасно.', ephemeral=True)
            logging.error(e)

class MessageUpg(ui.Modal):
    def __init__(self, group: Group):
        super().__init__(
            title='Отправка рассылки',
            components=[
                ui.TextInput(
                    label='Содержание',
                    custom_id='message_content',
                    max_length=512
                )
            ]
        )
        self.group = group
    
    async def callback(self, interaction: ModalInteraction):
        value = interaction.text_values['message_content']
        members = await self.group.get_members()
        components = [
            ui.Container(
                ui.TextDisplay('## Сообщение от лидера группировки'),
                ui.Separator(),
                ui.Separator(),
                ui.TextDisplay('```\n' + value + '\n```')
            )
        ]

        counter = 0
        for member in members:
            if member.id == interaction.author.id: continue
            try:
                await member.send(components=components, flags=MessageFlags(is_components_v2=True))
                counter += 1
            except:
                pass
        
        await interaction.response.send_message('Успешно отправлено ' + str(counter) + ' участникам вашей организации')

