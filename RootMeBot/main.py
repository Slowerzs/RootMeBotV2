from dotenv import load_dotenv

import discord
import asyncio
from os import getenv

load_dotenv()

from database.manager import DatabaseManager
from notify.manager import NotificationManager
from api.fetch import *
from bot.rootme_bot import RootMeBot


TOKEN = getenv('DISCORD_TOKEN')
GUILD = getenv('DISCORD_GUILD')
CHANNEL = int(getenv('BOT_CHANNEL'))

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


async def main():
    rootme_api = ApiRootMe( )
    notification_manager = NotificationManager()
    db_manager = DatabaseManager(rootme_api, notification_manager)
    bot = RootMeBot(db_manager, notification_manager)
    rootme_api.bot = bot
    await bot.start(TOKEN, CHANNEL)
    


if __name__ == "__main__":
    asyncio.run(main())




