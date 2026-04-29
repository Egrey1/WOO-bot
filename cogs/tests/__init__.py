from .commands import *

class TestCog(CollectCommand, BalCommand, VersionCommand, HelpCommand, PayCommand, GiveCommand, TopCommand, ComponentsTests):
    def __init__(self, bot):
        self.bot = bot

def setup(bot):
    bot.add_cog(TestCog(bot))