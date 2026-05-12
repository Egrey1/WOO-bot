from ..library import Cog, Context, command, random, Container, TextDisplay, Separator, MessageFlags, Colour, asyncio

class Roll(Cog):
    @command('roll')
    async def roll(self, ctx: Context, *, args: str):
        choice = ''
        components = [
            Container(
                TextDisplay('## Выбор рандомного элемента'),
                Separator(),
                TextDisplay('Идет подсчет вероятностей...')
            )
        ]
        mes = await ctx.send(components=components, flags=MessageFlags(is_components_v2=True))

        if args.isdigit():
            choice = str(random.randint(1, int(args)))
            components = [
                Container(
                    TextDisplay('## Выбор рандомного элемента'),
                    Separator(),
                    TextDisplay('*Черт, пользователь выбрал число, это многое меняет. Надо срочно что-то придумать*')
                )
            ]
            await mes.edit(components=components, flags=MessageFlags(is_components_v2=True))
            await asyncio.sleep(3)
            for i in range(1, int(args) + 1):
                components = [
                    Container(
                        TextDisplay('## Выбор рандомного элемента'),
                        Separator(),
                        TextDisplay('Это число подходит? `' + str(i) + '`'),
                        Separator(),
                        TextDisplay('-# Почему так много...? Черт, надо передохнуть') 
                    ) if i == 6 else Container(
                        TextDisplay('## Выбор рандомного элемента'),
                        Separator(),
                        TextDisplay('Это число подходит? `' + str(i) + '`')
                    ) 
                ]
                await mes.edit(components=components, flags=MessageFlags(is_components_v2=True))
                await asyncio.sleep(0.1 * (15 * (i == 6)))
                if (str(i) == choice) or (i == 11):
                    components = [
                        Container(
                            TextDisplay('## Выбор рандомного элемента'),
                            Separator(),
                            TextDisplay('**' + choice + '**'),
                            TextDisplay('-# Миссия завершена успешно, но достойно ли? Не уверен'),
                            accent_colour=Colour.green(),
                            spoiler=True
                        )
                    ]
                    await mes.edit(components=components, flags=MessageFlags(is_components_v2=True))
                    break

        else:
            choice = random.choice(args.split(',')).strip()
            for arg in args.split(','):
                components = [
                    Container(
                        TextDisplay('## Выбор рандомного элемента'),
                        Separator(),
                        TextDisplay('Идет проверка на достоинство элемента `' + arg.strip() + '`')
                    )
                ]
                await mes.edit(components=components, flags=MessageFlags(is_components_v2=True))
                await asyncio.sleep(0.4)
                if arg.strip() == choice:
                    components = [
                        Container(
                            TextDisplay('## Рандомный элемент выбран'),
                            Separator(),
                            TextDisplay('**' + arg.strip() + '**'),
                            TextDisplay('-# Миссия завершена успешно и достойно, я покидаю свой пост'),
                            accent_colour=Colour.green(),
                            spoiler=True
                        )
                    ]
                    await mes.edit(components=components, flags=MessageFlags(is_components_v2=True))
                    break


        