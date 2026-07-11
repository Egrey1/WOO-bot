from disnake import ModalInteraction, ui
import dependencies as deps
from . import Group
import logging
import asyncio

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
        group = Group.create(name)
        group.edit(leader_id=interaction.author.id)
        group.members_id += [interaction.author.id]
        if interaction.message: await interaction.message.edit(components= await group.get_v2_info(True))
        await interaction.response.send_message('Успешно создано!', ephemeral=True)