from ..library import command, Context, Cog
import disnake.ui as ui
from disnake import MessageFlags, MediaGalleryItem

class ComponentsTests(Cog):

    @command('t')
    async def t(self, ctx: Context):
        components = [
            ui.Container(
                ui.TextDisplay('# Заголовок 1'),
                ui.TextDisplay('## Заголовок 2'),
                ui.TextDisplay('### Заголовок 3'),
                ui.Separator(),
                ui.Section(
                    ui.TextDisplay('Текст длинный оооооооооооооооооооооооооооооооооооооооооооооооооо'),
                    accessory= ui.Button(label='Кнопка')
                ),
                ui.Separator(),
                ui.MediaGallery(
                    MediaGalleryItem('https://avatars.mds.yandex.net/i?id=d31533f6478cb25237e32986ed4098e7e2beb2e7-12569871-images-thumbs&n=13'),
                    MediaGalleryItem('https://avatars.mds.yandex.net/i?id=d31533f6478cb25237e32986ed4098e7e2beb2e7-12569871-images-thumbs&n=13'),
                    MediaGalleryItem('https://avatars.mds.yandex.net/i?id=d31533f6478cb25237e32986ed4098e7e2beb2e7-12569871-images-thumbs&n=13'),
                    MediaGalleryItem('https://avatars.mds.yandex.net/i?id=d31533f6478cb25237e32986ed4098e7e2beb2e7-12569871-images-thumbs&n=13'),
                    MediaGalleryItem('https://avatars.mds.yandex.net/i?id=d31533f6478cb25237e32986ed4098e7e2beb2e7-12569871-images-thumbs&n=13'),
                    MediaGalleryItem('https://avatars.mds.yandex.net/i?id=d31533f6478cb25237e32986ed4098e7e2beb2e7-12569871-images-thumbs&n=13'),
                    MediaGalleryItem('https://avatars.mds.yandex.net/i?id=d31533f6478cb25237e32986ed4098e7e2beb2e7-12569871-images-thumbs&n=13'),
                    MediaGalleryItem('https://avatars.mds.yandex.net/i?id=d31533f6478cb25237e32986ed4098e7e2beb2e7-12569871-images-thumbs&n=13'),
                    MediaGalleryItem('https://avatars.mds.yandex.net/i?id=d31533f6478cb25237e32986ed4098e7e2beb2e7-12569871-images-thumbs&n=13'),
                    MediaGalleryItem('https://avatars.mds.yandex.net/i?id=d31533f6478cb25237e32986ed4098e7e2beb2e7-12569871-images-thumbs&n=13')
                )
            ),
            ui.ActionRow(
                ui.Button(label='1'),
                ui.Button(label='2')
            )
        ]
        await ctx.send(components=components, flags=MessageFlags(is_components_v2=True))
        