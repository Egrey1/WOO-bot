import dependencies as deps
from os import listdir

for foldername in listdir('./cogs'):
    deps.bot.load_extension(f'cogs.{foldername}')