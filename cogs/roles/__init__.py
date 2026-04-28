from .commands import *
from .loops import CollectLoop
import time

class Roles(RolesCommands, CollectLoop):
    def __init__(self, bot):
        self.bot = bot
        self._first_time = True
        self.collect_loop.start()

def setup(bot):
    bot.add_cog(Roles(bot))