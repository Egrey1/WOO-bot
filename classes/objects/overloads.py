from disnake.user import _UserTag
from disnake import Role
from sqlite3 import Connection
from ..library import deps, logging, List, Tuple, dt

class NewConnection(Connection):
    def autocreate(self: Connection, user_id: int):
        cursor = self.cursor()
        cursor.execute("""
                    SELECT *
                    FROM currency
                    """)
        currencies = dict(cursor.fetchall())
        
        cursor.execute("""
                    SELECT *
                    FROM resources
                    """)
        resources = dict(cursor.fetchall())

        balance_str = ';'.join([f'{id_}:0' for id_ in currencies.keys()])
        resources_str = ';'.join([f'{id_}:0' for id_ in resources.keys()])
        cursor.execute("""
                    INSERT OR IGNORE INTO users (user_id, balance, resources)
                    VALUES (?, ?, ?)
                    """, (user_id, balance_str, resources_str))
        self.commit()
        cursor.close()

class NewUser(_UserTag):
    def get_balance(self) -> dict[str, int]:
        try:
            with deps.main_db as connect:
                cursor = connect.cursor()
                cursor.execute("""
                               SELECT balance
                               FROM users
                               WHERE id = ?
                               """, (self.id, ))
                fetch = cursor.fetchone()
                cursor.close()
                if not fetch:
                    connect.autocreate(self.id)
                    return self.get_balance()
                fetch = fetch['balance'].split(';')
                d: dict[str, int] = {}
                for bal in fetch:
                    currency, amount = bal.split(':')
                    d[currency] = int(amount)
                return d
        except Exception as e:
            logging.error(f'Ошибка в NewUser.get_balance: {e}')
            raise e
    def get_resources(self) -> dict[str, int]:
        try:
            with deps.main_db as connect:
                cursor = connect.cursor()
                cursor.execute("""
                               SELECT resources
                               FROM users
                               WHERE id = ?
                               """, (self.id, ))
                fetch = cursor.fetchone()
                cursor.close()
                if not fetch:
                    connect.autocreate(self.id)
                    return self.get_balance()
                fetch = fetch['resources'].split(';')
                d: dict[str, int] = {}
                for bal in fetch:
                    currency, amount = bal.split(':')
                    d[currency] = int(amount)
                return d
        except Exception as e:
            logging.error(f'Ошибка в NewUser.get_resources: {e}')
            raise e

class NewRole(Role):
    def get_role_information(self) -> Tuple[dt.time, int, str, List[Tuple[str, int]]] | None:
        try:
            with deps.main_db as connect:
                cursor = connect.cursor()
                cursor.execute("""
                               SELECT *
                               FROM roles
                               WHERE id = ?
                               """, (self.id, ))
                fetch = cursor.fetchone()
                if not fetch:
                    return None
                resources = fetch['resources'].split(';')
                result = []
                for resource in resources:
                    for name, amount in resource.split(':'):
                        result.append((name, int(amount)))
                result = list(result)
                return (
                    dt.time.fromisoformat(fetch['cooldown']),
                    int(fetch['earning']),
                    str(fetch['currency']),
                    result
                )
        except Exception as e:
            logging.error(f'Ошибка в NewRole.get_role_information: {e}')
    def addedit_role_information(
            self, 
            cooldown: dt.time | str = None,  # pyright: ignore[reportArgumentType]
            earning: int | str = None,  # pyright: ignore[reportArgumentType]
            currency: str = None,  # pyright: ignore[reportArgumentType]
            resources: List[Tuple[str, int]] | str = None # pyright: ignore[reportArgumentType]
            ) -> None:  # pyright: ignore[reportArgumentType]
            if isinstance(cooldown, dt.time):
                cooldown = cooldown.isoformat()
            resources = ';'.join([f'{name}:{amount}' for name, amount in resources]) if resources is not None else None # pyright: ignore[reportAssignmentType]

            if not any([cooldown, earning, currency, resources]):
                return

            arr = [
                'cooldown' if cooldown else None, 
                'earning' if earning else None, 
                'currency' if currency else None, 
                'resources' if resources else None
            ]

            set_format = ','.join([f'{name} = ?' for name in [i for i in arr if i is not None]])
            arr = [
                cooldown, earning, currency, resources
            ]
            arr = tuple([i for i in arr if i is not None] + [self.id])
            try:
                if all([cooldown, earning, currency, resources]):
                    with deps.main_db as connect:
                        cursor = connect.cursor()
                        cursor.execute("""
                                       INSERT OR REPLACE INTO roles (id, cooldown, earning, currency, resources)
                                       VALUES (?, ?, ?, ?, ?)
                                       """, (self.id, cooldown, earning, currency, resources))
                        connect.commit()
                        cursor.close()
                        return
                with deps.main_db as connect:
                    cursor = connect.cursor()
                    cursor.execute(f"""
                                   UPDATE roles
                                   SET {set_format}
                                   WHERE id = ?
                                   """, (arr))
                    connect.commit()
                    cursor.close()
            except Exception as e:
                logging.error(f'Ошибка в NewRole.addedit_role_information: {e}')