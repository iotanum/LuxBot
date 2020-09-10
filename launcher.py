import os

from dotenv import load_dotenv
from discord.ext import commands

load_dotenv(dotenv_path="secrets.env")

DISCORD_API_KEY = os.getenv("discord_api")

bot = commands.Bot(command_prefix=os.getenv("command_prefix"))

initial_extensions = ['cogs.command_error_handler',
                      'cogs.background_task']


if __name__ == '__main__':
    for extension in initial_extensions:
        try:
            bot.load_extension(extension)

        except Exception as e:
            print(e)
            print(f'Failed to load extension "{extension}"')

    bot.run(DISCORD_API_KEY, bot=True, reconnect=True)
