from sqlite3 import Connection
from disnake.ext.commands import Bot
from disnake import Embed, Intents, Role
from typing import List, Tuple


bot: Bot
intents: Intents
PREFIX: tuple[str]
TOKEN: str

main_db: Connection

MAIN_CURRENCY_SYMVOL: str
MAIN_CURRENCY_ID: str

class Currency:
    """"""
    def __init__(self, id_: int | str) -> None:
        """"""
    
    @classmethod
    def all(cls) -> List['Currency']: # type: ignore
        """"""
    
    @classmethod
    def create(cls):
        """"""
        
    def edit(self, name: str):
        """"""

class Resource:
    """"""
    def __init__(self, id_: int | str):
        """"""
    
    @classmethod
    def all(cls) -> List['Resource']:  # type: ignore
        """"""
    
    @classmethod
    def create(cls):
        """"""
    
    def edit(self, name: str):
        """"""

class ShopItem:
    """"""
    def __init__(self, id_: int | str):
        """"""
    
    @classmethod
    def create(cls,
               name: str,
               description: str,
               cost: int,
               required_role: Role | int,
               currency: str | int) -> List['ShopItem']: # type: ignore
        """"""

    def edit(self, 
                name: str | None = None, 
                description: str | None = None, 
                cost: int | None = None, 
                required_role: Role | int | None = None, 
                currency: str | None = None):
        """"""
    
    def get_embed(self) -> Embed: # type: ignore
        """"""
    
    def get_embed_field_params(self) -> Tuple[str, str]: # type: ignore
        """"""

class _UserBalance:
    pass
class _UserResources:
    pass