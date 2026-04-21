from .commands import *

class Removes(RemoveCurrency, RemoveResource, RemoveShopItem):
    def __init__(self, bot):
        self.bot = bot

def setup(bot):
    bot.add_cog(Removes(bot))