from sqlite3 import Connection
from disnake.ext.commands import Bot
from disnake import Intents


bot: Bot
intents: Intents
PREFIX: tuple[str]
TOKEN: str

main_db: Connection