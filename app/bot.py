import asyncio
import os
import logging

import discord
from discord.ext import commands
from dotenv import load_dotenv
from sleeper_group import SleeperGroup
from tasks import SummaryTasks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()
TOKEN = os.environ["TOKEN"]

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(command_prefix="/", intents=intents)

    async def setup_hook(self):
        self.tree.add_command(SleeperGroup())

        await self.add_cog(SummaryTasks(self))

        await self.tree.sync()
        logger.info("Commands synced.")

    async def on_ready(self):
        logger.info(f"Logged in as {self.user}")

bot = MyBot()

async def main():
    await bot.start(TOKEN)

asyncio.run(main())
