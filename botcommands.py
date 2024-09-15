import logging
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import pytz
from dateutil import parser
from secret import TOKEN

# Define intents and create bot instance
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

GUILD_ID = 288446755219963914
GUILD = discord.Object(id=GUILD_ID)

# Channel IDs
COMMENDATIONS_CHANNEL_ID = 1109263109526396938
REPORT_LOG_CHANNEL_ID = 889752071815974952
UNIT_STAFF_CHANNEL_ID = 740368938239524995
REQUIRED_ROLE = "Unit Staff"

# Report counter and incident report storage
report_counter = 0
incident_reports = {}

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Bot on_ready event to register commands
@bot.event
async def on_ready():
    try:
        logging.info("Starting command registration...")
        await bot.tree.clear_commands(guild=GUILD)  # Clear old commands for the specific guild
        
        # Register commands
        bot.tree.add_command(commend, guild=GUILD)
        bot.tree.add_command(incident_report, guild=GUILD)
        bot.tree.add_command(user_report_file, guild=GUILD)
        bot.tree.add_command(delete_report, guild=GUILD)
        
        # Sync commands with the guild
        await bot.tree.sync(guild=GUILD)
        
        logging.info(f"Logged in as {bot.user.name}")
        logging.info(f"Slash commands synced for guild {GUILD_ID}")
    except discord.HTTPException as http_error:
        logging.error(f"HTTP error during command registration or syncing: {http_error}")
    except Exception as e:
        logging.error(f"Unexpected error during command registration or syncing: {e}")

# Command definitions
@discord.app_commands.command(name="commend", description="Commend a person")
@discord.app_commands.guilds(GUILD_ID)
async def commend(interaction: discord.Interaction, person: discord.User, role: str, reason: str):
    guild = bot.get_guild(GUILD_ID)
    if guild is None:
        logging.exception("commend: guild is None")
        return

    channelCommendations = await guild.fetch_channel(COMMENDATIONS_CHANNEL_ID)
    if not isinstance(channelCommendations, discord.TextChannel):
        logging.exception("commend: channelCommendations is not discord.TextChannel")
        return

    await channelCommendations.send(
        f"Commended: {person.mention}\n"
        f"By: {interaction.user.mention}\n"
        f"Role: {role}\n"
        f"Reason: {reason}"
    )

    await interaction.response.send_message(f"Thank you for commending! It has been submitted successfully in {channelCommendations.mention}.", ephemeral=True, delete_after=10.0)

@discord.app_commands.command(name="incident_report", description="Start an incident report")
@discord.app_commands.guilds(GUILD_ID)
@discord.app_commands.checks.has_role(REQUIRED_ROLE)
async def incident_report(interaction: discord.Interaction):
    modal = IncidentReportModal(interaction)
    await interaction.response.send_modal(modal)

@discord.app_commands.command(name="user_report_file", description="Retrieve all reports for a specific user")
@discord.app_commands.guilds(GUILD_ID)
@discord.app_commands.describe(user_id="The Discord ID of the user")
@discord.app_commands.checks.has_role(REQUIRED_ROLE)
async def user_report_file(interaction: discord.Interaction, user_id: str):
    if user_id in incident_reports:
        embed = discord.Embed(title=f"Incident Reports for User ID: {user_id}", color=discord.Color.green())
        for report_id, report_url in incident_reports[user_id]:
            embed.add_field(name=report_id, value=f"[View Report]({report_url})", inline=False)
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message(f"No reports found for user ID: {user_id}", ephemeral=True)

@discord.app_commands.command(name="delete_report", description="Delete a report by its ID")
@discord.app_commands.guilds(GUILD_ID)
@discord.app_commands.checks.has_role(REQUIRED_ROLE)
@discord.app_commands.describe(report_id="The ID of the report to delete")
async def delete_report(interaction: discord.Interaction, report_id: str):
    global report_counter
    try:
        report_number = int(report_id.split()[2])
    except ValueError:
        await interaction.response.send_message("Invalid report ID format. Number extraction failed.", ephemeral=True)
        return

    if report_number > report_counter:
        await interaction.response.send_message("Report ID number is out of range.", ephemeral=True)
        return

    if report_number < report_counter:
        report_counter = report_number - 1

    for user_reports in incident_reports.values():
        for i, (r_id, _) in enumerate(user_reports):
            if r_id == report_id:
                user_reports.pop(i)
                break

    await interaction.response.send_message(f"Report with ID **{report_id}** has been deleted and counter adjusted.", ephemeral=True)

# Error handling for role check failure
@incident_report.error
@user_report_file.error
@delete_report.error
async def role_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.MissingRole):
        await interaction.response.send_message(f"You must have the `{REQUIRED_ROLE}` role to use this command.", ephemeral=True)

if __name__ == "__main__":
    bot.run(TOKEN)
