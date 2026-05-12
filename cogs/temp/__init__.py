from .commands import *

class Temp(Clear, GiveRole, Roll):
    def __init__(self, bot):
        self.bot = bot

def setup(bot):
    bot.add_cog(Temp(bot))