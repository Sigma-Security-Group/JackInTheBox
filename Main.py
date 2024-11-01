import discord
import os
import config
from discord.ext import commands
from secret import TOKEN, TOKEN_TEST, USE_TEST_BOT

INTENTS = discord.Intents.all()
COGS = [cog[:-3] for cog in os.listdir("cogs/") if cog.endswith(".py")]

class JackInTheBox(commands.Bot):
    """Jack In The Box."""
    def __init__(self, *, intents: discord.Intents) -> None:
        super().__init__(
            command_prefix=commands.when_mentioned,  # Use mention as command prefix rather than "-", which collides with Friendly Snek's prefix.
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
        self.tree.copy_global_to(guild=config.GUILD)  # This copies the global commands over to your guild.
        await self.tree.sync(guild=config.GUILD)

bot = JackInTheBox(intents=INTENTS)

if __name__ == "__main__":
    if USE_TEST_BOT:
        bot.run(TOKEN_TEST)
    else:
        bot.run(TOKEN)
