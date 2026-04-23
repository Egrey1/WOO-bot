from .commands import *

class Rights(RightsControl):
    def __init__(self, bot):
        self.bot = bot

def setup(bot):
    bot.add_cog(Rights(bot))