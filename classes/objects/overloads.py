from __future__ import annotations

import datetime as dt
from sqlite3 import Connection

from disnake.user import _UserTag
from disnake import Role
from disnake import ui

from ..library import deps, logging
from .game_objects import RoleIncome


class NewConnection(Connection):
    def __init__(self, database, *args, **kwargs):
        super().__init__(database, *args, **kwargs)

    def autocreate_user(self: Connection, user_id: int) -> None:
        cursor = self.cursor()
        cursor.execute(
            """
            INSERT OR IGNORE INTO users (id)
            VALUES (?)
            """,
            (user_id,),
        )

        cursor.execute(
            """
            INSERT OR IGNORE INTO user_balances (user_id, currency_id, amount)
            SELECT ?, id, 0
            FROM currencies
            """,
            (user_id,),
        )

        cursor.execute(
            """
            INSERT OR IGNORE INTO user_resources (user_id, resource_id, amount)
            SELECT ?, id, 0
            FROM resources
            """,
            (user_id,),
        )

        self.commit()
        cursor.close()


class NewUser(_UserTag):
    def in_db(self) -> bool:
        try:
            with deps.main_db as connect:
                cursor = connect.cursor()
                cursor.execute(
                    """
                    SELECT 1
                    FROM users
                    WHERE id = ?
                    """,
                    (self.id,),
                )
                fetch = cursor.fetchone()
                cursor.close()
                return fetch is not None
        except Exception as error:
            logging.warning(f'Ошибка в NewUser.in_db: {error}')
            return False

    def get_balance(self):
        deps.main_db.autocreate_user(self.id)
        return deps._UserBalance(self.id)  

    def get_resources(self):
        deps.main_db.autocreate_user(self.id)
        return deps._UserResources(self.id) 

    def get_inventory(self):
        deps.main_db.autocreate_user(self.id)
        return deps._UserInventory(self.id)
    
    def get_v2balance(self):
        balance = self.get_balance()[deps.MAIN_CURRENCY_ID]
        return [
            ui.Container(
                ui.TextDisplay(
                    '# Баланс пользователя <@' + str(self.id) + '>'
                ),
                ui.Separator(),
                ui.Separator(),
                ui.Section(
                    ui.TextDisplay(
                        '🔷 **В казне: ' + deps.bamount(balance.amount) + '**'
                    ),
                    accessory=ui.Button(
                        label='Пополнить',
                        emoji='🔁',
                        custom_id=f'balance_withdraw {self.id}'
                    )
                ),
                ui.Separator(),
                ui.Section(
                    ui.TextDisplay(
                        '🔶 **За рубежом: ' + deps.bamount(0) + '**'
                    ),
                    accessory=ui.Button(
                        label='Перевести',
                        emoji='🏦',
                        custom_id=f'balance_deposit {self.id}'
                    )
                ),
                ui.Separator(),
                ui.TextDisplay(
                    '💠 **Всего: ' + deps.bamount(balance.amount) + '**'
                )
            )
        ]


class NewRole(Role):
    def get_role_income(self) -> RoleIncome | None:
        try:
            return RoleIncome.from_role(self)
        except LookupError:
            return None
        except Exception as error:
            logging.error(f'Ошибка в NewRole.get_role_income: {error}')
            return None

    def get_role_information(self):
        try:
            return RoleIncome.from_role(self)
        except LookupError:
            return None
        except Exception as error:
            logging.error(f'Ошибка в NewRole.get_role_income: {error}')
            return None

    # def create_role_income(
    #     self,
    #     cooldown_seconds: int,
    #     currency: int | None = None,
    #     currency_amount: int | None = None,
    #     resources: list[tuple[int | str, int]] | None = None,
    # ) -> RoleIncome:
    #     return RoleIncome.create(
    #         role=self,
    #         cooldown_seconds=cooldown_seconds,
    #         currency=currency,
    #         currency_amount=currency_amount,
    #         resources=resources,
    #     )

    def create_role_information(
        self,
        cooldown: int | dt.timedelta,
        earning: int | float | None,
        currency: int | str | None,
        resources: list[tuple[int | str, int]] | str | None,
        tags: list[str] | tuple[str, ...] | None = None,
    ) -> RoleIncome:
        cooldown_seconds = int(cooldown.total_seconds()) if isinstance(cooldown, dt.timedelta) else int(cooldown)
        normalized_resources = resources

        if isinstance(resources, str):
            normalized_resources = []
            for raw_resource in resources.split(';'):
                resource_id, amount = raw_resource.split(':', maxsplit=1)
                normalized_resources.append((int(resource_id), int(amount)))

        return RoleIncome.create(
            role=self,
            cooldown_seconds=cooldown_seconds,
            currency=int(currency) if currency is not None else None,
            currency_amount=earning,
            resources=normalized_resources, # type: ignore
            tags=tags,
        )

    def edit_role_income(
        self,
        cooldown_seconds: int | None = None,
        currency: int | None = None,
        currency_amount: int | float | None = None,
        resources: list[tuple[int | str, int]] | None = None,
        is_active: bool | None = None,
        tags: list[str] | tuple[str, ...] | None = None,
    ) -> None:
        role_income = RoleIncome.from_role(self)
        role_income.edit(
            cooldown_seconds=cooldown_seconds,
            currency=currency,
            currency_amount=currency_amount,
            resources=resources,
            is_active=is_active,
            tags=tags,
        )

    def edit_role_information(self, **kwargs) -> None:
        cooldown = kwargs.get('cooldown')
        cooldown_seconds = None
        if isinstance(cooldown, dt.timedelta):
            cooldown_seconds = int(cooldown.total_seconds())
        elif cooldown is not None:
            cooldown_seconds = int(cooldown)

        self.edit_role_income(
            cooldown_seconds=cooldown_seconds,
            currency=kwargs.get('currency'),
            currency_amount=kwargs.get('earning'),
            resources=kwargs.get('resources'),
            is_active=kwargs.get('is_active'),
            tags=kwargs.get('tags'),
        )
