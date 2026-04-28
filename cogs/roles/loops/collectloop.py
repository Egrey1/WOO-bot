from ..library import loop, deps, Role, dt, Member, logging

class CollectLoop:
    @loop(seconds=20)
    async def collect_loop(self):
        logging.info('Сбор автоколлектов')
        roleincomes: list[deps.RoleIncome] = []
        for roleincome in deps.RoleIncome.all(True):
            roleincome = deps.RoleIncome(roleincome.id)
            if 'autocollect' in roleincome.tags:
                roleincomes.append(roleincome)
        roles: list[Role] = []
        members: set[Member] = set()
        for roleincome in roleincomes:
            try:
                roles.append(await deps.main_guild.fetch_role(roleincome.role_id))
            except:
                continue
        
        for role in roles:
            members = members.union(role.members)
        
        
        for member in members:
            user_balance = member.get_balance()
            user_resources = member.get_resources()
            percentage_income = 1
            percentage_balance_after = 1
            percentage_balance_before = 1

            for role in member.roles: 
                roleincome = role.get_role_information()
                if roleincome:
                    last_claim = roleincome.get_last_claim_at(member.id)
                    seconds_passed = (dt.datetime.now() - last_claim).total_seconds()
                    if ((last_claim is not None) and (seconds_passed < roleincome.cooldown_seconds)) and not ('ignorecooldown' in roleincome.tags):
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

