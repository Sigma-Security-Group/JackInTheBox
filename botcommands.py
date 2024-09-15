import json
import os
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
        
        # Clear old commands and register new commands
        await bot.tree.clear_commands(guild=GUILD)
        
        bot.tree.add_command(commend, guild=GUILD)
        bot.tree.add_command(incident_report, guild=GUILD)
        bot.tree.add_command(user_report_file, guild=GUILD)
        bot.tree.add_command(delete_report, guild=GUILD)
        
        # Sync commands with the guild
        await bot.tree.sync(guild=GUILD)
        
        # Verify commands
        commands = await bot.tree.fetch_commands()
        logging.info(f"Commands registered: {[cmd.name for cmd in commands]}")
        
        logging.info(f"Logged in as {bot.user.name}")
        logging.info(f"Slash commands synced for guild {GUILD_ID}")
    except discord.HTTPException as http_error:
        logging.error(f"HTTP error during command registration or syncing: {http_error}")
    except Exception as e:
        logging.error(f"Unexpected error during command registration or syncing: {e}")

# Basic commands
@bot.command(name='habibi', help="Responds with a personalized message.")
async def habibi(ctx):
    user_name = ctx.author.name
    response = f"{user_name} is Diddy's Habibi but loves Jack the most"
    await ctx.send(response)

@bot.command(name='evesjoke', help="Diddle East")
async def evesjoke(ctx):
    await ctx.send("Diddy is didling off to the diddle east. - Eve Makya")

# Commendation command
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

# Handle errors for the commend command
@commend.error
async def commend_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.MissingRole):
        await interaction.response.send_message("You do not have the required role to use this command.", ephemeral=True)

# Incident report modal
class IncidentReportModal(discord.ui.Modal):
    def __init__(self, interaction: discord.Interaction):
        super().__init__(title="Incident Report")
        self.interaction = interaction
        
        self.add_item(discord.ui.InputText(label="Incident Subject (Person of Report)", placeholder="Enter Discord username and ID"))
        self.add_item(discord.ui.InputText(label="Incident Date and Time", placeholder="Format: YYYY-MM-DD HH:MM", required=True))
        self.add_item(discord.ui.InputText(label="Incident Details", style=discord.InputTextStyle.long, placeholder="Enter the details of the incident", required=True))
        self.add_item(discord.ui.InputText(label="Incident Evidence", placeholder="Provide evidence (links, screenshots, etc.)", required=False))
        self.add_item(discord.ui.InputText(label="Incident Ticket Numbers", placeholder="Enter relevant ticket numbers", required=False))
        self.add_item(discord.ui.InputText(label="Incident Outcome", placeholder="Choose: Informal Verbal Warning, Formal Verbal Warning, Written Warning, Demotion, Kick, Ban, Blacklist"))

    async def callback(self, interaction: discord.Interaction):
        global report_counter
        
        report_counter += 1
        report_id = f"Incident Report {str(report_counter).zfill(4)}"
        
        subject = self.children[0].value
        date_time = self.children[1].value
        details = self.children[2].value
        evidence = self.children[3].value
        ticket_numbers = self.children[4].value
        outcome = self.children[5].value
        handler = interaction.user  # The person who submitted the report

        try:
            date_time_obj = datetime.strptime(date_time, "%Y-%m-%d %H:%M")
            date_time_utc = date_time_obj.astimezone(pytz.UTC)
        except ValueError:
            await interaction.response.send_message("Invalid date format. Please use `YYYY-MM-DD HH:MM`.", ephemeral=True)
            return

        embed = discord.Embed(title=report_id, color=discord.Color.red(), timestamp=discord.utils.utcnow())
        embed.add_field(name="Incident Subject", value=subject, inline=False)
        embed.add_field(name="Incident Handler", value=handler.mention, inline=False)
        embed.add_field(name="Incident Date and Time (UTC)", value=date_time_utc.strftime('%Y-%m-%d %H:%M UTC'), inline=False)
        embed.add_field(name="Incident Details", value=details, inline=False)
        embed.add_field(name="Incident Evidence", value=evidence if evidence else "No evidence provided", inline=False)
        embed.add_field(name="Incident Ticket Numbers", value=ticket_numbers if ticket_numbers else "No ticket numbers provided", inline=False)
        embed.add_field(name="Incident Outcome", value=outcome, inline=False)

        report_log_channel = bot.get_channel(REPORT_LOG_CHANNEL_ID)
        if report_log_channel:
            report_message = await report_log_channel.send(embed=embed)

            reported_user_id = subject.split()[-1]  # Extract the Discord ID from the subject
            if reported_user_id not in incident_reports:
                incident_reports[reported_user_id] = []
            incident_reports[reported_user_id].append((report_id, report_message.jump_url))

        # Send a confirmation message to the unit staff channel
        unit_staff_channel = bot.get_channel(UNIT_STAFF_CHANNEL_ID)
        if unit_staff_channel:
            await unit_staff_channel.send(f"New incident report filed by {handler.mention}: [View Report]({report_message.jump_url})")

        await interaction.response.send_message(f"Incident report successfully filed as **{report_id}**", ephemeral=True)

# Incident report command
@discord.app_commands.command(name="incident_report", description="Start an incident report")
@discord.app_commands.guilds(GUILD_ID)
@discord.app_commands.checks.has_role(REQUIRED_ROLE)
async def incident_report(interaction: discord.Interaction):
    modal = IncidentReportModal(interaction)
    await interaction.response.send_modal(modal)

# Retrieve reports for a specific user
@discord.app_commands.command(name="user_report_file", description="Retrieve all reports for a specific user by their Discord ID")
@discord.app_commands.guilds(GUILD_ID)
@discord.app_commands.describe(user_id="The Discord ID of the user you want to retrieve reports for")
@discord.app_commands.checks.has_role(REQUIRED_ROLE)
async def user_report_file(interaction: discord.Interaction, user_id: str):
    if user_id in incident_reports:
        embed = discord.Embed(title=f"Incident Reports for User ID: {user_id}", color=discord.Color.green())
        for report_id, report_url in incident_reports[user_id]:
            embed.add_field(name=report_id, value=f"[View Report]({report_url})", inline=False)

        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message(f"No reports found for user ID: {user_id}", ephemeral=True)

# Delete a report command
@discord.app_commands.command(name="delete_report", description="Delete a report by its ID")
@discord.app_commands.guilds(GUILD_ID)
@discord.app_commands.checks.has_role(REQUIRED_ROLE)
@discord.app_commands.describe(report_id="The ID of the report to delete")
async def delete_report(interaction: discord.Interaction, report_id: str):
    global report_counter
    try:
        report_number = int(report_id.split()[2])
    except ValueError:
        await interaction.response.send_message("Invalid report ID format. Please use `Incident Report ####`.", ephemeral=True)
        return
    
    if report_number >= report_counter:
        await interaction.response.send_message(f"Report ID {report_id} does not exist.", ephemeral=True)
        return
    
    # Remove the report from the storage
    for user_reports in incident_reports.values():
        for i, (r_id, r_url) in enumerate(user_reports):
            if r_id == report_id:
                del user_reports[i]
                break
    
    report_counter -= 1
    # Adjust the report counter
    new_report_id = f"Incident Report {str(report_counter).zfill(4)}"
    
    # Inform the user
    await interaction.response.send_message(f"Report {report_id} deleted successfully. The report counter has been adjusted to {str(report_counter).zfill(4)}.", ephemeral=True)

# Error handling for role check failure
@incident_report.error
@user_report_file.error
@delete_report.error
async def role_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.MissingRole):
        await interaction.response.send_message(f"You must have the `{REQUIRED_ROLE}` role to use this command.", ephemeral=True)

if __name__ == "__main__":
    bot.run(TOKEN)
