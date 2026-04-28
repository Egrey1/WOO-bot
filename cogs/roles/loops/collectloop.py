from ..library import loop, deps, Role, dt, Member, logging

class CollectLoop:
    @loop(hours=1)
    async def collect_loop(self):
        logging.info('Сбор автоколлектов')
        roleincomes: list[deps.RoleIncome] = []
        for roleincome in deps.RoleIncome.all(True):
            roleincome = deps.RoleIncome(roleincome.id)
            # if 'autocollect' in roleincome.tags:
            roleincomes.append(roleincome)
        members: set[Member] = set()

        a = await deps.main_guild.chunk()

        for roleincome in roleincomes:
            role = deps.main_guild.get_role(roleincome.role_id)
            if role:
                async for member in deps.main_guild.fetch_members(limit=None):
                    if role in member.roles:
                        members.add(member)
            else:
                continue
        
        
        for member in members:
            user_balance = member.get_balance()
            user_resources = member.get_resources()
            percentage_income = 1
            percentage_balance_after = 1
            percentage_balance_before = 1

            for role in member.roles: 
                roleincome = role.get_role_information()
                if roleincome:
                    if 'autocollect' not in roleincome.tags:
                        continue
                    last_claim = roleincome.get_last_claim_at(member.id)
                    if last_claim is not None:
                        seconds_passed = (dt.datetime.now() - last_claim).total_seconds()
                        if ((seconds_passed < roleincome.cooldown_seconds)) and not ('ignorecooldown' in roleincome.tags):
                            continue

                    if 'percentageI' in roleincome.tags:
                        percentage_income += (roleincome.currency_amount or 0) / 100
                        roleincome.set_last_claim_at(member.id, dt.datetime.now())
                    if 'percentageBafter' in roleincome.tags:
                        percentage_balance_after += (roleincome.currency_amount or 0) / 100
                        roleincome.set_last_claim_at(member.id, dt.datetime.now())
                    if 'percentageBbefore' in roleincome.tags:
                        percentage_balance_before += (roleincome.currency_amount or 0) / 100
                        roleincome.set_last_claim_at(member.id, dt.datetime.now())
                    
            user_balance[deps.MAIN_CURRENCY_ID] = int((user_balance[deps.MAIN_CURRENCY_ID].amount or 0) * percentage_balance_before)


            for role in member.roles:
                roleincome = role.get_role_information()

                if roleincome and roleincome.is_active:
                    if 'autocollect' not in roleincome.tags:
                        continue
                    last_claim: dt.datetime = roleincome.get_last_claim_at(member.id)
                    now = dt.datetime.now()
                    if ((last_claim is not None) and (now - last_claim).total_seconds() < roleincome.cooldown_seconds) and not ('ignorecooldown' in roleincome.tags):
                        continue

                    if any('percentage' in tag for tag in roleincome.tags):
                        continue

                    if roleincome.currency_id:
                        user_balance[roleincome.currency_id] += (roleincome.currency_amount or 0) * percentage_income
                    
                    for resource, amount in roleincome.resources:
                        user_resources[resource.id] += amount
                    roleincome.set_last_claim_at(member.id, now)
            user_balance[deps.MAIN_CURRENCY_ID] = int((user_balance[deps.MAIN_CURRENCY_ID].amount or 0) * percentage_balance_after)
        logging.info('Сбор автоколлектов закончился')

