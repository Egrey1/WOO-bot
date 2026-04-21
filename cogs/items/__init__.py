from .commands import *

class Items(ItemCommands):
    def __init__(self, bot):
        self.bot = bot

def setup(bot):
    bot.add_cog(Items(bot))