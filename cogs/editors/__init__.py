from .commands import *
from .library import Cog

class Editors(Cog):
    def __init__(self, bot):
        self.bot = bot

def setup(bot):
    bot.add_cog(Editors(bot))