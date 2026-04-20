from .commands import *

class Removes():
    def __init__(self, bot):
        self.bot = bot

def setup(bot):
    bot.add_cog(Removes(bot))