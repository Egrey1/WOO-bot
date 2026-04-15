from ..library import deps, logging, List, Role, Embed, Tuple

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
    
    def edit(self, name: str):
        try:
            with deps.main_db as connect:
                cursor = connect.cursor()
                cursor.execute("""
                               INSERT OR REPLACE INTO currencies (id, name)
                               VALUES (?, ?)
                               """, (self.id, name))
        except Exception as e:
            logging.error(f'Ошибка в Currency.edit: {e}')
        

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
    
    @classmethod
    def create(cls, name: str):
        try:
            with deps.main_db as connect:
                cursor = connect.cursor()
                cursor.execute("""
                               INSERT OR IGNORE INTO resources (name)
                               VALUES (?)
                               """, (name))
                connect.commit()
                cursor.close()
        except Exception as e:
            logging.error(f'Ошибка в Resource.create: {e}')
            raise e
        
    def edit(self, name: str):
        try:
            with deps.main_db as connect:
                cursor = connect.cursor()
                cursor.execute("""
                               UPDATE resources 
                               SET name = ?
                               """, (self.id, name))
        except Exception as e:
            logging.error(f'Ошибка в Resource.edit: {e}')

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
    
    @classmethod
    def create(cls,
               name: str,
               description: str,
               cost: int,
               required_role: Role | int,
               currency: str | int):
        try:
            with deps.main_db as connect:
                cursor = connect.cursor()
                cursor.execute("""
                               INSERT INTO shop (name, description, cost, required_role, currency)
                               VALUES (?, ?, ?, ?, ?)
                               """, (name, description, cost, required_role, currency))
                connect.commit()
                cursor.close()
        except Exception as e:
            logging.error(f'Ошибка в ShopItem.create: {e}')
            raise e


    def edit(self, **kwargs):
        kwargs['required_role'] = kwargs.get('required_role', None).id if isinstance(kwargs.get('required_role', None), Role) else kwargs.get('required_role', None) # type: ignore
        try:
            with deps.main_db as connect:
                cursor = connect.cursor()
                arr = [name for name in kwargs.keys()]
                set_format = ','.join([f'{n} = ?' for n in arr if n is not None])
                arr = tuple([i for i in kwargs.values() if i is not None] + [self.id])
                cursor.execute(f"""
                                UPDATE shop
                                SET {set_format}
                                WHERE id = ?
                                """, (arr))
        except Exception as e:
            logging.error(f'Ошибка в Resource.edit: {e}')
    
    def get_embed(self) -> Embed:
        embed = Embed(title=f'{self.name} - {self.cost}{deps.MAIN_CURRENCY_ID}', description=self.description)
        embed.add_field('Требуеиые роли', f'<&{self.required_role_id}>', inline=False)
        return embed
    
    def get_embed_field_params(self) -> Tuple[str, str]:
        desc = self.description[:200]
        return (self.name, desc if desc == self.description[:200] else desc + '...')
        
    
class _UserBalance:
    def __init__(self, id_: int | str):
        self.id = id_
        self._dict: dict = {}
        try:
            with deps.main_db as connect:
                cursor = connect.cursor()
                cursor.execute("""
                               SELECT balance
                               FROM users
                               WHERE id = ?
                               """, (self.id, ))
                d = dict(cursor.fetchone())
                for name, amount in d.keys():
                    self._dict[name] = amount
                cursor.close()
        except Exception as e:
            logging.warning(f'Ошибка в UserBalance.init: {e}')
    
    def __getitem__(self, key: str | int):
        self._dict[key]

    def __setitem__(self, key: str | int, value: int):
        self._dict[key] = value
        set_string = ';'.join([f'{name}:{amount}' for name, amount in self._dict.items()])
        try:
            with deps.main_db as connect:
                cursor = connect.cursor()
                cursor.execute("""
                               UPDATE balance
                               SET balance = ?
                               WHERE id = ?
                               """, (set_string, self.id))
                connect.commit()
                cursor.close()
        except Exception as e:
            logging.error(f'Ошибка в UserBalance.setitem: {e}')
            raise e
    
    def __getattribute__(self, name: str):
        self._dict.__getattribute__(name)

class _UserResources:
    def __init__(self, id_: int | str):
        self.id = id_
        self._dict: dict = {}
        try:
            with deps.main_db as connect:
                cursor = connect.cursor()
                cursor.execute("""
                               SELECT resources
                               FROM users
                               WHERE id = ?
                               """, (self.id, ))
                d = dict(cursor.fetchone())
                for name, amount in d.keys():
                    self._dict[name] = amount
                cursor.close()
        except Exception as e:
            logging.warning(f'Ошибка в UserResources.init: {e}')
    
    def __getitem__(self, key: str | int):
        self._dict[key]
        
    def __setitem__(self, key: str | int, value: int):
        self._dict[key] = value
        set_string = ';'.join([f'{name}:{amount}' for name, amount in self._dict.items()])
        try:
            with deps.main_db as connect:
                cursor = connect.cursor()
                cursor.execute("""
                               UPDATE resources
                               SET resources = ?
                               WHERE id = ?
                               """, (set_string, self.id))
                connect.commit()
                cursor.close()
        except Exception as e:
            logging.error(f'Ошибка в UserResources.setitem: {e}')
            raise e
    
    def __getattribute__(self, name: str):
        self._dict.__getattribute__(name)
    