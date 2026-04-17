from .commands import *

class ShopCog(InvCommand, ShopCommand):
    def __init__(self, bot):
        self.bot = bot

def setup(bot):
    bot.add_cog(ShopCog(bot))