from ..library import Modal, deps, TextInput, TextInputStyle, ModalInteraction

class EditResourceModal(Modal):

    def __init__(self, resource: deps.Resource):
        super().__init__(title='Редактирование ресурса') # type: ignore
        self.resource = resource

        self.name = TextInput(label='Название', required=False, max_length=32)
        self.description = TextInput(label='Описание', required=False, style=TextInputStyle.long, max_length=1024)
        self.emoji = TextInput(label='Эмодзи', required=False, max_length=32)
    
    async def callback(self, interaction: ModalInteraction) -> None:
        name = self.name.value.strip() if self.name.value else None
        description = self.description.value.strip() if self.description.value else None
        emoji = self.emoji.value.strip() if self.emoji.value else None

        if not any((name, description, emoji)):
            await interaction.response.send_message('Вы не указали ни одного параметра для изменения', ephemeral=True)
            return
        
        self.resource.edit(name, description, emoji)
        await interaction.response.send_message('Ресурс успешно изменен!')