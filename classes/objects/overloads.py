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
        return deps._UserBalance(self.id) # type: ignore То же самое
    
    def get_resources(self) -> dict[str, int]:
        return deps._UserResources(self.id) # type: ignore То же самое

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
    
    def edit_role_information(
            self, 
            **kwargs
            ) -> None:  
            if isinstance(kwargs.get('cooldown', None), dt.time):
                kwargs['cooldown'] = kwargs['cooldown'].isoformat()
                
            kwargs['resources'] = ';'.join([f'{name}:{amount}' for name, amount in kwargs['resources']]) if kwargs['resources'] is not None else None 

            if not any(kwargs.values()):
                return



            arr = [name for name in kwargs.keys()]

            set_format = ','.join([f'{name} = ?' for name in [i for i in arr if i is not None]])
            
            arr = tuple([i for i in kwargs.values() if i is not None] + [self.id])
            try:
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
    
    def create_role_information(
            self, 
            cooldown: dt.time | str, 
            earning: int | str, 
            currency: str, 
            resources: List[Tuple[str, int]] | str 
        ) -> None:
        try:
            with deps.main_db as connect:
                cursor = connect.cursor()

                cursor.execute("""
                               INSERT INTO roles (id, cooldown, earning, currency, resources)
                               VALUES (?, ?, ?, ?, ?)
                               """, (self.id, cooldown, earning, currency, resources))
                connect.commit()
                cursor.close()
        except Exception as e: 
            logging.error(f'Ошибка в NewRole.create_role_information: {e}')
            raise e
        