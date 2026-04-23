from sqlite3 import Connection
from disnake.ext.commands import Bot
from disnake import Component, Embed, Intents, Member, Role, User
from typing import List, Tuple
import datetime as dt
from disnake.ui import Components, ActionRow

bot: Bot
intents: Intents
PREFIX: tuple[str]
TOKEN: str
VERSION: str

rights: Connection
"""
Подключение к SQLite-базе данных `rights.db`.

База данных используется для хранения прав ролей на пользование ботом.

Схема таблиц:
    `rights`
        Основная таблица. Формат записи всех полей: f'{Role.id};{Role.id}'...
        Поля:
            `manage_items TEXT`
                Право на управление предметами. Их редактирование, удаление и создание
            `manage_rincomes TEXT`
                Право на управление заработком ролей. Их редактирование, удаление и создание
            `manage_resources TEXT`
                Право на управление ресурсами. Их редактирование, удаление и создание
            `administrator TEXT`
                Все права выше и дополнительно позволяет назначать другие роли на другие права
"""

main_db: Connection
"""
Главное подключение к SQLite-базе данных `main.db`.

База данных используется как единое хранилище экономической системы бота.
В проекте предполагается работа только с одним Discord-сервером, поэтому
отдельная таблица серверов не используется.

Схема таблиц:
    `users`
        Хранит пользователей, которых уже видел бот.
        Поля:
            `id INTEGER PRIMARY KEY`
                Discord ID пользователя.
            `username TEXT`
                Имя пользователя на момент сохранения.
            `display_name TEXT`
                Отображаемое имя пользователя на момент сохранения.
            `created_at TEXT`
                Дата создания записи. Формат: `YYYY-MM-DD HH:MM:SS`.
            `updated_at TEXT`
                Дата последнего обновления записи. Формат: `YYYY-MM-DD HH:MM:SS`.

    `currencies`
        Хранит доступные валюты сервера.
        Поля:
            `id INTEGER PRIMARY KEY AUTOINCREMENT`
                Внутренний идентификатор валюты.
            `name TEXT UNIQUE`
                Уникальное имя валюты.
            `symbol TEXT`
                Символ валюты для отображения.
            `is_main INTEGER`
                Флаг основной валюты. Обычно `0` или `1`.
            `created_at TEXT`
                Время создания записи.
            `updated_at TEXT`
                Время последнего обновления записи.

    `resources`
        Хранит ресурсы, которые не являются валютой.
        Поля:
            `id INTEGER PRIMARY KEY AUTOINCREMENT`
                Внутренний идентификатор ресурса.
            `name TEXT UNIQUE`
                Уникальное имя ресурса.
            `description TEXT`
                Краткое описание ресурса.
            `emoji TEXT`
                Символ или emoji для отображения в сообщениях.
            `created_at TEXT`
                Время создания записи.
            `updated_at TEXT`
                Время последнего обновления записи.

    `user_balances`
        Хранит количество каждой валюты у каждого пользователя.
        Поля:
            `id INTEGER PRIMARY KEY AUTOINCREMENT`
                Идентификатор строки.
            `user_id INTEGER`
                Ссылка на `users.id`.
            `currency_id INTEGER`
                Ссылка на `currencies.id`.
            `amount INTEGER`
                Количество валюты у пользователя.
            `updated_at TEXT`
                Время последнего изменения значения.
        Формат хранения:
            одна строка = одна валюта у одного пользователя.

    `user_resources`
        Хранит количество каждого ресурса у каждого пользователя.
        Поля:
            `id INTEGER PRIMARY KEY AUTOINCREMENT`
                Идентификатор строки.
            `user_id INTEGER`
                Ссылка на `users.id`.
            `resource_id INTEGER`
                Ссылка на `resources.id`.
            `amount INTEGER`
                Количество ресурса у пользователя.
            `updated_at TEXT`
                Время последнего изменения значения.
        Формат хранения:
            одна строка = один ресурс у одного пользователя.

    `shop_items`
        Хранит предметы магазина.
        Поля:
            `id INTEGER PRIMARY KEY AUTOINCREMENT`
                Внутренний идентификатор предмета.
            `name TEXT UNIQUE`
                Название предмета.
            `description TEXT`
                Описание предмета.
            `cost_amount INTEGER`
                Цена предмета в выбранной валюте.
            `cost_currency_id INTEGER`
                Ссылка на `currencies.id`.
            `required_role_id INTEGER`
                Discord ID роли, необходимой для покупки. Может быть `NULL`.
            `stock INTEGER`
                Остаток предмета. `NULL` означает бесконечный запас.
            `is_active INTEGER`
                Флаг активности предмета. Обычно `0` или `1`.
            `created_at TEXT`
                Время создания записи.
            `updated_at TEXT`
                Время последнего обновления записи.

    `user_inventory`
        Хранит предметы, принадлежащие пользователям.
        Поля:
            `id INTEGER PRIMARY KEY AUTOINCREMENT`
                Идентификатор строки.
            `user_id INTEGER`
                Ссылка на `users.id`.
            `shop_item_id INTEGER`
                Ссылка на `shop_items.id`.
            `amount INTEGER`
                Количество одинаковых предметов у пользователя.
            `updated_at TEXT`
                Время последнего изменения записи.
        Формат хранения:
            одна строка = один предмет магазина у одного пользователя.

    `role_incomes`
        Хранит роли, которые позволяют получать доход по кулдауну.
        Поля:
            `id INTEGER PRIMARY KEY AUTOINCREMENT`
                Внутренний идентификатор настройки дохода.
            `role_id INTEGER UNIQUE`
                Discord ID роли.
            `cooldown_seconds INTEGER`
                Кулдаун между сборами в секундах.
            `currency_id INTEGER`
                Ссылка на `currencies.id`. Может быть `NULL`, если роль не выдает валюту.
            `currency_amount INTEGER`
                Размер валютной награды. Может быть `NULL`.
            `is_active INTEGER`
                Флаг активности записи. Обычно `0` или `1`.
            `created_at TEXT`
                Время создания записи.
            `updated_at TEXT`
                Время последнего обновления записи.

    `role_income_resources`
        Хранит ресурсы, которые дополнительно выдает доходная роль.
        Поля:
            `id INTEGER PRIMARY KEY AUTOINCREMENT`
                Идентификатор строки.
            `role_income_id INTEGER`
                Ссылка на `role_incomes.id`.
            `resource_id INTEGER`
                Ссылка на `resources.id`.
            `amount INTEGER`
                Количество ресурса за один сбор.
        Формат хранения:
            одна строка = один ресурс в награде одной роли.

    `role_income_claims`
        Хранит информацию о последнем сборе дохода пользователем.
        Поля:
            `id INTEGER PRIMARY KEY AUTOINCREMENT`
                Идентификатор строки.
            `role_income_id INTEGER`
                Ссылка на `role_incomes.id`.
            `user_id INTEGER`
                Ссылка на `users.id`.
            `last_claim_at TEXT`
                Момент последнего сбора в ISO-формате:
                `YYYY-MM-DDTHH:MM:SS` или `YYYY-MM-DDTHH:MM:SS.mmmmmm`.
        Формат хранения:
            одна строка = один пользователь для одной доходной роли.

Заметки:
    - Для работы с `main_db` проект использует `sqlite3.Row`, поэтому строки БД
      читаются по именам колонок.
    - Объекты из `classes/objects/game_objects.py` уже знают, в какие таблицы
      обращаться, поэтому в основной логике чаще всего не нужен прямой SQL.
    - Для корректной работы связей в SQLite желательно включать
      `PRAGMA foreign_keys = ON`.
"""

MAIN_CURRENCY_SYMVOL: str
MAIN_CURRENCY_ID: int

class Rights:
    """
    Объект доступа к таблице `rights` из базы `rights.db`.

    Назначение:
        Хранит и управляет списками Discord ID ролей для заранее определенных
        прав доступа бота.

    Поля экземпляра:
        `manage_items: list[int]`
            Роли, которым разрешено управлять предметами магазина.
        `manage_rincomes: list[int]`
            Роли, которым разрешено управлять доходными ролями.
        `manage_resources: list[int]`
            Роли, которым разрешено управлять ресурсами.
        `administrator: list[int]`
            Роли с полными административными правами.
        `fields: tuple[str, ...]`
            Набор поддерживаемых названий полей.

    Используемая база:
        `rights.db`

    Используемая таблица:
        `rights`

    Формат хранения:
        Каждое поле хранится как строка вида
        `role_id;role_id;role_id`.
    """
    manage_items: list[int]
    manage_rincomes: list[int]
    manage_resources: list[int]
    administrator: list[int]
    fields: tuple[str, ...]

    def __init__(self) -> None:
        """
        Загружает текущие списки ролей из таблицы `rights`.

        Возвращает:
            `None`

        Исключения:
            `RuntimeError`
                Если подключение к `rights.db` не настроено или запись не удалось загрузить.
        """

    def get(self, field: str) -> list[int]: # type: ignore
        """
        Возвращает список ролей для указанного поля прав.

        Параметры:
            `field: str`
                Имя поля. Например: `manage_items`.

        Возвращает:
            `list[int]`
                Список Discord ID ролей.

        Исключения:
            `ValueError`
                Если поле не поддерживается.
        """

    def add(self, field: str, role_id: int) -> list[int]: # type: ignore
        """
        Добавляет роль в выбранное поле прав.

        Параметры:
            `field: str`
                Имя поля прав.
            `role_id: int`
                Discord ID роли.

        Возвращает:
            `list[int]`
                Обновленный список ролей.
        """

    def remove(self, field: str, role_id: int) -> list[int]: # type: ignore
        """
        Удаляет роль из выбранного поля прав.

        Параметры:
            `field: str`
                Имя поля прав.
            `role_id: int`
                Discord ID роли.

        Возвращает:
            `list[int]`
                Обновленный список ролей.
        """

    def set(self, field: str, role_ids: list[int] | tuple[int, ...]) -> list[int]: # type: ignore
        """
        Полностью заменяет список ролей в выбранном поле прав.

        Параметры:
            `field: str`
                Имя поля прав.
            `role_ids: list[int] | tuple[int, ...]`
                Новый полный список Discord ID ролей.

        Возвращает:
            `list[int]`
                Новый сохраненный список ролей.
        """

    def get_manage_items(self) -> list[int]: # type: ignore
        """Возвращает список ролей из поля `manage_items`."""

    def add_manage_items(self, role_id: int) -> list[int]: # type: ignore
        """Добавляет роль в поле `manage_items`."""

    def remove_manage_items(self, role_id: int) -> list[int]: # type: ignore
        """Удаляет роль из поля `manage_items`."""

    def set_manage_items(self, role_ids: list[int] | tuple[int, ...]) -> list[int]: # type: ignore
        """Полностью заменяет поле `manage_items`."""

    def get_manage_rincomes(self) -> list[int]: # type: ignore
        """Возвращает список ролей из поля `manage_rincomes`."""

    def add_manage_rincomes(self, role_id: int) -> list[int]: # type: ignore
        """Добавляет роль в поле `manage_rincomes`."""

    def remove_manage_rincomes(self, role_id: int) -> list[int]: # type: ignore
        """Удаляет роль из поля `manage_rincomes`."""

    def set_manage_rincomes(self, role_ids: list[int] | tuple[int, ...]) -> list[int]: # type: ignore
        """Полностью заменяет поле `manage_rincomes`."""

    def get_manage_resources(self) -> list[int]: # type: ignore
        """Возвращает список ролей из поля `manage_resources`."""

    def add_manage_resources(self, role_id: int) -> list[int]: # type: ignore
        """Добавляет роль в поле `manage_resources`."""

    def remove_manage_resources(self, role_id: int) -> list[int]: # type: ignore
        """Удаляет роль из поля `manage_resources`."""

    def set_manage_resources(self, role_ids: list[int] | tuple[int, ...]) -> list[int]: # type: ignore
        """Полностью заменяет поле `manage_resources`."""

    def get_administrator(self) -> list[int]: # type: ignore
        """Возвращает список ролей из поля `administrator`."""

    def add_administrator(self, role_id: int) -> list[int]: # type: ignore
        """Добавляет роль в поле `administrator`."""

    def remove_administrator(self, role_id: int) -> list[int]: # type: ignore
        """Удаляет роль из поля `administrator`."""

    def set_administrator(self, role_ids: list[int] | tuple[int, ...]) -> list[int]: # type: ignore
        """Полностью заменяет поле `administrator`."""

    def is_manage_items(self, user: Member | User) -> bool: # type: ignore
        """Проверяет, имеет ли права user на управление предметами магазина"""
    
    def is_manage_rincomes(self, user: Member | User) -> bool: # type: ignore
        """Проверяет, имеет ли права user на управление ролями для заработка"""
    
    def is_manage_resources(self, user: Member | User) -> bool: # type: ignore
        """Проверяет, имеет ли права user на управление ресурсами"""
    
    def is_administrator(self, user: Member | User) -> bool: # type: ignore
        """Проверяет, имеет ли права user на управление другими ролями"""


class Currency:
    """
    Объект валюты сервера.

    Поля экземпляра:
        `id: int`
            Идентификатор валюты из таблицы `currencies`.
        `name: str`
            Название валюты.
        `symbol: str | None`
            Символ валюты для отображения.
        `is_main: bool`
            Является ли валюта основной.
        `created_at: str`
            Время создания записи в БД.
        `updated_at: str`
            Время последнего обновления записи.

    Используемая таблица:
        `currencies`

    Исключения:
        `LookupError`
            Если валюта с указанным ID не найдена.
        `RuntimeError`
            Если база данных еще не инициализирована.
        `sqlite3.Error`
            Возможны ошибки БД при создании или изменении.
    """
    id: int
    name: str
    symbol: str | None
    is_main: bool
    created_at: str
    updated_at: str
    amount: int | None

    def __init__(self, id_: int | str) -> None:
        """
        Загружает валюту из БД по ее идентификатору.

        Параметры:
            `id_: int | str`
                Идентификатор валюты в таблице `currencies`.

        Возвращает:
            `None`

        Исключения:
            `LookupError`
                Если валюта с таким ID не существует.
            `RuntimeError`
                Если соединение с БД не настроено.
        """
    
    @classmethod
    def all(cls) -> List['Currency']: # type: ignore
        """
        Возвращает список всех валют из таблицы `currencies`.

        Параметры:
            отсутствуют.

        Возвращает:
            `list[Currency]`
                Все валюты, отсортированные по `id`.

        Исключения:
            `RuntimeError`
                Если соединение с БД не настроено.
        """
    
    @classmethod
    def create(cls, name: str, symbol: str | None = None, is_main: bool = False) -> 'Currency': # type: ignore
        """
        Создает новую валюту и возвращает загруженный объект.

        Параметры:
            `name: str`
                Название новой валюты. Должно быть уникальным.
            `symbol: str | None = None`
                Символ валюты для отображения.
            `is_main: bool = False`
                Нужно ли сделать валюту основной.

        Возвращает:
            `Currency`
                Только что созданная валюта.

        Исключения:
            `sqlite3.IntegrityError`
                Если нарушена уникальность имени.
            `RuntimeError`
                Если соединение с БД не настроено.

        Заметки:
            Если `is_main=True`, у остальных валют флаг `is_main` будет сброшен.
        """
        
    def edit(self, name: str | None = None, symbol: str | None = None, is_main: bool | None = None):
        """
        Обновляет поля текущей валюты и перезагружает объект из БД.

        Параметры:
            `name: str | None = None`
                Новое имя валюты.
            `symbol: str | None = None`
                Новый символ валюты.
            `is_main: bool | None = None`
                Новый статус основной валюты.

        Возвращает:
            `None`

        Исключения:
            `sqlite3.Error`
                Возможны ошибки при обновлении записи.
            `RuntimeError`
                Если соединение с БД не настроено.

        Заметки:
            Если все параметры равны `None`, метод ничего не делает.
        """

    def __int__(self) -> int: # type: ignore
        """
        Возвращает `amount`, если объект используется как числовое значение.

        Возвращает:
            `int`
                Количество валюты, связанное с объектом.

        Заметки:
            Если `amount` не задан, возвращается `0`.
        """

    def __str__(self) -> str: # type: ignore
        """
        Возвращает строковое представление объекта.

        Возвращает:
            `str`
                Количество валюты, если заполнен `amount`, иначе название валюты.
        """

    def __iadd__(self, value: int) -> 'Currency': # type: ignore
        """
        Увеличивает `amount` внутри объекта валюты.

        Параметры:
            `value: int`
                Насколько увеличить количество.

        Возвращает:
            `Currency`
                Тот же объект с обновленным `amount`.
        """

    def __isub__(self, value: int) -> 'Currency': # type: ignore
        """
        Уменьшает `amount` внутри объекта валюты.

        Параметры:
            `value: int`
                Насколько уменьшить количество.

        Возвращает:
            `Currency`
                Тот же объект с обновленным `amount`.
        """

class Resource:
    """
    Объект ресурса сервера.

    Attributes:
        id: int
            Идентификатор ресурса из таблицы `resources`.
        name: str
            Название ресурса.
        description: str | None
            Описание ресурса.
        emoji: str | None
            Emoji или текстовый символ ресурса.
        created_at: str
            Время создания записи.
        updated_at: str
            Время последнего обновления записи.

    Используемая таблица:
        `resources`
    """
    id: int
    name: str
    description: str | None
    emoji: str | None
    created_at: str
    updated_at: str
    amount: int | None

    def __init__(self, id_: int | str):
        """
        Загружает ресурс из БД по идентификатору.

        Параметры:
            `id_: int | str`
                Идентификатор ресурса.

        Возвращает:
            `None`

        Исключения:
            `LookupError`
                Если ресурс не найден.
            `RuntimeError`
                Если соединение с БД не настроено.
        """
    
    @classmethod
    def all(cls) -> List['Resource']:  # type: ignore
        """
        Возвращает список всех ресурсов.

        Параметры:
            отсутствуют.

        Возвращает:
            `list[Resource]`
                Все ресурсы, отсортированные по `id`.
        """
    
    @classmethod
    def create(cls, name: str, description: str | None = None, emoji: str | None = None) -> 'Resource': # type: ignore
        """
        Создает новый ресурс и возвращает его объект.

        Параметры:
            `name: str`
                Название ресурса. Должно быть уникальным.
            `description: str | None = None`
                Описание ресурса.
            `emoji: str | None = None`
                Emoji или символ ресурса.

        Возвращает:
            `Resource`
                Созданный ресурс.

        Исключения:
            `sqlite3.IntegrityError`
                Если имя ресурса уже занято.
            `RuntimeError`
                Если соединение с БД не настроено.
        """
    
    def edit(self, name: str | None = None, description: str | None = None, emoji: str | None = None):
        """
        Обновляет текущий ресурс и перечитывает его из БД.

        Параметры:
            `name: str | None = None`
                Новое имя ресурса.
            `description: str | None = None`
                Новое описание ресурса.
            `emoji: str | None = None`
                Новый emoji или символ.

        Возвращает:
            `None`

        Заметки:
            Если все параметры равны `None`, метод ничего не делает.
        """

    def delete(self) -> None:
        """
        Полностью удаляет ресурс из базы данных и очищает все связанные записи.

        Возвращает:
            `None`

        Заметки:
            Удаляются связанные строки из:
            - `user_resources`
            - `role_income_resources`
            - `resources`
        """

    def __int__(self) -> int: # type: ignore
        """
        Возвращает `amount`, если объект используется как числовое значение.

        Возвращает:
            `int`
                Количество ресурса, связанное с объектом.

        Заметки:
            Если `amount` не задан, возвращается `0`.
        """

    def __str__(self) -> str: # type: ignore
        """
        Возвращает строковое представление объекта.

        Возвращает:
            `str`
                Количество ресурса, если заполнен `amount`, иначе имя ресурса.
        """

    def __iadd__(self, value: int) -> 'Resource': # type: ignore
        """
        Увеличивает `amount` внутри объекта ресурса.

        Параметры:
            `value: int`
                Насколько увеличить количество.

        Возвращает:
            `Resource`
                Тот же объект с обновленным `amount`.
        """

    def __isub__(self, value: int) -> 'Resource': # type: ignore
        """
        Уменьшает `amount` внутри объекта ресурса.

        Параметры:
            `value: int`
                Насколько уменьшить количество.

        Возвращает:
            `Resource`
                Тот же объект с обновленным `amount`.
        """

class ShopItem:
    """
    Объект предмета магазина.

    Поля экземпляра:
        `id: int`
            Идентификатор предмета из таблицы `shop_items`.
        `name: str`
            Название предмета.
        `description: str | None`
            Описание предмета.
        `cost_amount: int`
            Стоимость предмета.
        `cost_currency_id: int`
            ID валюты, в которой оплачивается предмет.
        `required_role_id: int | None`
            Discord ID роли, необходимой для покупки.
        `stock: int | None`
            Остаток на складе. `None` означает бесконечный запас.
        `is_active: bool`
            Доступен ли предмет в магазине.
        `created_at: str`
            Время создания записи.
        `updated_at: str`
            Время последнего изменения записи.
        `currency: Currency`
            Загруженный объект валюты стоимости.

    Используемая таблица:
        `shop_items`
    """
    id: int
    name: str
    description: str | None
    cost_amount: int
    cost_currency_id: int
    required_role_id: int | None
    stock: int | None
    is_active: bool
    created_at: str
    updated_at: str
    currency: Currency

    def __init__(self, id_: int | str):
        """
        Загружает предмет магазина по его ID.

        Параметры:
            `id_: int | str`
                Идентификатор предмета в таблице `shop_items`.

        Возвращает:
            `None`

        Исключения:
            `LookupError`
                Если предмет не найден.
            `RuntimeError`
                Если соединение с БД не настроено.
        """
    
    @classmethod
    def create(cls,
               name: str,
               description: str,
               cost: int,
               required_role: Role | int | None,
               currency: str | int,
               stock: int | None = None,
               is_active: bool = True) -> 'ShopItem': # type: ignore
        """
        Создает новый предмет магазина.

        Параметры:
            `name: str`
                Название предмета. Должно быть уникальным.
            `description: str`
                Описание предмета.
            `cost: int`
                Стоимость предмета.
            `required_role: Role | int | None`
                Роль, необходимая для покупки. Можно передать объект роли,
                ее Discord ID или `None`.
            `currency: str | int`
                Идентификатор валюты стоимости.
            `stock: int | None = None`
                Остаток предмета. `None` означает бесконечный запас.
            `is_active: bool = True`
                Будет ли предмет сразу доступен.

        Возвращает:
            `ShopItem`
                Созданный предмет магазина.

        Исключения:
            `sqlite3.IntegrityError`
                Если нарушена уникальность имени или ссылка на валюту.
            `RuntimeError`
                Если соединение с БД не настроено.
        """

    @classmethod
    def all(cls, active_only: bool = False) -> List['ShopItem']: # type: ignore
        """
        Возвращает список всех предметов магазина

        Params:
            active_only (bool): По умолчанию False. Нужно ли брать только активные предметы
        
        Returns:
            list[ShopItem]: Список всех предметов магазина

        """

    def edit(self, 
                name: str | None = None, 
                description: str | None = None, 
                cost: int | None = None, 
                required_role: Role | int | None = None, 
                currency: str | int | None = None,
                stock: int | None = None,
                is_active: bool | None = None):
        """
        Изменяет поля предмета магазина и перезагружает объект.

        Параметры:
            `name: str | None = None`
                Новое имя предмета.
            `description: str | None = None`
                Новое описание предмета.
            `cost: int | None = None`
                Новая стоимость.
            `required_role: Role | int | None = None`
                Новая требуемая роль.
            `currency: str | int | None = None`
                Новый ID валюты стоимости.
            `stock: int | None = None`
                Новый остаток.
            `is_active: bool | None = None`
                Новый флаг активности.

        Возвращает:
            `None`

        Заметки:
            Если все параметры равны `None`, метод ничего не делает.
        """
    
    def get_embed(self) -> Embed: # type: ignore
        """
        Собирает embed для показа предмета в Discord.

        Параметры:
            отсутствуют.

        Возвращает:
            `disnake.Embed`
                Готовый embed с названием, ценой, описанием и дополнительными полями.

        Заметки:
            Метод удобен для витрины магазина или детального просмотра предмета.
        """
    
    def get_embed_field_params(self) -> Tuple[str, str]: # type: ignore
        """
        Возвращает сокращенную пару значений для `Embed.add_field`.

        Параметры:
            отсутствуют.

        Возвращает:
            `tuple[str, str]`
                Кортеж вида `(название, сокращенное описание)`.

        Заметки:
            Описание автоматически обрезается примерно до 200 символов.
        """

    def delete(self) -> None:
        """
        Полностью удаляет предмет магазина и очищает все связанные записи.

        Возвращает:
            `None`

        Заметки:
            Удаляются связанные строки из:
            - `user_inventory`
            - `shop_items`
        """

    def get_v2component(self, moderator_mode: bool = False) -> list[Components | ActionRow]:
        """
        Возвращает набор компонентов для визуального отображения предмета в UI.

        Метод предназначен для поддержки новой версии клиентского интерфейса,
        где предметы магазина отображаются через составные UI-компоненты.

        Параметры:
            отсутствуют.

        Возвращает:
            `list[object]`
                Список компонент, необходимых для рендеринга предмета в
                новой версии интерфейса.

        Заметки:
            Реализация обычно строит визуальный блок с названием, ценой,
            описанием и кнопкой покупки.
        """
        raise NotImplementedError

    def get_container(self) -> Components:
        """
        Возвращает контейнер UI, описывающий предмет магазина.

        Контейнер служит для компактного отображения информации о предметах
        в интерфейсе: название, цена, описание, требуемая роль и остаток.

        Параметры:
            отсутствуют.

        Возвращает:
            `object`
                Объект контейнера UI для рендеринга предмета.

        Заметки:
            В зависимости от платформы реализация контейнера может базироваться
            на `disnake.ui.Container` или другой UI-структуре.
        """
        raise NotImplementedError

class InventoryItem:
    """
    Объект одной записи инвентаря пользователя.

    Поля экземпляра:
        `user_id: int`
            Discord ID владельца предмета.
        `shop_item_id: int`
            ID предмета из таблицы `shop_items`.
        `amount: int`
            Количество одинаковых предметов.
        `updated_at: str`
            Время последнего обновления записи.
        `item: ShopItem`
            Загруженный объект предмета магазина.

    Используемая таблица:
        `user_inventory`
    """
    user_id: int
    shop_item_id: int
    amount: int
    updated_at: str
    item: ShopItem

    def __init__(self, user_id: int | str, shop_item_id: int | str):
        """
        Загружает одну запись инвентаря пользователя.

        Параметры:
            `user_id: int | str`
                Discord ID пользователя.
            `shop_item_id: int | str`
                Идентификатор предмета магазина.

        Возвращает:
            `None`

        Исключения:
            `LookupError`
                Если запись инвентаря не найдена.
        """

    @classmethod
    def all_for_user(cls, user_id: int | str) -> List['InventoryItem']: # type: ignore
        """
        Возвращает все записи инвентаря конкретного пользователя.

        Параметры:
            `user_id: int | str`
                Discord ID пользователя.

        Возвращает:
            `list[InventoryItem]`
                Все найденные записи инвентаря пользователя.
        """

    @classmethod
    def create(cls, user_id: int, shop_item: ShopItem | int, amount: int = 1) -> 'InventoryItem': # type: ignore
        """
        Создает или обновляет запись инвентаря пользователя.

        Параметры:
            `user_id: int`
                Discord ID пользователя.
            `shop_item: ShopItem | int`
                Предмет магазина или его ID.
            `amount: int = 1`
                Итоговое количество предметов.

        Возвращает:
            `InventoryItem`
                Созданная или обновленная запись инвентаря.

        Исключения:
            `ValueError`
                Если количество отрицательное.
        """

    def edit(self, amount: int) -> None:
        """
        Обновляет количество предметов в инвентаре.

        Параметры:
            `amount: int`
                Новое количество предметов.

        Возвращает:
            `None`

        Исключения:
            `ValueError`
                Если количество отрицательное.

        Заметки:
            Если передать `0`, запись будет удалена из БД.
        """

    def delete(self) -> None:
        """
        Удаляет запись предмета из инвентаря пользователя.

        Возвращает:
            `None`
        """

    def __int__(self) -> int: # type: ignore
        """
        Возвращает количество предметов как число.

        Возвращает:
            `int`
                Значение поля `amount`.
        """

    def __str__(self) -> str: # type: ignore
        """
        Возвращает количество предметов как строку.

        Возвращает:
            `str`
                Строковое представление поля `amount`.
        """

    def __iadd__(self, value: int) -> 'InventoryItem': # type: ignore
        """
        Увеличивает `amount` внутри объекта записи инвентаря.

        Параметры:
            `value: int`
                Насколько увеличить количество.

        Возвращает:
            `InventoryItem`
                Тот же логический предмет с обновленным количеством.
        """

    def __isub__(self, value: int) -> 'InventoryItem': # type: ignore
        """
        Уменьшает `amount` внутри объекта записи инвентаря.

        Параметры:
            `value: int`
                Насколько уменьшить количество.

        Возвращает:
            `InventoryItem`
                Тот же логический предмет с обновленным количеством.
        """

class RoleIncome:
    """
    Объект доходной роли.

    Поля экземпляра:
        `id: int`
            Идентификатор записи в `role_incomes`.
        `role_id: int`
            Discord ID роли.
        `cooldown_seconds: int`
            Кулдаун между сборами в секундах.
        `currency_id: int | None`
            ID валюты награды.
        `currency_amount: int | None`
            Размер награды в валюте.
        `is_active: bool`
            Активна ли доходная роль.
        `created_at: str`
            Время создания записи.
        `updated_at: str`
            Время последнего обновления записи.
        `currency: Currency | None`
            Объект валюты награды, если она есть.
        `resources: list[tuple[Resource, int]]`
            Список ресурсов, которые выдает роль.

    Используемые таблицы:
        `role_incomes`
        `role_income_resources`
        `role_income_claims`
    """
    id: int
    role_id: int
    cooldown_seconds: int
    currency_id: int | None
    currency_amount: int | None
    is_active: bool
    created_at: str
    updated_at: str
    currency: Currency | None
    resources: List[Tuple[Resource, int]]

    def __init__(self, id_: int | str):
        """
        Загружает доходную роль по ID записи.

        Параметры:
            `id_: int | str`
                Идентификатор записи в `role_incomes`.

        Возвращает:
            `None`

        Исключения:
            `LookupError`
                Если запись не найдена.
            `RuntimeError`
                Если соединение с БД не настроено.
        """

    @classmethod
    def from_role(cls, role: Role | int) -> 'RoleIncome': # type: ignore
        """
        Ищет настройку дохода по Discord-роли.

        Параметры:
            `role: Role | int`
                Объект роли или ее Discord ID.

        Возвращает:
            `RoleIncome`
                Найденная доходная роль.

        Исключения:
            `LookupError`
                Если для роли еще не создан доход.
        """

    @classmethod
    def all(cls, active_only: bool = False) -> List['RoleIncome']: # type: ignore
        """
        Возвращает список всех доходных ролей.

        Параметры:
            `active_only: bool = False`
                Если `True`, будут возвращены только активные записи.

        Возвращает:
            `list[RoleIncome]`
                Все найденные доходные роли.
        """

    @classmethod
    def create(cls,
               role: Role | int,
               cooldown_seconds: int,
               currency: 'Currency | int | None' = None, # type: ignore
               currency_amount: int | None = None,
               resources: List[Tuple[int | str, int]] | None = None,
               is_active: bool = True) -> 'RoleIncome': # type: ignore
        """
        Создает новую настройку дохода для роли.

        Параметры:
            `role: Role | int`
                Объект Discord-роли или ее ID.
            `cooldown_seconds: int`
                Кулдаун между сборами в секундах.
            `currency: Currency | int | None = None`
                Валюта награды.
            `currency_amount: int | None = None`
                Размер награды в валюте.
            `resources: list[tuple[int | str, int]] | None = None`
                Дополнительные ресурсы награды в формате
                `(resource_id, amount)`.
            `is_active: bool = True`
                Должна ли роль сразу быть активной.

        Возвращает:
            `RoleIncome`
                Созданный объект доходной роли.

        Исключения:
            `ValueError`
                Если кулдаун меньше либо равен нулю, не удалось определить ID роли
                или не указана ни валюта, ни ресурсы.
            `sqlite3.IntegrityError`
                Если доход для роли уже существует.
        """

    def edit(self,
             cooldown_seconds: int | None = None,
             currency: 'Currency | int | None' = None, # type: ignore
             currency_amount: int | None = None,
             resources: List[Tuple[int | str, int]] | None = None,
             is_active: bool | None = None):
        """
        Изменяет доходную роль и, при необходимости, полностью заменяет список ресурсов.

        Параметры:
            `cooldown_seconds: int | None = None`
                Новый кулдаун в секундах.
            `currency: Currency | int | None = None`
                Новая валюта награды.
            `currency_amount: int | None = None`
                Новый размер валютной награды.
            `resources: list[tuple[int | str, int]] | None = None`
                Новый полный список ресурсов роли. Если передан список, старые
                ресурсы будут удалены и заменены.
            `is_active: bool | None = None`
                Новый флаг активности.

        Возвращает:
            `None`

        Исключения:
            `ValueError`
                Если `cooldown_seconds <= 0`.
        """

    def get_last_claim_at(self, user_id: int) -> dt.datetime or None: # type: ignore
        """
        Возвращает время последнего сбора дохода конкретным пользователем.

        Параметры:
            `user_id: int`
                Discord ID пользователя.

        Возвращает:
            `datetime | None`
                Время последнего сбора или `None`, если пользователь еще не собирал доход.

        Используемая таблица:
            `role_income_claims`
        """

    def set_last_claim_at(self, user_id: int, last_claim_at) -> None:
        """
        Создает или обновляет запись о последнем сборе дохода пользователем.

        Параметры:
            `user_id: int`
                Discord ID пользователя.
            `last_claim_at: datetime | str`
                Новый момент последнего сбора. Если передан `datetime`,
                он будет преобразован в ISO-строку.

        Возвращает:
            `None`

        Заметки:
            Метод использует upsert-логику: запись создается, если ее не было,
            и обновляется, если она уже существует.
        """

    def delete(self) -> None:
        """
        Полностью удаляет доходную роль и очищает все связанные записи.

        Возвращает:
            `None`

        Заметки:
            Удаляются связанные строки из:
            - `role_income_claims`
            - `role_income_resources`
            - `role_incomes`
        """
    
    def get_v2component(self, moderator_mode: bool = False) -> list[Component | ActionRow]: # type: ignore
        pass

class _UserBalance(dict[int, Currency]):
    """
    Словареподобная обертка над балансами пользователя.

    Назначение:
        Позволяет работать с балансами как с `dict`, где ключом является
        `currency_id`, а значением — количество валюты.

    Пример:
        `balance[1] += 100`

    Используемая таблица:
        `user_balances`

    Заметки:
        - Класс создается через `user.get_balance()`.
        - При изменении значения запись сразу сохраняется в БД.
        - Метод `get_objects()` в реальной реализации возвращает пары
          `(Currency, amount)`.
    """
    id: int
    _dict: dict[int, Currency]

    def __init__(self, id_: int | str) -> None:
        """
        Загружает балансы пользователя из таблицы `user_balances`.

        Параметры:
            `id_: int | str`
                Discord ID пользователя.

        Возвращает:
            `None`
        """

    def __getitem__(self, key: int | str) -> Currency: # type: ignore
        """
        Возвращает объект валюты по `currency_id`.

        Параметры:
            `key: int | str`
                Идентификатор валюты.

        Возвращает:
            `Currency`
                Объект валюты, у которого заполнено поле `amount`.

        Исключения:
            `KeyError`
                Если валюты нет в локальном словаре объекта.
        """

    def __setitem__(self, key: int | str, value: Currency | int) -> None:
        """
        Записывает новое количество валюты и сразу сохраняет его в БД.

        Параметры:
            `key: int | str`
                Идентификатор валюты.
            `value: Currency | int`
                Либо число, либо объект `Currency` с заполненным `amount`.

        Возвращает:
            `None`
        """

    def __delitem__(self, key: int | str) -> None:
        """
        Удаляет запись валюты пользователя из локального объекта и из БД.

        Параметры:
            `key: int | str`
                Идентификатор валюты.

        Возвращает:
            `None`
        """

    def __iter__(self):
        """
        Возвращает итератор по `currency_id`.
        """

    def __len__(self) -> int: # type: ignore
        """
        Возвращает количество валютных записей пользователя.
        """

    def get_objects(self) -> List[Currency]: # type: ignore
        """
        Возвращает список объектов валюты.

        Возвращает:
            `list[Currency]`
                Балансы пользователя в виде объектов валюты с заполненным `amount`.
        """

class _UserResources(dict[int, Resource]):
    """
    Словареподобная обертка над ресурсами пользователя.

    Назначение:
        Позволяет работать с ресурсами как с `dict`, где ключом является
        `resource_id`, а значением — количество ресурса.

    Пример:
        `resources[3] += 2`

    Используемая таблица:
        `user_resources`

    Заметки:
        - Класс создается через `user.get_resources()`.
        - При изменении значения запись сразу сохраняется в БД.
        - Метод `get_objects()` в реальной реализации возвращает пары
          `(Resource, amount)`.
    """
    id: int
    _dict: dict[int, Resource]

    def __init__(self, id_: int | str) -> None:
        """
        Загружает ресурсы пользователя из таблицы `user_resources`.

        Параметры:
            `id_: int | str`
                Discord ID пользователя.

        Возвращает:
            `None`
        """

    def __getitem__(self, key: int | str) -> Resource: # type: ignore
        """
        Возвращает объект ресурса по `resource_id`.

        Параметры:
            `key: int | str`
                Идентификатор ресурса.

        Возвращает:
            `Resource`
                Объект ресурса, у которого заполнено поле `amount`.

        Исключения:
            `KeyError`
                Если ресурса нет в локальном словаре объекта.
        """

    def __setitem__(self, key: int | str, value: Resource | int) -> None:
        """
        Записывает новое количество ресурса и сразу сохраняет его в БД.

        Параметры:
            `key: int | str`
                Идентификатор ресурса.
            `value: Resource | int`
                Либо число, либо объект `Resource` с заполненным `amount`.

        Возвращает:
            `None`
        """

    def __delitem__(self, key: int | str) -> None:
        """
        Удаляет запись ресурса пользователя из локального объекта и из БД.

        Параметры:
            `key: int | str`
                Идентификатор ресурса.

        Возвращает:
            `None`
        """

    def __iter__(self):
        """
        Возвращает итератор по `resource_id`.
        """

    def __len__(self) -> int: # type: ignore
        """
        Возвращает количество ресурсных записей пользователя.
        """

    def get_objects(self) -> List[Resource]: # type: ignore
        """
        Возвращает список объектов ресурса.

        Возвращает:
            `list[Resource]`
                Ресурсы пользователя в виде объектов с заполненным `amount`.
        """

class _UserInventory(dict[int, InventoryItem]):
    """
    Словареподобная обертка над инвентарем пользователя.

    Назначение:
        Позволяет работать с инвентарем как с `dict`, где ключом является
        `shop_item_id`, а значением — объект `InventoryItem`.

    Пример:
        `inventory[5] += 1`

    Используемая таблица:
        `user_inventory`

    Заметки:
        - Класс создается через `user.get_inventory()`.
        - При изменении значения запись сразу сохраняется в БД.
        - Метод `get_objects()` возвращает объекты `InventoryItem`.
        - Метод `get_entries()` возвращает объекты `InventoryItem`.
    """
    id: int
    _dict: dict[int, InventoryItem]

    def __init__(self, id_: int | str) -> None:
        """
        Загружает инвентарь пользователя из таблицы `user_inventory`.

        Параметры:
            `id_: int | str`
                Discord ID пользователя.

        Возвращает:
            `None`
        """

    def __getitem__(self, key: int | str) -> InventoryItem: # type: ignore
        """
        Возвращает объект предмета инвентаря по `shop_item_id`.

        Параметры:
            `key: int | str`
                Идентификатор предмета магазина.

        Возвращает:
            `InventoryItem`
                Объект записи инвентаря с заполненным `amount` и `item`.
        """

    def __setitem__(self, key: int | str, value: InventoryItem | int) -> None:
        """
        Записывает новое количество предметов и сразу сохраняет его в БД.

        Параметры:
            `key: int | str`
                Идентификатор предмета магазина.
            `value: InventoryItem | int`
                Либо число, либо объект `InventoryItem`.

        Возвращает:
            `None`

        Исключения:
            `ValueError`
                Если количество отрицательное.

        Заметки:
            Если передать `0`, запись будет удалена из инвентаря.
        """

    def __delitem__(self, key: int | str) -> None:
        """
        Удаляет запись предмета из инвентаря пользователя.

        Параметры:
            `key: int | str`
                Идентификатор предмета магазина.

        Возвращает:
            `None`
        """

    def __iter__(self):
        """
        Возвращает итератор по `shop_item_id`.
        """

    def __len__(self) -> int: # type: ignore
        """
        Возвращает количество разных предметов в инвентаре пользователя.
        """

    def get_objects(self) -> List[InventoryItem]: # type: ignore
        """
        Возвращает список объектов `InventoryItem`.

        Возвращает:
            `list[InventoryItem]`
                Инвентарь пользователя в виде объектов записей инвентаря.
        """

    def get_entries(self) -> List[InventoryItem]: # type: ignore
        """
        Возвращает полный список записей инвентаря в виде объектов `InventoryItem`.

        Возвращает:
            `list[InventoryItem]`
                Полные записи инвентаря пользователя.
        """
