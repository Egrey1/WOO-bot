from __future__ import annotations

from collections.abc import Iterator
import datetime as dt
from typing import Text

from ..library import deps, logging, Role, Embed, sql_Connection
from disnake import ButtonStyle, Member
import disnake.ui as ui


class NotFound(LookupError):
    def __init__(self, object_name: str, object_id: int | str) -> None:
        super().__init__(f'{object_name} с идентификатором {object_id} не найден')


def _require_connection() -> sql_Connection:
    connection = getattr(deps, 'main_db', None)
    if connection is None:
        raise RuntimeError('База данных не инициализирована')
    return connection


def _require_rights_connection() -> sql_Connection:
    connection = getattr(deps, 'rights', None)
    if connection is None:
        raise RuntimeError('База данных прав не инициализирована')
    return connection


def _normalize_role_id(role: Role | int | None) -> int | None:
    if isinstance(role, Role):
        return role.id
    return role if role != -1 else None


def _parse_tags(raw_value: str | None) -> list[str]:
    if not raw_value:
        return []
    return [tag for tag in raw_value.split(';') if tag]


def _serialize_tags(tags: list[str] | tuple[str, ...]) -> str:
    normalized: list[str] = []
    seen: set[str] = set()
    for raw_tag in tags:
        tag = str(raw_tag).strip()
        if not tag or tag in seen:
            continue
        normalized.append(tag)
        seen.add(tag)
    return ';'.join(normalized)


def _normalize_number(value: int | float) -> int | float:
    normalized = float(value)
    return int(normalized) if normalized.is_integer() else normalized


def _truncate_number(value: int | float) -> int:
    return int(float(value))


def _format_number(value: int | float | None) -> str:
    if value is None:
        return '0'
    return str(_normalize_number(value))


def migrate_main_db() -> None:
    connection = _require_connection()
    _enable_foreign_keys(connection)
    _migrate_role_incomes_table(connection)
    _migrate_user_balances_table(connection)


def _enable_foreign_keys(connection: sql_Connection) -> None:
    cursor = connection.cursor()
    cursor.execute('PRAGMA foreign_keys = ON')
    cursor.close()


def _migrate_role_incomes_table(connection: sql_Connection) -> None:
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT sql
        FROM sqlite_master
        WHERE type = 'table' AND name = 'role_incomes'
        """
    )
    row = cursor.fetchone()
    cursor.close()

    if row is None:
        return

    create_sql = str(row['sql'] or '').replace('"', '').replace(' ', '').lower()
    if 'currency_amount' not in create_sql or '>=0' not in create_sql:
        return

    cursor = connection.cursor()
    cursor.execute('PRAGMA foreign_keys = OFF')
    cursor.execute(
        """
        CREATE TABLE role_incomes__new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_id INTEGER NOT NULL UNIQUE,
            cooldown_seconds INTEGER NOT NULL CHECK (cooldown_seconds > 0),
            currency_id INTEGER,
            currency_amount REAL,
            is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
            tags TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (currency_id) REFERENCES currencies(id) ON DELETE SET NULL
        )
        """
    )

    cursor.execute("PRAGMA table_info(role_incomes)")
    existing_columns = {str(column['name']) for column in cursor.fetchall()}
    tags_select = "COALESCE(tags, '')" if 'tags' in existing_columns else "''"

    cursor.execute(
        f"""
        INSERT INTO role_incomes__new (
            id,
            role_id,
            cooldown_seconds,
            currency_id,
            currency_amount,
            is_active,
            tags,
            created_at,
            updated_at
        )
        SELECT
            id,
            role_id,
            cooldown_seconds,
            currency_id,
            currency_amount,
            is_active,
            {tags_select},
            created_at,
            updated_at
        FROM role_incomes
        """
    )
    cursor.execute("DROP TABLE role_incomes")
    cursor.execute("ALTER TABLE role_incomes__new RENAME TO role_incomes")
    cursor.execute('PRAGMA foreign_keys = ON')
    connection.commit()
    cursor.close()


def _migrate_user_balances_table(connection: sql_Connection) -> None:
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT sql
        FROM sqlite_master
        WHERE type = 'table' AND name = 'user_balances'
        """
    )
    row = cursor.fetchone()
    cursor.close()

    if row is None:
        return

    create_sql = str(row['sql'] or '').replace('"', '').replace(' ', '').lower()
    if 'amountintegernotnulldefault0check(amount>=0)' not in create_sql:
        return

    cursor = connection.cursor()
    cursor.execute('PRAGMA foreign_keys = OFF')
    cursor.execute(
        """
        CREATE TABLE user_balances__new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            currency_id INTEGER NOT NULL,
            amount INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (currency_id) REFERENCES currencies(id) ON DELETE CASCADE,
            UNIQUE (user_id, currency_id)
        )
        """
    )
    cursor.execute(
        """
        INSERT INTO user_balances__new (
            id,
            user_id,
            currency_id,
            amount,
            updated_at
        )
        SELECT
            id,
            user_id,
            currency_id,
            amount,
            updated_at
        FROM user_balances
        """
    )
    cursor.execute("DROP TABLE user_balances")
    cursor.execute("ALTER TABLE user_balances__new RENAME TO user_balances")
    cursor.execute('PRAGMA foreign_keys = ON')
    connection.commit()
    cursor.close()


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


class Rights:
    """"""

    fields = (
        'manage_items',
        'manage_rincomes',
        'manage_resources',
        'administrator',
    )

    def __init__(self) -> None:
        self._ensure_row()
        self._reload()

    @staticmethod
    def _parse(raw_value: str | None) -> list[int]:
        if not raw_value:
            return []
        return [int(role_id) for role_id in raw_value.split(';') if role_id]

    @staticmethod
    def _serialize(role_ids: list[int]) -> str:
        normalized = []
        seen: set[int] = set()
        for role_id in role_ids:
            normalized_id = int(role_id)
            if normalized_id not in seen:
                normalized.append(normalized_id)
                seen.add(normalized_id)
        return ';'.join(str(role_id) for role_id in normalized)

    def _ensure_row(self) -> None:
        with _require_rights_connection() as connect:
            cursor = connect.cursor()
            cursor.execute("SELECT COUNT(*) AS count FROM rights")
            count = int(cursor.fetchone()['count'])
            if count == 0:
                cursor.execute(
                    """
                    INSERT INTO rights (manage_items, manage_rincomes, manage_resources, administrator)
                    VALUES ('', '', '', '')
                    """
                )
                connect.commit()
            cursor.close()

    def _reload(self) -> None:
        with _require_rights_connection() as connect:
            cursor = connect.cursor()
            cursor.execute(
                """
                SELECT manage_items, manage_rincomes, manage_resources, administrator
                FROM rights
                LIMIT 1
                """
            )
            row = cursor.fetchone()
            cursor.close()

        if row is None:
            raise RuntimeError('Не удалось загрузить права из базы данных')

        for field in self.fields:
            setattr(self, field, self._parse(row[field]))

    def _validate_field(self, field: str) -> None:
        if field not in self.fields:
            raise ValueError(f'Неизвестное поле прав: {field}')

    def _save_field(self, field: str, role_ids: list[int]) -> list[int]:
        self._validate_field(field)
        serialized = self._serialize(role_ids)
        with _require_rights_connection() as connect:
            cursor = connect.cursor()
            cursor.execute(
                f"""
                UPDATE rights
                SET {field} = ?
                """,
                (serialized,),
            )
            connect.commit()
            cursor.close()

        parsed = self._parse(serialized)
        setattr(self, field, parsed)
        return parsed

    def get(self, field: str) -> list[int]:
        self._validate_field(field)
        return list(getattr(self, field))

    def add(self, field: str, role_id: int) -> list[int]:
        current = self.get(field)
        normalized_role_id = int(role_id)
        if normalized_role_id not in current:
            current.append(normalized_role_id)
        return self._save_field(field, current)

    def remove(self, field: str, role_id: int) -> list[int]:
        normalized_role_id = int(role_id)
        current = [saved_role_id for saved_role_id in self.get(field) if saved_role_id != normalized_role_id]
        return self._save_field(field, current)

    def set(self, field: str, role_ids: list[int] | tuple[int, ...]) -> list[int]:
        return self._save_field(field, [int(role_id) for role_id in role_ids])

    def get_manage_items(self) -> list[int]:
        return self.get('manage_items')

    def add_manage_items(self, role_id: int) -> list[int]:
        return self.add('manage_items', role_id)

    def remove_manage_items(self, role_id: int) -> list[int]:
        return self.remove('manage_items', role_id)

    def set_manage_items(self, role_ids: list[int] | tuple[int, ...]) -> list[int]:
        return self.set('manage_items', role_ids)

    def get_manage_rincomes(self) -> list[int]:
        return self.get('manage_rincomes')

    def add_manage_rincomes(self, role_id: int) -> list[int]:
        return self.add('manage_rincomes', role_id)

    def remove_manage_rincomes(self, role_id: int) -> list[int]:
        return self.remove('manage_rincomes', role_id)

    def set_manage_rincomes(self, role_ids: list[int] | tuple[int, ...]) -> list[int]:
        return self.set('manage_rincomes', role_ids)

    def get_manage_resources(self) -> list[int]:
        return self.get('manage_resources')

    def add_manage_resources(self, role_id: int) -> list[int]:
        return self.add('manage_resources', role_id)

    def remove_manage_resources(self, role_id: int) -> list[int]:
        return self.remove('manage_resources', role_id)

    def set_manage_resources(self, role_ids: list[int] | tuple[int, ...]) -> list[int]:
        return self.set('manage_resources', role_ids)

    def get_administrator(self) -> list[int]:
        return self.get('administrator')

    def add_administrator(self, role_id: int) -> list[int]:
        return self.add('administrator', role_id)

    def remove_administrator(self, role_id: int) -> list[int]:
        return self.remove('administrator', role_id)

    def set_administrator(self, role_ids: list[int] | tuple[int, ...]) -> list[int]:
        return self.set('administrator', role_ids)

    def is_manage_items(self, user: Member) -> bool:
        return any([role.id in self.get_manage_items() for role in user.roles])
    
    def is_manage_rincomes(self, user: Member) -> bool:
        return any([role.id in self.get_manage_rincomes() for role in user.roles])
    
    def is_manage_resources(self, user: Member) -> bool:
        return any([role.id in self.get_manage_resources() for role in user.roles])
    
    def is_administrator(self, user: Member) -> bool:
        return any([role.id in self.get_administrator() for role in user.roles])


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
        self.amount: int | float | None = None

    def __int__(self) -> int:
        return 0 if self.amount is None else int(float(self.amount))

    def __float__(self) -> float:
        return 0.0 if self.amount is None else float(self.amount)

    def __str__(self) -> str:
        return _format_number(self.amount) if self.amount is not None else self.name

    def _with_amount(self, amount: int | float) -> 'Currency':
        currency = Currency(self.id)
        currency.amount = _normalize_number(amount)
        return currency

    def __iadd__(self, value: int | float) -> 'Currency':
        return self._with_amount(_truncate_number(float(self) + float(value)))

    def __isub__(self, value: int | float) -> 'Currency':
        return self._with_amount(_truncate_number(float(self) - float(value)))

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
        self.amount: int | None = None

    def __int__(self) -> int:
        return 0 if self.amount is None else int(self.amount)

    def __str__(self) -> str:
        return str(self.amount) if self.amount is not None else self.name

    def _with_amount(self, amount: int) -> 'Resource':
        resource = Resource(self.id)
        resource.amount = amount
        return resource

    def __iadd__(self, value: int) -> 'Resource':
        return self._with_amount(int(self) + int(value))

    def __isub__(self, value: int) -> 'Resource':
        return self._with_amount(int(self) - int(value))

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

    def delete(self) -> None:
        """"""

        with _require_connection() as connect:
            cursor = connect.cursor()
            cursor.execute(
                """
                DELETE FROM user_resources
                WHERE resource_id = ?
                """,
                (self.id,),
            )
            cursor.execute(
                """
                DELETE FROM role_income_resources
                WHERE resource_id = ?
                """,
                (self.id,),
            )
            cursor.execute(
                """
                DELETE FROM resources
                WHERE id = ?
                """,
                (self.id,),
            )
            connect.commit()
            cursor.close()


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
        self.tags = _parse_tags(row['tags'])
        self.currency = Currency(self.cost_currency_id)
        self.buy_mode = False

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
        query += "ORDER BY cost_amount"
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
        tags: list[str] | tuple[str, ...] | None = None,
    ) -> 'ShopItem':
        """"""

        currency_id = currency.id if isinstance(currency, Currency) else int(currency)
        role_id = _normalize_role_id(required_role)
        serialized_tags = _serialize_tags(tags or [])

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
                    is_active,
                    tags
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (name, description, cost, currency_id, role_id, stock, int(is_active), serialized_tags),
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
        tags: list[str] | tuple[str, ...] | None = None,
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
        if tags is not None:
            updates.append('tags = ?')
            params.append(_serialize_tags(tags))

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

    def set_tags(self, tags: list[str] | tuple[str, ...]) -> list[str]:
        self.edit(tags=tags)
        return list(self.tags)

    def add_tag(self, tag: str) -> list[str]:
        updated_tags = list(self.tags)
        normalized_tag = str(tag).strip()
        if normalized_tag and normalized_tag not in updated_tags:
            updated_tags.append(normalized_tag)
            self.edit(tags=updated_tags)
        return list(self.tags)

    def remove_tag(self, tag: str) -> list[str]:
        normalized_tag = str(tag).strip()
        self.edit(tags=[saved_tag for saved_tag in self.tags if saved_tag != normalized_tag])
        return list(self.tags)

    def delete(self) -> None:
        """"""

        with _require_connection() as connect:
            cursor = connect.cursor()
            cursor.execute(
                """
                DELETE FROM user_inventory
                WHERE shop_item_id = ?
                """,
                (self.id,),
            )
            cursor.execute(
                """
                DELETE FROM shop_items
                WHERE id = ?
                """,
                (self.id,),
            )
            connect.commit()
            cursor.close()

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

    def get_v2component(self, moderator_mode: bool = False) -> list[ui.Container | ui.ActionRow]:
        if not moderator_mode:
            return [
                ui.Container(
                    ui.TextDisplay('## ' + self.name),
                    ui.Separator(),
                    ui.TextDisplay(self.description),
                    ui.Section(
                        ui.TextDisplay(f'Стоимость {self.cost_amount}{self.currency.symbol}'),
                        accessory=ui.Button(
                            label='Купить', 
                            style=ButtonStyle.green, 
                            custom_id=f'item_buy {self.id}',
                            emoji='🛒',
                            disabled= not self.is_active
                        )
                    ),
                    ui.TextDisplay(
                        f'Требуемая роль: <@&{self.required_role_id}>' if self.required_role_id is not None else 'Требуемая роль: Нет'
                    )
                )
            ]
        else:
            return [
                ui.Container(
                    ui.Section(
                        ui.TextDisplay('## ' + self.name),
                        accessory=ui.Button(
                            label='Изменить',
                            style=ButtonStyle.blurple,
                            custom_id=f'item_edit_name {self.id}',
                            emoji='⚙️'
                        )
                    ),
                    ui.Separator(),
                    ui.Section(
                        ui.TextDisplay(self.description),
                        accessory=ui.Button(
                            label='Изменить',
                            style=ButtonStyle.blurple,
                            custom_id=f'item_edit_description {self.id}',
                            emoji='⚙️'
                        )
                    ),
                    ui.Section(
                        ui.TextDisplay('Купить за ' + deps.bamount(self.cost_amount) + self.currency.symbol),
                        accessory=ui.Button(
                            label='Купить', 
                            style=ButtonStyle.green, 
                            custom_id=f'item_buy {self.id}',
                            emoji='🛒',
                            disabled= not self.is_active
                        )
                    ),
                    ui.TextDisplay(
                        f'Требуемая роль: <@&{self.required_role_id}>' if self.required_role_id is not None else 'Требуемая роль: Нет'
                    )
                ),
                ui.ActionRow(
                    ui.Button(
                        label='Изменить цену',
                        style=ButtonStyle.blurple,
                        custom_id=f'item_edit_price {self.id}',
                        emoji='⚙️'
                    ),
                    ui.Button(
                        label='Удалить',
                        style=ButtonStyle.danger,
                        custom_id=f'item_delete {self.id}',
                        emoji='🗑️'
                    )
                ),
                ui.ActionRow(
                    ui.RoleSelect(
                        placeholder='Изменить требуемую роль',
                        custom_id=f'item_edit_role {self.id}'
                    )
                )
            ]

    def get_container(self) -> ui.Container:
        return ui.Container(
            ui.TextDisplay('### ' + self.name),
            ui.Separator(),
            ui.TextDisplay(self.description if len(self.description[:256] + '...') <= 256 else self.description[:253] + '...'),
            ui.Section(
                ui.TextDisplay(f'Стоимость {self.cost_amount}{self.currency.symbol}'),
                accessory=ui.Button(
                    label='Купить', 
                    style=ButtonStyle.green, 
                    custom_id=f'item_buy {self.id}',
                    emoji='🛒',
                    disabled= not self.is_active
                )
            ),
            ui.TextDisplay(
                f'Требуемая роль: <@&{self.required_role_id}>' if self.required_role_id is not None else 'Требуемая роль: Нет'
            ),
            ui.Separator()
        )


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

    def __int__(self) -> int:
        return int(self.amount)

    def __str__(self) -> str:
        return str(self.amount)

    def _with_amount(self, amount: int) -> 'InventoryItem':
        entry = InventoryItem(self.user_id, self.shop_item_id)
        entry.amount = amount
        return entry

    def __iadd__(self, value: int | float) -> 'InventoryItem':
        return self._with_amount(self.amount + _truncate_number(value))

    def __isub__(self, value: int | float) -> 'InventoryItem':
        return self._with_amount(self.amount - _truncate_number(value))

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
        amount: int | float = 1,
    ) -> 'InventoryItem':
        """"""

        normalized_amount = _truncate_number(amount)
        if normalized_amount < 0:
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
                (user_id, shop_item_id, normalized_amount),
            )
            connect.commit()
            cursor.close()
        return cls(user_id, shop_item_id)

    def edit(self, amount: int | float) -> None:
        """"""

        normalized_amount = _truncate_number(amount)
        if normalized_amount < 0:
            raise ValueError('Количество предметов не может быть отрицательным')
        if normalized_amount == 0:
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
                (normalized_amount, self.user_id, self.shop_item_id),
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
        self.currency_amount = _normalize_number(row['currency_amount']) if row['currency_amount'] is not None else None
        self.is_active = bool(row['is_active'])
        self.created_at = str(row['created_at'])
        self.updated_at = str(row['updated_at'])
        self.tags = _parse_tags(row['tags'])
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
        currency_amount: int | float | None = None,
        resources: list[tuple[int | str, int]] | None = None,
        is_active: bool = True,
        tags: list[str] | tuple[str, ...] | None = None,
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
        serialized_tags = _serialize_tags(tags or [])

        with _require_connection() as connect:
            cursor = connect.cursor()
            cursor.execute(
                """
                INSERT INTO role_incomes (
                    role_id,
                    cooldown_seconds,
                    currency_id,
                    currency_amount,
                    is_active,
                    tags
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (role_id, cooldown_seconds, currency_id, _normalize_number(currency_amount) if currency_amount is not None else None, int(is_active), serialized_tags),
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
        currency_amount: int | float | None = None,
        resources: list[tuple[int | str, int]] | None = None,
        is_active: bool | None = None,
        tags: list[str] | tuple[str, ...] | None = None,
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
            params.append(_normalize_number(currency_amount))
        if is_active is not None:
            updates.append('is_active = ?')
            params.append(int(is_active))
        if tags is not None:
            updates.append('tags = ?')
            params.append(_serialize_tags(tags))

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

    def set_tags(self, tags: list[str] | tuple[str, ...]) -> list[str]:
        self.edit(tags=tags)
        return list(self.tags)

    def add_tag(self, tag: str) -> list[str]:
        updated_tags = list(self.tags)
        normalized_tag = str(tag).strip()
        if normalized_tag and normalized_tag not in updated_tags:
            updated_tags.append(normalized_tag)
            self.edit(tags=updated_tags)
        return list(self.tags)

    def remove_tag(self, tag: str) -> list[str]:
        normalized_tag = str(tag).strip()
        self.edit(tags=[saved_tag for saved_tag in self.tags if saved_tag != normalized_tag])
        return list(self.tags)

    def delete(self) -> None:
        """"""

        with _require_connection() as connect:
            cursor = connect.cursor()
            cursor.execute(
                """
                DELETE FROM role_income_claims
                WHERE role_income_id = ?
                """,
                (self.id,),
            )
            cursor.execute(
                """
                DELETE FROM role_income_resources
                WHERE role_income_id = ?
                """,
                (self.id,),
            )
            cursor.execute(
                """
                DELETE FROM role_incomes
                WHERE id = ?
                """,
                (self.id,),
            )
            connect.commit()
            cursor.close()

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

    def get_v2component(self, moderator_mode: bool = False):
        seconds = self.cooldown_seconds
        hours = seconds // 3600
        seconds -= hours * 3600
        minutes = seconds // 60
        seconds -= minutes * 60
        form_str = (str(hours) + (' часов ' if hours > 4 else ' часа ' if hours > 1 else ' час ')) if hours else ''
        form_str += (str(minutes) + (' минут ' if minutes > 4 else ' минуты ' if minutes > 1 else ' минута '))  if minutes else ''
        form_str += (str(seconds) + (' секунд ' if seconds > 4 else ' секунды ' if seconds > 1 else ' секунда ')) if seconds else '' if form_str else 'Нет'
        if self.currency:
            salary = deps.bamount(_format_number(self.currency_amount) )
            if not any( 'percentage' in tag for tag in self.tags):
                salary += self.currency.symbol or ''
            else: 
                salary += '%'
                    
        else:
            salary = (self.resources[0][0].name + ' x ' + str(self.resources[0][1]))
        if moderator_mode:
            return [
                ui.Container(
                    ui.TextDisplay('## <@&' + str(self.role_id) + '>'),
                    ui.Separator(),
                    ui.Section(
                        ui.TextDisplay(
                             'Кулдаун: ' + form_str
                        ),
                        accessory=ui.Button(
                            label='Изменить', 
                            style=ButtonStyle.blurple, 
                            custom_id=f'role_edit_cooldown {self.id}',
                            emoji='⚙️'
                        )
                    ),
                    ui.Section(
                        ui.TextDisplay(
                            f'Заработок: ' + salary
                        ),
                        accessory=ui.Button(
                            label='Изменить', 
                            style=ButtonStyle.blurple, 
                            custom_id=f'role_edit_income {self.id}',
                            emoji='⚙️'
                        )
                    ),
                    ui.Separator(),
                    ui.TextDisplay(
                        '-# ' + (', '.join(self.tags) if self.tags else 'Теги отсутствуют')
                    )
                ),
                ui.ActionRow(
                    ui.Button(
                        label='Удалить',
                        style=ButtonStyle.danger,
                        custom_id=f'role_delete {self.id}',
                        emoji='🗑️'
                    )
                ),
                ui.ActionRow(
                    ui.Button(
                        label='Добавить тег',
                        style=ButtonStyle.blurple,
                        custom_id=f'role_edit_add_tag {self.id}',
                        emoji='⚙️'
                    ),
                    ui.Button(
                        label='Удалить тег',
                        style=ButtonStyle.blurple,
                        custom_id=f'role_edit_remove_tag {self.id}',
                        emoji='⚙️'
                    )
                )
            ]

        return [
            ui.Container(
                ui.TextDisplay('## <@&' + str(self.role_id) + '>'),
                ui.Separator(),
                ui.TextDisplay('Кулдаун: ' + form_str),
                ui.TextDisplay(
                    f'Заработок: ' + salary
                ),
                ui.Separator(),
                ui.TextDisplay(
                    '-# ' + (', '.join(self.tags) if self.tags else 'Теги отсутствуют')
                )
            )
        ]


class _UserEntityMap(dict[int, object]):
    table_name: str = ''
    key_column: str = ''

    def __init__(self, id_: int | str):
        super().__init__()
        self.id = int(id_)
        self._reload()

    @property
    def _dict(self):
        return self

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
        super().clear()
        for row in rows:
            key = int(row[self.key_column])
            amount = _normalize_number(row['amount'])
            super().__setitem__(key, self._make_value(key, amount))

    def _make_value(self, key: int, amount: int | float):
        return amount

    def _normalize_value(self, value) -> int | float:
        return _normalize_number(value)

    def __getitem__(self, key: int | str):
        return super().__getitem__(int(key))

    def __setitem__(self, key: int | str, value) -> None:
        normalized_key = int(key)
        normalized_value = self._normalize_value(value)

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

        super().__setitem__(normalized_key, self._make_value(normalized_key, normalized_value))

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

        super().__delitem__(normalized_key)

    def __iter__(self) -> Iterator[int]:
        return super().__iter__()

    def __len__(self) -> int:
        return super().__len__()

    def clear(self) -> None:
        for key in list(self.keys()):
            self.__delitem__(key)

    def pop(self, key: int | str, default=...):
        normalized_key = int(key)
        if normalized_key not in self:
            if default is ...:
                raise KeyError(normalized_key)
            return default
        value = self[normalized_key]
        self.__delitem__(normalized_key)
        return value

    def popitem(self):
        if not self:
            raise KeyError('popitem(): dictionary is empty')
        key = next(iter(self))
        value = self[key]
        self.__delitem__(key)
        return key, value

    def setdefault(self, key: int | str, default=None):
        normalized_key = int(key)
        if normalized_key not in self:
            self[normalized_key] = 0 if default is None else default
        return self[normalized_key]

    def update(self, other=None, /, **kwargs) -> None:
        if other is not None:
            if hasattr(other, 'items'):
                for key, value in other.items():
                    self[key] = value
            else:
                for key, value in other:
                    self[key] = value

        for key, value in kwargs.items():
            self[key] = value

    def get_objects(self):
        raise NotImplementedError


class _UserBalance(_UserEntityMap):
    """"""

    table_name = 'user_balances'
    key_column = 'currency_id'

    def _make_value(self, key: int, amount: int | float) -> Currency:
        currency = Currency(key)
        currency.amount = amount
        return currency

    def _normalize_value(self, value: Currency | int | float) -> int:
        raw_value = value.amount if isinstance(value, Currency) and value.amount is not None else value
        return _truncate_number(raw_value) # type: ignore

    def get_objects(self) -> list[Currency]:
        """"""

        return list(self.values()) # type: ignore


class _UserResources(_UserEntityMap):
    """"""

    table_name = 'user_resources'
    key_column = 'resource_id'

    def _make_value(self, key: int, amount: int) -> Resource:
        resource = Resource(key)
        resource.amount = amount
        return resource

    def _normalize_value(self, value: Resource | int) -> int:
        return int(value.amount if isinstance(value, Resource) and value.amount is not None else value)

    def get_objects(self) -> list[Resource]:
        """"""

        return list(self.values()) # type: ignore


class _UserInventory(_UserEntityMap):
    """"""

    table_name = 'user_inventory'
    key_column = 'shop_item_id'

    def _make_value(self, key: int, amount: int) -> InventoryItem:
        entry = InventoryItem(self.id, key)
        entry.amount = amount
        return entry

    def _normalize_value(self, value: InventoryItem | int | float) -> int:
        return _truncate_number(value.amount if isinstance(value, InventoryItem) else value)

    def __setitem__(self, key: int | str, value: InventoryItem | int | float) -> None:
        normalized_value = self._normalize_value(value)
        if normalized_value < 0:
            raise ValueError('Количество предметов не может быть отрицательным')
        if normalized_value == 0:
            if int(key) in self._dict:
                self.__delitem__(key)
            return
        super().__setitem__(key, normalized_value)

    def get_objects(self) -> list[InventoryItem]:
        """"""

        return list(self.values()) # type: ignore

    def get_entries(self) -> list[InventoryItem]:
        """"""

        return list(self.values()) # type: ignore
