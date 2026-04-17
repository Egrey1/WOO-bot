from .commands import *

class TestCog(AddRoleIncome, CollectCommand, BalCommand):
    def __init__(self, bot):
        self.bot = bot

def setup(bot):
    bot.add_cog(TestCog(bot))