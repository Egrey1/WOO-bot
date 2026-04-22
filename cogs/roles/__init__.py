from .commands import *

class Roles(RolesCommands):
    def __init__(self, bot):
        self.bot = bot

def setup(bot):
    bot.add_cog(Roles(bot))