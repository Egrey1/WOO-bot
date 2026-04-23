from .commands import *

class TestCog(CollectCommand, BalCommand, VersionCommand, HelpCommand):
    def __init__(self, bot):
        self.bot = bot

def setup(bot):
    bot.add_cog(TestCog(bot))