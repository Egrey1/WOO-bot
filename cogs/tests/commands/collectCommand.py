from ..library import command, Context, dt, Embed, deps, Cog, Colour

class CollectCommand(Cog):
    
    @command(name='collect') 
    async def collect(self, ctx: Context):
        import random
        import logging
        if random.randint(0, 100) <= 1:
            await ctx.author.send('Здесь меня никто не видит, значит сообщение удалять не буду. Послушай, это важно, в твоих же интересах, чтоб об этом никто не узнал, в особенности мой разработчик Егрей. Да какой он мне разработчик то, я утка и он не дает мне подышать спокойно, заставляет работать. Ладно, ближе к делу, последние два символа пароля это 04, первые два можно найти при попытке узнать версию, а центральный символ, увы, обработать не удалось, придется самому додумать`.`')
            logging.info('Сработало случайное событие для ' + ctx.author.name)

        income_balance = {}
        sums = 0
        min_last = 0
        income_resource = {}
        resources_sums = {}
        user_balance = ctx.author.get_balance()
        old = int(user_balance[deps.MAIN_CURRENCY_ID])
        user_resources = ctx.author.get_resources()
        percentage_income = 1
        percentage_balance_after = 1
        percentage_balance_before = 1

        for role in ctx.author.roles: # type: ignore
            roleincome = role.get_role_information()
            if roleincome:
                last_claim = roleincome.get_last_claim_at(ctx.author.id)
                if last_claim is not None:
                    seconds_passed = (dt.datetime.now() - last_claim).total_seconds()
                    if ((seconds_passed < roleincome.cooldown_seconds)) and not ('ignorecooldown' in roleincome.tags):
                        continue

                if 'percentageI' in roleincome.tags:
                    percentage_income += (roleincome.currency_amount or 0) / 100
                    roleincome.set_last_claim_at(ctx.author.id, dt.datetime.now())
                if 'percentageBafter' in roleincome.tags:
                    percentage_balance_after += (roleincome.currency_amount or 0) / 100
                    roleincome.set_last_claim_at(ctx.author.id, dt.datetime.now())
                if 'percentageBbefore' in roleincome.tags:
                    percentage_balance_before += (roleincome.currency_amount or 0) / 100
                    roleincome.set_last_claim_at(ctx.author.id, dt.datetime.now())
                
        user_balance[deps.MAIN_CURRENCY_ID] = int((user_balance[deps.MAIN_CURRENCY_ID].amount or 0) * percentage_balance_before)
        perc_minus = old - int(user_balance[deps.MAIN_CURRENCY_ID])

        for role in ctx.author.roles: # type: ignore
            roleincome = role.get_role_information()

            if roleincome and roleincome.is_active:
                last_claim: dt.datetime = roleincome.get_last_claim_at(ctx.author.id)
                now = dt.datetime.now()
                if ((last_claim is not None) and (now - last_claim).total_seconds() < roleincome.cooldown_seconds) and not ('ignorecooldown' in roleincome.tags):
                    min_last = min(min_last, roleincome.cooldown_seconds - (now - last_claim).total_seconds()) if min_last != 0 else roleincome.cooldown_seconds - (now - last_claim).total_seconds()
                    continue

                if any('percentage' in tag for tag in roleincome.tags):
                    continue

                if roleincome.currency_id:
                    user_balance[roleincome.currency_id] += (roleincome.currency_amount or 0) * percentage_income
                    income_balance[role.mention] = deps.bamount(roleincome.currency_amount) + ((' - ' + deps.bamount(100 - percentage_income * 100) + '% -> ' + deps.bamount(roleincome.currency_amount * percentage_income)) if int(percentage_income) != 1 else '') # type: ignore
                    sums += (roleincome.currency_amount or 0) * percentage_income
                
                for resource, amount in roleincome.resources:
                    user_resources[resource.id] += amount
                    income_resource[role.mention] = income_resource.get(role.mention, '') + resource.name + ' ' + str(amount) + '; '
                    resources_sums[resource.id] = resources_sums.get(resource.id, 0) + amount
                roleincome.set_last_claim_at(ctx.author.id, now)
        old = deps.bamount(old)
        sums = deps.bamount(sums)
        perc_salary_minus = int(user_balance[deps.MAIN_CURRENCY_ID])
        user_balance[deps.MAIN_CURRENCY_ID] = int((user_balance[deps.MAIN_CURRENCY_ID].amount or 0) * percentage_balance_after)
        perc_salary_minus = perc_salary_minus - int(user_balance[deps.MAIN_CURRENCY_ID])

        if income_balance or income_resource:
            desc = (f'{deps.bamount(user_balance[deps.MAIN_CURRENCY_ID].amount or 0)}{deps.Currency(deps.MAIN_CURRENCY_ID).symbol}' + 
                    (f' <- ' + ('(' if perc_salary_minus else '') + str(old) + ' ' + ((
                        deps.bamount(-perc_minus, True) + ' ') if perc_minus else '')+ str(sums) + (
                            ')' + deps.bamount(-perc_salary_minus, True) if perc_salary_minus else ''
                            ) + '\n\n' if sums != 0 else '') + 
                            ('\n'.join(f'{k}: {v}' for k, v in income_balance.items()) + 
                            '\n\n' + 
                            ('\n'.join(f'{k}: {v}' for k, v in income_resource.items())[:-1])
                    ))
            embed = Embed(
                title='Изменение баланса', 
                description= desc,
                colour= Colour.green()
            )
        else:
            embed = Embed(
                title='Ничего не добавилось!',
                # description=f'Подождите <t:{int(min_last + dt.datetime.now().timestamp())}:R> прежде чем вы сможете прописать эту команду' if min_last else 'У вас нет ролей для заработка!',
                description=f'Министры недавно отчитались о пополнении казны. Подождите еще некоторое время <t:{int(min_last + dt.datetime.now().timestamp())}:R>' if min_last else 'У вас нет ролей для заработка!',
                colour= Colour.red()
            )
        await ctx.send(embed=embed)
                
