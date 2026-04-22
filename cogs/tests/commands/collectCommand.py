from ..library import command, Context, dt, Embed, deps, Cog, Colour

class CollectCommand(Cog):
    
    @command(name='collect') 
    async def collect(self, ctx: Context):
        income_balance = {}
        sums = 0
        min_last = 0
        income_resource = {}
        resources_sums = {}
        user_balance = ctx.author.get_balance()
        old = user_balance[deps.MAIN_CURRENCY_ID]
        user_resources = ctx.author.get_resources()

        for role in ctx.author.roles: # type: ignore
            roleincome = role.get_role_information()

            if roleincome and roleincome.is_active:
                last_claim: dt.datetime = roleincome.get_last_claim_at(ctx.author.id)
                now = dt.datetime.now()
                if (last_claim is not None) and (now - last_claim).total_seconds() < roleincome.cooldown_seconds:
                    min_last = min(min_last, (now - last_claim).total_seconds()) if min_last != 0 else (now - last_claim).total_seconds()
                    continue

                if roleincome.currency_id:
                    user_balance[roleincome.currency_id] += roleincome.currency_amount if roleincome.currency_amount else 0
                    income_balance[role.mention] = roleincome.currency_amount
                    sums += roleincome.currency_amount if roleincome.currency_amount else 0 
                
                for resource, amount in roleincome.resources:
                    user_resources[resource.id] += amount
                    income_resource[role.mention] = income_resource.get(role.mention, '') + resource.name + ' ' + str(amount) + '; '
                    resources_sums[resource.id] = resources_sums.get(resource.id, 0) + amount
                roleincome.set_last_claim_at(ctx.author.id, now)
        
        if income_balance or income_resource:
            embed = Embed(
                title='Изменение баланса', 
                description= (
                    f'Баланс равен {user_balance[deps.MAIN_CURRENCY_ID]}{deps.Currency(deps.MAIN_CURRENCY_ID).symbol}' + 
                    (f' <- {old} + {sums}\n\n' if sums != 0 else '') + 
                            ('\n'.join(f'{k}: {v}' for k, v in income_balance.items()) + 
                            '\n\n' + 
                            ('\n'.join(f'{k}: {v}' for k, v in income_resource.items())[:-1])
                    )
                ),
                colour= Colour.green()
            )
        else:
            embed = Embed(
                title='Ничего не добавилось!',
                description=f'Подождите <t:{int(min_last + dt.datetime.now().timestamp())}:R> прежде чем вы сможете прописать эту команду' if min_last else 'У вас нет ролей для заработка!',
                colour= Colour.red()
            )
        await ctx.send(embed=embed)
                
