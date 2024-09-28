import json
import logging
import discord
import config
import os
from config import GUILD, GUILD_ID
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone, timedelta
from dateutil.parser import parse
from secret import TOKEN, TOKEN_TEST, USE_TEST_BOT

INTENTS = discord.Intents.all()
COGS = [cog[:-3] for cog in os.listdir("cogs/") if cog.endswith(".py")]

class JackInTheBox(commands.Bot):
    """Jack In The Box."""
    def __init__(self, *, intents: discord.Intents) -> None:
        super().__init__(
            command_prefix= "-",
            intents=intents,
            activity=discord.Activity( 
                type=discord.ActivityType.watching,
                name="Diddy from the MQ-9 Reaper Drone."
            ),
            status="online"
        )

    async def setup_hook(self) -> None:
        for cog in COGS:
            await bot.load_extension(f"cogs.{cog}")
        self.tree.copy_global_to(guild=GUILD)  # This copies the global commands over to your guild.
        await self.tree.sync(guild=GUILD)

bot = JackInTheBox(intents=INTENTS)

if __name__ == "__main__":
    if USE_TEST_BOT:
        bot.run(TOKEN_TEST)
    else:
        bot.run(TOKEN)