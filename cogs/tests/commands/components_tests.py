from ..library import command, Context, Cog
import disnake.ui as ui
from disnake import MessageFlags, MediaGalleryItem

class ComponentsTests(Cog):

    @command('starlight', aliases=['StarLight', 'Starlight', 'starLight'])
    async def t(self, ctx: Context):
        await ctx.send('Это самый лучший сервер в своем роде! Поверьте мне`.` `.` `.`')
        