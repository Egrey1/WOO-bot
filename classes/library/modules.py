
import dependencies as deps
import logging
from typing import List, Tuple
import datetime as dt
from disnake import Role, Embed, Colour, Message
from disnake.ext.commands import Context

from sqlite3 import Connection as sql_Connection