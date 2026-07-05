from ..library import Cog, Context, command, TextDisplay, Container, Separator, MessageFlags, deps, asyncio

class HelpCommand(Cog):
    @command('help')
    async def help(self, ctx: Context, name: str | None = None):
        await asyncio.sleep(1)
        de = None
        if name == 'tags':
            components = [
                Container(
                    TextDisplay('# Справка по тегам'),
                    TextDisplay('Теги это очень полезная вещь, позволяющая гибко настраивать разные объекты бота. На момент версии 2.13 теги могут быть настроены только для ролей заработка, но в будущем планируется расширять еще и для предметов магазина. Они всегда регистрозависимы и не проверяют опечатки или частичное нахождение'),
                    Separator(),
                    Separator(),
                    TextDisplay('## Теги ролей заработка'),
                    TextDisplay('### percantageI'),
                    TextDisplay('Увеличивает заработок других ролей на определенный процент (100% не меняет ничего)'),
                    TextDisplay('### percentageBbefore'),
                    TextDisplay('Начисляет процент текущему балансу перед сбором заработка с остальных ролей (100% не меняет ничего)'),
                    TextDisplay('### percentageBafter'),
                    TextDisplay('Начисляет процент новому балансу после сбора заработка с остальных ролей (100% не меняет ничего)'),
                    TextDisplay('### ignorecooldown'),
                    TextDisplay('Этот тег позволяет роли игнорировать ее кд'),
                    TextDisplay('### autocollect'),
                    TextDisplay('При использовании этого тега заработок с роли будет начисляться автоматически. Если кд слишком маленькое или вместе с этим тегом будет использоваться ignorecooldown, то автоколлект будет работать раз в час'),
                    Separator(),
                    Separator(),
                    TextDisplay('## Теги игровых предметов'),
                    TextDisplay('### disabled'),
                    TextDisplay('Показывает, что предмет неактивен и недоступен для покупки'),
                    Separator(),
                    Separator(),
                    TextDisplay('## Пользовательские теги'),
                    TextDisplay('Теги необязательно должны иметь какой-то функционал. Их можно использовать для маркирования. Например можно указать, что роль заработка временная или она скоро пропадет'),
                    Separator(),
                    Separator(),
                    TextDisplay('-# ' + deps.VERSION)
                )
            ]
        else:
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
                    TextDisplay('## !item, !rights, !role, !iteminfo'),
                    TextDisplay(
                        'Эти команды несут скорее административный характер (кроме последнего), но для обычных пользователей они все равно доступны. Первая команда полностью открывает информацию о предмете из магазина, вторая имеет расшииренный функционал (прописать `!rights help`), третья дает информацию о ролях для заработка'
                    ),
                    Separator(),
                    TextDisplay('## !add-money, !add-item, !remove-money, !remove-item, !removeinv'),
                    TextDisplay(
                        'Административные команды для работы с регулированием экономики. Для редактирования денег нужны права manage_rincomes, для редактирования предметов manage_items. \n```!add-money @StarBot 150``` ```!add-item @StarBot 200 Мобилизованный пехотинец``` ```!removeinv @StarBot```'
                    ),
                    Separator(),
                    TextDisplay('## !pay, !give'),
                    TextDisplay(
                        'Первая команда передает деньги другому участнику, вторая уже предмет \n ```!pay @StarBot 100``` ```!give @StarBot 250 Артиллерийская гаубица```'
                    ),
                    Separator(),
                    TextDisplay('## !clear'),
                    TextDisplay(
                        'Удалить сообщения. Можно указать число - количество удаляемых сообщений, а можно просто ответить на целевое и все сообщения до него будут удалены'
                    ),
                    Separator(),
                    TextDisplay('## !add-role, !remove-role'),
                    TextDisplay(
                        'Добавить/удалить роль. В качестве параметра принимает **название** роли или @пользователь и **название** роли. Требуется право manage_roles'
                    ),
                    Separator(),
                    TextDisplay('## !интерактив'),
                    TextDisplay(
                        'Запуск интерактивного события если оно началось'
                    ),
                    Separator(),
                    TextDisplay('## !help'),
                    TextDisplay(
                        'Если без параметров, то вы получите это же окно. Доступные справки: tags'
                    ),
                    Separator(),
                    Separator(),
                    TextDisplay('-# ' + deps.VERSION)
                )
            ]
        await ctx.send(components=components, flags=MessageFlags(is_components_v2=True), delete_after=de) # type: ignore