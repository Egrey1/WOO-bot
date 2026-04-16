import logging

import dependencies as deps
from os import listdir

for foldername in listdir('./cogs'):
    if foldername[-3:] != '.py' and foldername[:2] != '__':
        deps.bot.load_extension(f'cogs.{foldername}')
        logging.info(f'Загружено расширение {foldername}')