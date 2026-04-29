import dependencies as deps
import disnake as ds
import disnake.user as ds_user
from disnake.ext.commands import Bot
from dotenv import load_dotenv
from os import getenv
import sqlite3 as sql
import logging
import classes as cls

def first_config():
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    deps.PREFIX = ('!', '! ')
    deps.bot = Bot(
        command_prefix=deps.PREFIX, 
        intents=ds.Intents.all(), 
        sync_commands=True, 
        allowed_mentions=ds.AllowedMentions.none(),
        help_command=None,
        strip_after_prefix=True
    )
    
    deps.TOKEN = getenv('TOKEN')
    deps.test_mode = bool(getenv('test_mode'))
    deps.MAIN_CURRENCY_ID = 1
    deps.VERSION = '2.14 Изменение интерфейса команды !bal, облегчение создания предметов' 
    
    deps.rights = sql.connect('databases2/rights.db', check_same_thread=False)
    deps.rights.row_factory = sql.Row
    deps.rights.execute('PRAGMA foreign_keys = ON')
    deps.main_db = cls.NewConnection('databases2/main.db', check_same_thread=False)
    deps.main_db.row_factory = sql.Row
    deps.main_db.execute('PRAGMA foreign_keys = ON')
    deps.MAIN_GUILD_ID = 1365405287007125666 if not deps.test_mode else 1051925846170030172
    cls.migrate_main_db()

    deps.Rights = cls.Rights
    deps.Resource = cls.Resource
    deps.Currency = cls.Currency
    deps.ShopItem = cls.ShopItem
    deps.InventoryItem = cls.InventoryItem
    deps.RoleIncome = cls.RoleIncome
    deps._UserBalance = cls._UserBalance
    deps._UserResources = cls._UserResources
    deps._UserInventory = cls._UserInventory


    ds.Role.get_role_information = cls.NewRole.get_role_information # type: ignore
    ds.Role.create_role_information = cls.NewRole.create_role_information  # type: ignore
    ds.Role.edit_role_information = cls.NewRole.edit_role_information # type: ignore

    ds_user._UserTag.get_balance = cls.NewUser.get_balance # type: ignore
    ds_user._UserTag.get_resources = cls.NewUser.get_resources # type: ignore
    ds_user._UserTag.get_inventory = cls.NewUser.get_inventory # type: ignore
    ds_user._UserTag.get_v2balance = cls.NewUser.get_v2balance # type: ignore
    

async def second_config():
    try:
        deps.main_guild = await deps.bot.fetch_guild(deps.MAIN_GUILD_ID)
    except:
        logging.warning('Основной сервер получить не удалось')
    import cogs as _
    logging.info(f'Бот успешно запущен как {deps.bot.user}')
    logging.info(f'Количество загруженных когов/расширений: {len(deps.bot.cogs)}')
    logging.info(f'Количество доступных команд: {len(deps.bot.all_commands)}')
    logging.info(f'Версия бота: {deps.VERSION}')
