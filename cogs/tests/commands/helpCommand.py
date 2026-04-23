from ..library import Cog, Context, command, TextDisplay, Container, Separator, MessageFlags, deps

class HelpCommand(Cog):
    @command('help')
    async def help(self, ctx: Context):
        components = [
            Container(
                TextDisplay('# Справка по боту'),
                Separator(),
                Separator(),
                TextDisplay('## !collect, !bal, !shop, !buy, !inv'),
                TextDisplay(
                    'Базовые команды с которыми все знакомы. Первая для сбора денег, вторая для просмотра баланса, третья для просмотра магазина, четвертая для покупки товаров оттуда, пятая для просмотра текущего инвентаря. В этих командах никаких интерактивных элементов нет'
                ),
                Separator(),
                TextDisplay('## !item, !rights, !role'),
                TextDisplay(
                    'Эти команды несут скорее административный характер, но для обычных пользователей они все равно доступны. Первая команда полностью открывает информацию о предмете из магазина, вторая имеет расшииренный функционал (прописать `!rights help`), третья дает информацию о ролях для заработка'
                ),
                Separator(),
                TextDisplay('-# ' + deps.VERSION)
            )
        ]
        await ctx.send(components=components, flags=MessageFlags(is_components_v2=True))