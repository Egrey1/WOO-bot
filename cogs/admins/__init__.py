from .commands import *

class AdminsCommands(AddItem, AddMoney, RemoveItem, RemoveMoney):
    def __init__(self, bot):
        self.bot = bot

def setup(bot):
    bot.add_cog(AdminsCommands(bot))