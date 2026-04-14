from ..library import deps, logging, List, Role

class NotFound(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class Currency:
    def __init__(self, id_: int | str):
        try:
            with deps.main_db as connect:
                cursor = connect.cursor()
                cursor.execute("""
                               SELECT *
                               FROM currencies
                               WHERE id = ?
                               """, (id_, ))
                fetch = cursor.fetchone()
                cursor.close()
                if not fetch:
                    raise NotFound
                self.id = id_
                self.name = fetch['name']
        except Exception as e:
            logging.error(f'Ошибка в Currency.init: {e}')
    
    @classmethod
    def all(cls) -> List['Currency']:
        try:
            with deps.main_db as connect:
                cursor = connect.cursor()
                cursor.execute("""
                               SELECT id
                               FROM currencies
                               """)
                fetches = cursor.fetchall()
                cursor.close()
                result = []
                for fetch in fetches:
                    result.append(cls(fetch['id']))
                return result
        except Exception as e:
            logging.error(f'Ошибка в Currency.all: {e}')
            return []
    
    def addedit(self, name: str):
        try:
            with deps.main_db as connect:
                cursor = connect.cursor()
                cursor.execute("""
                               INSERT OR REPLACE INTO currencies (id, name)
                               VALUES (?, ?)
                               """, (self.id, name))
        except Exception as e:
            logging.error(f'Ошибка в Currency.addedit: {e}')
        

class Resource:
    def __init__(self, id_: int | str):
        try:
            with deps.main_db as connect:
                cursor = connect.cursor()
                cursor.execute("""
                               SELECT *
                               FROM resources
                               WHERE id = ?
                               """, (id_, ))
                fetch = cursor.fetchone()
                cursor.close()
                if not fetch:
                    raise NotFound
                self.id = id_
                self.name = fetch['name']
        except Exception as e:
            logging.error(f'Ошибка в Resource.init: {e}')
    
    @classmethod
    def all(cls) -> List['Resource']:
        try:
            with deps.main_db as connect:
                cursor = connect.cursor()
                cursor.execute("""
                               SELECT id
                               FROM resources
                               """)
                fetches = cursor.fetchall()
                cursor.close()
                result = []
                for fetch in fetches:
                    result.append(cls(fetch['id']))
                return result
        except Exception as e:
            logging.error(f'Ошибка в Resource.all: {e}')
            return []
    
    def addedit(self, name: str):
        try:
            with deps.main_db as connect:
                cursor = connect.cursor()
                cursor.execute("""
                               INSERT OR REPLACE INTO resources (id, name)
                               VALUES (?, ?)
                               """, (self.id, name))
        except Exception as e:
            logging.error(f'Ошибка в Resource.addedit: {e}')

class ShopItem:
    def __init__(self, id_: int | str):
        try:
            with deps.main_db as connect:
                cursor = connect.cursor()
                cursor.execute("""
                               SELECT *
                               FROM shop
                               WHERE id = ?
                               """, (id_, ))
                fetch = cursor.fetchone()
                cursor.close()
                if not fetch:
                    raise NotFound
                self.id = id_
                self.name               = str(fetch['name'])
                self.description        = str(fetch['description'])
                self.cost               = int(fetch['cost'])
                self.required_role_id   = int(fetch['required_role'])
                self.currency           = Currency(fetch['currency'])
        except Exception as e:
            logging.error(f'Ошибка в ShopItem.init: {e}')
    
    @classmethod
    def all(cls) -> List['ShopItem']:
        try:
            with deps.main_db as connect:
                cursor = connect.cursor()
                cursor.execute("""
                               SELECT id
                               FROM shop
                               """)
                fetches = cursor.fetchall()
                cursor.close()
                result = []
                for fetch in fetches:
                    result.append(cls(fetch['id']))
                return result
        except Exception as e:
            logging.error(f'Ошибка в ShopItem.all: {e}')
            return []
    
    def addedit(self, 
                name: str | None = None, 
                description: str | None = None, 
                cost: int | None = None, 
                required_role_id: Role | int | None = None, 
                currency: str | None = None):
        required_role_id = required_role_id.id if isinstance(required_role_id, Role) else required_role_id
        try:
            with deps.main_db as connect:
                cursor = connect.cursor()
                if all([name, description, cost, required_role_id, currency]):
                    cursor.execute("""
                                   INSERT OR REPLACE INTO resources (id, name, description, cost, required_role, currency)
                                   VALUES (?, ?, ?, ?, ?, ?)
                                   """, (self.id, name, description, cost, required_role_id, currency))
                else:
                    arr = [
                        'name' if name else None,
                        'description' if description else None,
                        'cost' if cost else None,
                        'required_role' if required_role_id else None,
                        'currency' if currency else None
                    ]
                    set_format = ','.join([f'{n} = ?' for n in arr if n is not None])
                    arr = [name, description, cost, required_role_id, currency]
                    arr = tuple([i for i in arr if i is not None] + [self.id])
                    cursor.execute(f"""
                                   UPDATE shop
                                   SET {set_format}
                                   WHERE id = ?
                                   """, (arr))
        except Exception as e:
            logging.error(f'Ошибка в Resource.addedit: {e}')