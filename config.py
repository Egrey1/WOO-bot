import dependencies as deps
from disnake import Intents
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
    deps.bot = Bot(command_prefix=deps.PREFIX, intents=Intents.all())
    deps.TOKEN = getenv('TOKEN')

    deps.main_db = sql.connect('databases/main.db', check_same_thread=False)
    deps.main_db.row_factory = sql.Row
    
    sql.Connection.autocreate = cls.NewConnection.autocreate
    

async def second_config():
    pass
