import logging

import discord
from discord.ext import commands
from discord import app_commands
from secret import TOKEN

GUILD_ID = 288446755219963914
GUILD = discord.Object(id=GUILD_ID)
COMMENDATIONS = 1109263109526396938

@discord.app_commands.command(name="commend")
@discord.app_commands.guilds(GUILD)
@discord.app_commands.describe(
    user = "User to commend.",
    role = "The user's role in the operation.",
    reason = "Why you commend these user."
)
async def commend(interaction: discord.Interaction, user: discord.User, role: str, reason: str) -> None:
    """ Commend a user that has done well in an operation. """
    logging.info(f"{interaction.user.display_name} ({interaction.user.id}) commended user {user.display_name} ({user.id}).")
    guild = bot.get_guild(GUILD_ID)
    if guild is None:
        logging.exception("commend: guild is None")
        return

    channelCommendations = await guild.fetch_channel(COMMENDATIONS)
    if not isinstance(channelCommendations, discord.TextChannel):
        logging.exception("commend: channelCommendations is not discord.TextChannel")
        return

    await channelCommendations.send(
        f"Commended: {user.mention}\n"
        f"By: {interaction.user.mention}\n"
        f"Role: {role}\n"
        f"Reason: {reason}"
    )

    await interaction.response.send_message(f"Thank you for commending! It has been submitted successfully in {channelCommendations.mention}.", ephemeral=True, delete_after=10.0)

if __name__ == "__main__":
    # Gives the bot all intents to allow us to do anything we want.
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix="!", intents=intents)
    bot.run(TOKEN)