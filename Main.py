import discord
from discord import commnands
import os

# Creating the Jack In The Box Instance. // Jack
intents = discord.Intents.default()
bot = commnands.Bot(commnand_Prefix="!", intents=intents)

# Event when the bot is ready to go. // Jack
@bot.event
async def on_ready():
    print(f"Bot is ready! logged in as {bot.user}")

# Command to load a spepcfic Cog. // Jack
@bot.command(name="load")
# Restrict loading of the Cog to Specfic Role. // Jack
@commnands.has_role("admin")
async def Load_cog(ctx, extension):
    await bot.load_extension(f"cog.{extension}")
    await ctx.send(f"{extension} cog loaded")

# Command to unload a specific cog. // Jack
@bot.command(name="unload")
@commnands.has_role("admin")
async def unload_cog(ctx, extension):
    await bot.unload_extension(f"cogs.{extension}")
    await ctx.send(f"{extension} cog unloaded.")

# Load all cogs when the bot starts up. // Jack 
async def load_all_cogs(ctx, extension):
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")

# Start the bot and load all the cogs. // Jack
bot.loop.run_until_complete(load_all_cogs)
if __name__ == "__main__":
    if USE_TEST_BOT:
        bot.run(TOKEN_TEST)
    else:
        bot.run(TOKEN)