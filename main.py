import logging
import dependencies as deps
import config

config.first_config()

@deps.bot.event
async def on_ready():
    await config.second_config()

if __name__ == "__main__":
    # deps.bot.run(deps.TOKEN)
    print(deps.bamount(1234567890))