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
    deps.PREFIX = ('&', '& ')
    deps.bot = Bot(command_prefix=deps.PREFIX, intents=ds.Intents.all())
    deps.TOKEN = getenv('TOKEN')

    deps.main_db = sql.connect('databases/main.db', check_same_thread=False)
    deps.main_db.row_factory = sql.Row

    deps.Resource = cls.Resource
    deps.Currency = cls.Currency
    deps.ShopItem = cls.ShopItem
    deps.RoleIncome = cls.RoleIncome
    deps._UserBalance = cls._UserBalance
    deps._UserResources = cls._UserResources
    
    
    sql.Connection.autocreate = cls.NewConnection.autocreate

    ds.Role.get_role_income = cls.NewRole.get_role_income # pyright: ignore[reportAttributeAccessIssue]
    ds.Role.get_role_information = cls.NewRole.get_role_information # pyright: ignore[reportAttributeAccessIssue]
    ds.Role.create_role_income = cls.NewRole.create_role_income # pyright: ignore[reportAttributeAccessIssue]
    ds.Role.edit_role_information = cls.NewRole.edit_role_information # pyright: ignore[reportAttributeAccessIssue]
    ds.Role.edit_role_income = cls.NewRole.edit_role_income # pyright: ignore[reportAttributeAccessIssue]

    ds_user._UserTag.get_balance = cls.NewUser.get_balance # pyright: ignore[reportAttributeAccessIssue]
    ds_user._UserTag.get_resources = cls.NewUser.get_resources # pyright: ignore[reportAttributeAccessIssue]
    

async def second_config():
    pass
