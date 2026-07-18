from .commands import *

class AdminsCommands(AddItem, AddMoney, RemoveItem, RemoveMoney, WipeCommand, RemoveInvCommand, TempHooks):
    def __init__(self, bot):
        self.bot = bot
        self.cheker.start()

def setup(bot):
    bot.add_cog(AdminsCommands(bot))