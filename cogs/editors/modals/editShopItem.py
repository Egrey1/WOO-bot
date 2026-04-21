from ..library import Modal, deps, TextInput, TextInputStyle, ModalInteraction, Role

class EditShopItemModal(Modal):

    def __init__(self, resource: deps.ShopItem, required_role: Role | None):
        super().__init__(title='Редактирование предмета из магазина') # type: ignore
        self.resource = resource
        self.required_role = required_role

        self.name = TextInput(label='Название', required=False, max_length=32)
        self.description = TextInput(label='Описание', required=False, style=TextInputStyle.long, max_length=1024)
        self.cost = TextInput(label='Стоимость', required=False, max_length=20, placeholder='0')
    
    async def callback(self, interaction: ModalInteraction) -> None:
        name = self.name.value
        description = self.description.value
        cost = self.cost.value

        if not any((name, description, cost)):
            await interaction.response.send_message('Вы не указали ни одного параметра для изменения', ephemeral=True)
            return
        
        try:
            self.resource.edit(name, description, int(cost) if cost else None, self.required_role)
            embed = self.resource.get_embed()
            await interaction.response.send_message('Предмет успешно изменен!', embed=embed)
        except:
            await interaction.response.send_message('Неверно введена стоимость! ожидалось число', ephemeral=True)