from __future__ import annotations

from collections.abc import Iterator, MutableMapping
import datetime as dt

from ..library import deps, logging, Role, Embed, sql_Connection


class NotFound(LookupError):
    def __init__(self, object_name: str, object_id: int | str) -> None:
        super().__init__(f'{object_name} с идентификатором {object_id} не найден')


def _require_connection() -> sql_Connection:
    connection = getattr(deps, 'main_db', None)
    if connection is None:
        raise RuntimeError('База данных не инициализирована')
    return connection


def _normalize_role_id(role: Role | int | None) -> int | None:
    if isinstance(role, Role):
        return role.id
    return role


class _BaseEntity:
    table_name: str = ''

    @classmethod
    def _fetch_one(cls, query: str, params: tuple[object, ...]):
        with _require_connection() as connect:
            cursor = connect.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            cursor.close()
        return row

    @classmethod
    def _fetch_all(cls, query: str, params: tuple[object, ...] = ()):
        with _require_connection() as connect:
            cursor = connect.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
        return rows


class Currency(_BaseEntity):
    """"""

    table_name = 'currencies'

    def __init__(self, id_: int | str) -> None:
        row = self._fetch_one(
            """
            SELECT *
            FROM currencies
            WHERE id = ?
            """,
            (id_,),
        )
        if row is None:
            raise NotFound('Валюта', id_)

        self.id = int(row['id'])
        self.name = str(row['name'])
        self.symbol = row['symbol']
        self.is_main = bool(row['is_main'])
        self.created_at = str(row['created_at'])
        self.updated_at = str(row['updated_at'])

    @classmethod
    def all(cls) -> list['Currency']:
        """"""

        rows = cls._fetch_all(
            """
            SELECT id
            FROM currencies
            ORDER BY id
            """
        )
        return [cls(row['id']) for row in rows]

    @classmethod
    def create(
        cls,
        name: str,
        symbol: str | None = None,
        is_main: bool = False,
    ) -> 'Currency':
        """"""

        with _require_connection() as connect:
            cursor = connect.cursor()
            if is_main:
                cursor.execute(
                    """
                    UPDATE currencies
                    SET is_main = 0,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE is_main = 1
                    """
                )
            cursor.execute(
                """
                INSERT INTO currencies (name, symbol, is_main)
                VALUES (?, ?, ?)
                """,
                (name, symbol, int(is_main)),
            )
            created_id = cursor.lastrowid
            connect.commit()
            cursor.close()
        return cls(created_id) # type: ignore

    def edit(
        self,
        name: str | None = None,
        symbol: str | None = None,
        is_main: bool | None = None,
    ) -> None:
        """"""

        updates: list[str] = []
        params: list[object] = []

        if name is not None:
            updates.append('name = ?')
            params.append(name)
        if symbol is not None:
            updates.append('symbol = ?')
            params.append(symbol)

        with _require_connection() as connect:
            cursor = connect.cursor()
            if is_main is not None:
                if is_main:
                    cursor.execute(
                        """
                        UPDATE currencies
                        SET is_main = 0,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE is_main = 1 AND id != ?
                        """,
                        (self.id,),
                    )
                updates.append('is_main = ?')
                params.append(int(is_main))

            if not updates:
                cursor.close()
                return

            updates.append('updated_at = CURRENT_TIMESTAMP')
            params.append(self.id)
            cursor.execute(
                f"""
                UPDATE currencies
                SET {', '.join(updates)}
                WHERE id = ?
                """,
                tuple(params),
            )
            connect.commit()
            cursor.close()

        self.__init__(self.id)


class Resource(_BaseEntity):
    """"""

    table_name = 'resources'

    def __init__(self, id_: int | str) -> None:
        row = self._fetch_one(
            """
            SELECT *
            FROM resources
            WHERE id = ?
            """,
            (id_,),
        )
        if row is None:
            raise NotFound('Ресурс', id_)

        self.id = int(row['id'])
        self.name = str(row['name'])
        self.description = row['description']
        self.emoji = row['emoji']
        self.created_at = str(row['created_at'])
        self.updated_at = str(row['updated_at'])

    @classmethod
    def all(cls) -> list['Resource']:
        """"""

        rows = cls._fetch_all(
            """
            SELECT id
            FROM resources
            ORDER BY id
            """
        )
        return [cls(row['id']) for row in rows]

    @classmethod
    def create(
        cls,
        name: str,
        description: str | None = None,
        emoji: str | None = None,
    ) -> 'Resource':
        """"""

        with _require_connection() as connect:
            cursor = connect.cursor()
            cursor.execute(
                """
                INSERT INTO resources (name, description, emoji)
                VALUES (?, ?, ?)
                """,
                (name, description, emoji),
            )
            created_id = cursor.lastrowid
            connect.commit()
            cursor.close()
        return cls(created_id) # type: ignore

    def edit(
        self,
        name: str | None = None,
        description: str | None = None,
        emoji: str | None = None,
    ) -> None:
        """"""

        updates: list[str] = []
        params: list[object] = []

        if name is not None:
            updates.append('name = ?')
            params.append(name)
        if description is not None:
            updates.append('description = ?')
            params.append(description)
        if emoji is not None:
            updates.append('emoji = ?')
            params.append(emoji)

        if not updates:
            return

        updates.append('updated_at = CURRENT_TIMESTAMP')
        params.append(self.id)

        with _require_connection() as connect:
            cursor = connect.cursor()
            cursor.execute(
                f"""
                UPDATE resources
                SET {', '.join(updates)}
                WHERE id = ?
                """,
                tuple(params),
            )
            connect.commit()
            cursor.close()

        self.__init__(self.id)


class ShopItem(_BaseEntity):
    """"""

    table_name = 'shop_items'

    def __init__(self, id_: int | str) -> None:
        row = self._fetch_one(
            """
            SELECT *
            FROM shop_items
            WHERE id = ?
            """,
            (id_,),
        )
        if row is None:
            raise NotFound('Предмет магазина', id_)

        self.id = int(row['id'])
        self.name = str(row['name'])
        self.description = row['description']
        self.cost_amount = int(row['cost_amount'])
        self.cost_currency_id = int(row['cost_currency_id'])
        self.required_role_id = row['required_role_id']
        self.stock = row['stock']
        self.is_active = bool(row['is_active'])
        self.created_at = str(row['created_at'])
        self.updated_at = str(row['updated_at'])
        self.currency = Currency(self.cost_currency_id)

    @classmethod
    def all(cls, active_only: bool = False) -> list['ShopItem']:
        """"""

        query = """
        SELECT id
        FROM shop_items
        """
        params: tuple[object, ...] = ()
        if active_only:
            query += "WHERE is_active = 1 "
        query += "ORDER BY id"
        rows = cls._fetch_all(query, params)
        return [cls(row['id']) for row in rows]

    @classmethod
    def create(
        cls,
        name: str,
        description: str,
        cost: int,
        required_role: Role | int | None,
        currency: str | int,
        stock: int | None = None,
        is_active: bool = True,
    ) -> 'ShopItem':
        """"""

        currency_id = currency.id if isinstance(currency, Currency) else int(currency)
        role_id = _normalize_role_id(required_role)

        with _require_connection() as connect:
            cursor = connect.cursor()
            cursor.execute(
                """
                INSERT INTO shop_items (
                    name,
                    description,
                    cost_amount,
                    cost_currency_id,
                    required_role_id,
                    stock,
                    is_active
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (name, description, cost, currency_id, role_id, stock, int(is_active)),
            )
            created_id = cursor.lastrowid
            connect.commit()
            cursor.close()
        return cls(created_id) # type: ignore

    def edit(
        self,
        name: str | None = None,
        description: str | None = None,
        cost: int | None = None,
        required_role: Role | int | None = None,
        currency: str | int | None = None,
        stock: int | None = None,
        is_active: bool | None = None,
    ) -> None:
        """"""

        updates: list[str] = []
        params: list[object] = []

        if name is not None:
            updates.append('name = ?')
            params.append(name)
        if description is not None:
            updates.append('description = ?')
            params.append(description)
        if cost is not None:
            updates.append('cost_amount = ?')
            params.append(cost)
        if required_role is not None:
            updates.append('required_role_id = ?')
            params.append(_normalize_role_id(required_role))
        if currency is not None:
            currency_id = currency.id if isinstance(currency, Currency) else int(currency)
            updates.append('cost_currency_id = ?')
            params.append(currency_id)
        if stock is not None:
            updates.append('stock = ?')
            params.append(stock)
        if is_active is not None:
            updates.append('is_active = ?')
            params.append(int(is_active))

        if not updates:
            return

        updates.append('updated_at = CURRENT_TIMESTAMP')
        params.append(self.id)

        with _require_connection() as connect:
            cursor = connect.cursor()
            cursor.execute(
                f"""
                UPDATE shop_items
                SET {', '.join(updates)}
                WHERE id = ?
                """,
                tuple(params),
            )
            connect.commit()
            cursor.close()

        self.__init__(self.id)

    def get_embed(self) -> Embed:
        """"""

        price = f'{self.cost_amount}{self.currency.symbol or ""}'
        embed = Embed(title=f'{self.name} - {price}', description=self.description or '')
        if self.required_role_id is not None:
            embed.add_field(name='Требуемая роль', value=f'<@&{self.required_role_id}>', inline=False)
        if self.stock is not None:
            embed.add_field(name='Остаток', value=str(self.stock), inline=False)
        return embed

    def get_embed_field_params(self) -> tuple[str, str]:
        """"""

        description = self.description or ''
        if len(description) <= 200:
            return self.name, description
        return self.name, description[:197] + '...'


class InventoryItem(_BaseEntity):
    """"""

    table_name = 'user_inventory'

    def __init__(self, user_id: int | str, shop_item_id: int | str) -> None:
        row = self._fetch_one(
            """
            SELECT *
            FROM user_inventory
            WHERE user_id = ? AND shop_item_id = ?
            """,
            (user_id, shop_item_id),
        )
        if row is None:
            raise NotFound('Предмет инвентаря', f'{user_id}:{shop_item_id}')

        self.user_id = int(row['user_id'])
        self.shop_item_id = int(row['shop_item_id'])
        self.amount = int(row['amount'])
        self.updated_at = str(row['updated_at'])
        self.item = ShopItem(self.shop_item_id)

    @classmethod
    def all_for_user(cls, user_id: int | str) -> list['InventoryItem']:
        """"""

        rows = cls._fetch_all(
            """
            SELECT user_id, shop_item_id
            FROM user_inventory
            WHERE user_id = ?
            ORDER BY shop_item_id
            """,
            (user_id,),
        )
        return [cls(row['user_id'], row['shop_item_id']) for row in rows]

    @classmethod
    def create(
        cls,
        user_id: int,
        shop_item: ShopItem | int,
        amount: int = 1,
    ) -> 'InventoryItem':
        """"""

        if amount < 0:
            raise ValueError('Количество предметов не может быть отрицательным')

        shop_item_id = shop_item.id if isinstance(shop_item, ShopItem) else int(shop_item)
        with _require_connection() as connect:
            cursor = connect.cursor()
            cursor.execute(
                """
                INSERT INTO user_inventory (user_id, shop_item_id, amount)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, shop_item_id)
                DO UPDATE SET
                    amount = excluded.amount,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (user_id, shop_item_id, amount),
            )
            connect.commit()
            cursor.close()
        return cls(user_id, shop_item_id)

    def edit(self, amount: int) -> None:
        """"""

        if amount < 0:
            raise ValueError('Количество предметов не может быть отрицательным')
        if amount == 0:
            self.delete()
            return

        with _require_connection() as connect:
            cursor = connect.cursor()
            cursor.execute(
                """
                UPDATE user_inventory
                SET amount = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND shop_item_id = ?
                """,
                (amount, self.user_id, self.shop_item_id),
            )
            connect.commit()
            cursor.close()

        self.__init__(self.user_id, self.shop_item_id)

    def delete(self) -> None:
        """"""

        with _require_connection() as connect:
            cursor = connect.cursor()
            cursor.execute(
                """
                DELETE FROM user_inventory
                WHERE user_id = ? AND shop_item_id = ?
                """,
                (self.user_id, self.shop_item_id),
            )
            connect.commit()
            cursor.close()


class RoleIncome(_BaseEntity):
    """"""

    table_name = 'role_incomes'

    def __init__(self, id_: int | str) -> None:
        row = self._fetch_one(
            """
            SELECT *
            FROM role_incomes
            WHERE id = ?
            """,
            (id_,),
        )
        if row is None:
            raise NotFound('Доход роли', id_)

        self.id = int(row['id'])
        self.role_id = int(row['role_id'])
        self.cooldown_seconds = int(row['cooldown_seconds'])
        self.currency_id = row['currency_id']
        self.currency_amount = row['currency_amount']
        self.is_active = bool(row['is_active'])
        self.created_at = str(row['created_at'])
        self.updated_at = str(row['updated_at'])
        self.currency = Currency(self.currency_id) if self.currency_id is not None else None
        self.resources = self._load_resources()

    @classmethod
    def from_role(cls, role: Role | int) -> 'RoleIncome':
        """"""

        role_id = _normalize_role_id(role)
        row = cls._fetch_one(
            """
            SELECT id
            FROM role_incomes
            WHERE role_id = ?
            """,
            (role_id,),
        )
        if row is None:
            raise NotFound('Доход роли', role_id if role_id is not None else 'None')
        return cls(row['id'])

    @classmethod
    def all(cls, active_only: bool = False) -> list['RoleIncome']:
        """"""

        query = """
        SELECT id
        FROM role_incomes
        """
        if active_only:
            query += "WHERE is_active = 1 "
        query += "ORDER BY id"
        rows = cls._fetch_all(query)
        return [cls(row['id']) for row in rows]

    @classmethod
    def create(
        cls,
        role: Role | int,
        cooldown_seconds: int,
        currency: Currency | int | None = None,
        currency_amount: int | None = None,
        resources: list[tuple[int | str, int]] | None = None,
        is_active: bool = True,
    ) -> 'RoleIncome':
        """"""

        role_id = _normalize_role_id(role)
        if role_id is None:
            raise ValueError('Не удалось определить ID роли')
        if cooldown_seconds <= 0:
            raise ValueError('Кулдаун должен быть больше нуля')
        if currency is None and not resources:
            raise ValueError('Нужно указать валюту или хотя бы один ресурс')

        currency_id = None
        if currency is not None:
            currency_id = currency.id if isinstance(currency, Currency) else int(currency)

        with _require_connection() as connect:
            cursor = connect.cursor()
            cursor.execute(
                """
                INSERT INTO role_incomes (
                    role_id,
                    cooldown_seconds,
                    currency_id,
                    currency_amount,
                    is_active
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (role_id, cooldown_seconds, currency_id, currency_amount, int(is_active)),
            )
            created_id = cursor.lastrowid

            if resources:
                cursor.executemany(
                    """
                    INSERT INTO role_income_resources (role_income_id, resource_id, amount)
                    VALUES (?, ?, ?)
                    """,
                    [
                        (created_id, int(resource_id), int(amount))
                        for resource_id, amount in resources
                    ],
                )

            connect.commit()
            cursor.close()

        return cls(created_id)  # type: ignore

    def _load_resources(self) -> list[tuple[Resource, int]]:
        rows = self._fetch_all(
            """
            SELECT resource_id, amount
            FROM role_income_resources
            WHERE role_income_id = ?
            ORDER BY id
            """,
            (self.id,),
        )
        return [(Resource(row['resource_id']), int(row['amount'])) for row in rows]

    def edit(
        self,
        cooldown_seconds: int | None = None,
        currency: Currency | int | None = None,
        currency_amount: int | None = None,
        resources: list[tuple[int | str, int]] | None = None,
        is_active: bool | None = None,
    ) -> None:
        """"""

        updates: list[str] = []
        params: list[object] = []

        if cooldown_seconds is not None:
            if cooldown_seconds <= 0:
                raise ValueError('Кулдаун должен быть больше нуля')
            updates.append('cooldown_seconds = ?')
            params.append(cooldown_seconds)
        if currency is not None:
            currency_id = currency.id if isinstance(currency, Currency) else int(currency)
            updates.append('currency_id = ?')
            params.append(currency_id)
        if currency_amount is not None:
            updates.append('currency_amount = ?')
            params.append(currency_amount)
        if is_active is not None:
            updates.append('is_active = ?')
            params.append(int(is_active))

        with _require_connection() as connect:
            cursor = connect.cursor()
            if updates:
                updates.append('updated_at = CURRENT_TIMESTAMP')
                params.append(self.id)
                cursor.execute(
                    f"""
                    UPDATE role_incomes
                    SET {', '.join(updates)}
                    WHERE id = ?
                    """,
                    tuple(params),
                )

            if resources is not None:
                cursor.execute(
                    """
                    DELETE FROM role_income_resources
                    WHERE role_income_id = ?
                    """,
                    (self.id,),
                )
                if resources:
                    cursor.executemany(
                        """
                        INSERT INTO role_income_resources (role_income_id, resource_id, amount)
                        VALUES (?, ?, ?)
                        """,
                        [
                            (self.id, int(resource_id), int(amount))
                            for resource_id, amount in resources
                        ],
                    )

            connect.commit()
            cursor.close()

        self.__init__(self.id)

    def get_last_claim_at(self, user_id: int) -> dt.datetime | None:
        """"""

        row = self._fetch_one(
            """
            SELECT last_claim_at
            FROM role_income_claims
            WHERE role_income_id = ? AND user_id = ?
            """,
            (self.id, user_id),
        )
        if row is None:
            return None
        return dt.datetime.fromisoformat(str(row['last_claim_at']))

    def set_last_claim_at(self, user_id: int, last_claim_at: dt.datetime | str) -> None:
        """"""

        normalized = last_claim_at.isoformat() if isinstance(last_claim_at, dt.datetime) else last_claim_at
        with _require_connection() as connect:
            cursor = connect.cursor()
            cursor.execute(
                """
                INSERT INTO role_income_claims (role_income_id, user_id, last_claim_at)
                VALUES (?, ?, ?)
                ON CONFLICT(role_income_id, user_id)
                DO UPDATE SET
                    last_claim_at = excluded.last_claim_at
                """,
                (self.id, user_id, normalized),
            )
            connect.commit()
            cursor.close()


class _UserEntityMap(MutableMapping[int, int]):
    table_name: str = ''
    key_column: str = ''
    value_factory = staticmethod(int)

    def __init__(self, id_: int | str):
        self.id = int(id_)
        self._dict: dict[int, int] = {}
        self._reload()

    def _reload(self) -> None:
        rows = _BaseEntity._fetch_all(
            f"""
            SELECT {self.key_column}, amount
            FROM {self.table_name}
            WHERE user_id = ?
            ORDER BY {self.key_column}
            """,
            (self.id,),
        )
        self._dict = {int(row[self.key_column]): int(row['amount']) for row in rows}

    def __getitem__(self, key: int | str) -> int:
        return self._dict[int(key)]

    def __setitem__(self, key: int | str, value: int) -> None:
        normalized_key = int(key)
        normalized_value = int(value)

        with _require_connection() as connect:
            cursor = connect.cursor()
            cursor.execute(
                f"""
                INSERT INTO {self.table_name} (user_id, {self.key_column}, amount)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, {self.key_column})
                DO UPDATE SET
                    amount = excluded.amount,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (self.id, normalized_key, normalized_value),
            )
            connect.commit()
            cursor.close()

        self._dict[normalized_key] = normalized_value

    def __delitem__(self, key: int | str) -> None:
        normalized_key = int(key)
        with _require_connection() as connect:
            cursor = connect.cursor()
            cursor.execute(
                f"""
                DELETE FROM {self.table_name}
                WHERE user_id = ? AND {self.key_column} = ?
                """,
                (self.id, normalized_key),
            )
            connect.commit()
            cursor.close()

        del self._dict[normalized_key]

    def __iter__(self) -> Iterator[int]:
        return iter(self._dict)

    def __len__(self) -> int:
        return len(self._dict)

    def get_objects(self) -> list[tuple[object, int]]:
        raise NotImplementedError


class _UserBalance(_UserEntityMap):
    """"""

    table_name = 'user_balances'
    key_column = 'currency_id'

    def get_objects(self) -> list[tuple[Currency, int]]:
        """"""

        return [(Currency(currency_id), amount) for currency_id, amount in self._dict.items()]


class _UserResources(_UserEntityMap):
    """"""

    table_name = 'user_resources'
    key_column = 'resource_id'

    def get_objects(self) -> list[tuple[Resource, int]]:
        """"""

        return [(Resource(resource_id), amount) for resource_id, amount in self._dict.items()]


class _UserInventory(_UserEntityMap):
    """"""

    table_name = 'user_inventory'
    key_column = 'shop_item_id'

    def __setitem__(self, key: int | str, value: int) -> None:
        if int(value) < 0:
            raise ValueError('Количество предметов не может быть отрицательным')
        if int(value) == 0:
            if int(key) in self._dict:
                self.__delitem__(key)
            return
        super().__setitem__(key, value)

    def get_objects(self) -> list[tuple[ShopItem, int]]:
        """"""

        return [(ShopItem(shop_item_id), amount) for shop_item_id, amount in self._dict.items()]

    def get_entries(self) -> list[InventoryItem]:
        """"""

        return [InventoryItem(self.id, shop_item_id) for shop_item_id in self._dict]
