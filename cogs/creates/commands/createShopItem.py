from ..library import Cog, deps, command, Context, Message

class CreateShopItem(Cog):
    @command(name='create-item', aliases=['create_item'])
    async def create_item(self, ctx: Context):
        if True:
            pass
    
        await ctx.send('В процессе реализации')
    
    @Cog.listener()
    async def on_message(self, message: Message):
        pass