from .commands import *

class Creates(AddRoleIncome):
    def __init__(self, bot):
        self.bot = bot
        self.users = {}
        self.messages = {}
        self.messagesS = {}
        self.creater = {}

def setup(bot):
    bot.add_cog(Creates(bot))