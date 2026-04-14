import logging
import dependencies as deps
import config

config.first_config()

@deps.bot.event
async def on_ready():
    await config.second_config()


deps.bot.run(deps.TOKEN)