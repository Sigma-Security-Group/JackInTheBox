import json
import logging
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone, timedelta
from dateutil.parser import parse
from secret import TOKEN, TOKEN_TEST, USE_TEST_BOT  # Ensure TOKEN is defined in secret.py

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Define intents and create bot instance
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

#Discord Server ID's
GUILD_ID = 864441968776052747 if USE_TEST_BOT else 288446755219963914
GUILD = discord.Object(id=GUILD_ID)

# Channel & Role ID's
COMMENDATIONS_CHANNEL_ID = 1274979300386275328 if USE_TEST_BOT else 1109263109526396938
REPORT_LOG_CHANNEL_ID = 866938361628852224 if USE_TEST_BOT else 889752071815974952
UNIT_STAFF_CHANNEL_ID = 864442610613485590 if USE_TEST_BOT else 740368938239524995
UNIT_STAFF_ROLE_ID = 864443672032706560 if USE_TEST_BOT else 655465074982518805
REQUIRED_ROLE = "Unit Staff"

# Candidate Tracking - Key Information
OPERATION_KEYWORD = "has attended an Operation"
TOTAL_OPERATIONS = 3 

#Incident Report Fail Logging Text Boxes
user_persistent_modal_values = {}

with open("Data/incident_reports.json") as f: 
    incident_reports = json.load(f)

@bot.event
async def on_ready():
    try:
        logging.info("Starting command registration...")
        bot.tree.clear_commands(guild=GUILD)
        bot.tree.add_command(commend, guild=GUILD)
        bot.tree.add_command(track_operations, guild=GUILD)
        bot.tree.add_command(incident_report, guild=GUILD)
        bot.tree.add_command(user_report_file, guild=GUILD)
        bot.tree.add_command(delete_report, guild=GUILD)
        await bot.tree.sync(guild=GUILD)
        commands = await bot.tree.fetch_commands(guild=GUILD)
        logging.info(f"Commands registered: {[cmd.name for cmd in commands]}")
        logging.info(f"Logged in as {bot.user.name}")
        logging.info(f"Slash commands synced for guild {GUILD_ID}")
    except discord.HTTPException as http_error:
        logging.exception(f"HTTP error during command registration or syncing: {http_error}")
    except Exception as e:
        logging.exception(f"Unexpected error during command registration or syncing: {e}")

@bot.event
async def on_application_command_error(interaction: discord.Interaction, error: Exception):
    logging.exception(f"Error in command: {error}")
    await interaction.response.send_message("An error occurred while processing your request. Please try again later.", ephemeral=True)

# Commendation command
@discord.app_commands.command(name="commend", description="Commend a person")
@discord.app_commands.guilds(GUILD_ID)
async def commend(interaction: discord.Interaction, person: discord.User, role: str, reason: str):
    try:
        guild = bot.get_guild(GUILD_ID)
        channelCommendations = await guild.fetch_channel(COMMENDATIONS_CHANNEL_ID)
        await channelCommendations.send(
            f"Commended: {person.mention}\n"
            f"By: {interaction.user.mention}\n"
            f"Role: {role}\n"
            f"Reason: {reason}"
        )
        await interaction.response.send_message(f"Thank you for commending! It has been submitted successfully in {channelCommendations.mention}.", ephemeral=True, delete_after=10.0)
    except Exception as e:
        logging.exception(f"Error in commend command: {e}")
        await interaction.response.send_message("An error occurred while processing your commendation.", ephemeral=True)

# Candidate Tracking
@bot.tree.command(name="track_operations", description="Track operations for a selected user.")
@app_commands.describe(member="The member whose operations you want to track.")
async def track_operations(interaction: discord.Interaction, member: discord.Member):
    channelCommendations = bot.get_channel(COMMENDATIONS_CHANNEL_ID)

    # Initialize count for the selected member
    operation_count = 1

    # Check previous messages in the commendation channel
    async for message in channelCommendations.history(limit=1000):
        # Ensure the message contains the keyword "Candidate Tracking" (case-insensitive) and mentions the member
        if OPERATION_KEYWORD.lower() in message.content.lower() and member in message.mentions:
            operation_count += 1

    # Check if the member has reached the required number of operations
    if operation_count >= TOTAL_OPERATIONS:
        # Get the unit staff role by ID
        unit_staff_role = interaction.guild.get_role(UNIT_STAFF_ROLE_ID)

        # Send eligibility message
        message_content = (
            f"{member.mention} has been deployed {operation_count} times and is eligible for a Contract. "
            f"{unit_staff_role.mention}, please fill in the necessary paperwork and notify HR."
        )
        await channelCommendations.send(message_content)
    else:
        # Calculate remaining operations
        remaining_ops = TOTAL_OPERATIONS - operation_count
        
        # Send status update message
        message_content = (
            f"{member.mention} has attended an Operation and is on their way to becoming a Sigma Associate. "
            f"They have {remaining_ops} operations left."
        )
        await channelCommendations.send(message_content)

    # Acknowledge the interaction
    await interaction.response.send_message(f"Tracking complete for {member.display_name}.", ephemeral=True)

# Incident report modal
class IncidentReportModal(discord.ui.Modal):
    def __init__(self, interaction: discord.Interaction):
        super().__init__(title="Incident Report")
        self.interaction = interaction

        get_persistent_default = lambda key: user_persistent_modal_values[interaction.user.id][key] if interaction.user.id in user_persistent_modal_values else None
        persistent_default_timestamp = get_persistent_default("timestamp")
        if persistent_default_timestamp and persistent_default_timestamp < (datetime.now(timezone.utc) - timedelta(minutes=15)).timestamp():
            del user_persistent_modal_values[interaction.user.id]

        self.add_item(discord.ui.TextInput(label="Incident Subject (Name and Discord ID)", placeholder="Enter Discord username and ID", default=get_persistent_default("subject"), required=True))
        self.add_item(discord.ui.TextInput(label="Incident Date", placeholder="Include Year, Month and Day.", default=get_persistent_default("date_time"), required=True))
        self.add_item(discord.ui.TextInput(label="Incident Details", style=discord.TextStyle.long, placeholder="Enter the details of the incident", default=get_persistent_default("details"), required=True))
        self.add_item(discord.ui.TextInput(label="Incident Evidence", style=discord.TextStyle.long, placeholder="Provide evidence (links, screenshots, ticket numbers, etc.)", default=get_persistent_default("evidence"), required=False))
        self.add_item(discord.ui.TextInput(label="Incident Outcome", style=discord.TextStyle.long, placeholder="Informal Verbal Warning, Formal Verbal Warning, Written Warning, Demotion, Kick, Ban, Blacklist", default=get_persistent_default("outcome"), required=True))

    async def on_submit(self, interaction: discord.Interaction):
        try:
            report_id = incident_reports[-1]["report_id"] + 1 if len(incident_reports) > 0 else 1
            subject = self.children[0].value
            date_time = self.children[1].value
            details = self.children[2].value
            evidence = self.children[3].value
            outcome = self.children[4].value
            handler = interaction.user
            
            try:
                date_time_obj = parse(date_time)
            except Exception as e:
                logging.exception(f"Error converting date. {e}")
                await interaction.response.send_message("Invalid date format. Please use YYYY-MM-DD.", ephemeral=True)
                user_persistent_modal_values[interaction.user.id] = {
                    "timestamp": datetime.now(timezone.utc).timestamp(),
                    "subject": subject,
                    "date_time": date_time,
                    "details": details,
                    "evidence":  evidence,
                    "outcome": outcome
                }
                return

            embed = discord.Embed(title=f"Incident Report {report_id:04}", color=discord.Color.red(), timestamp=discord.utils.utcnow())
            embed.add_field(name="Incident Subject", value=subject, inline=False)
            embed.add_field(name="Incident Handler", value=handler.mention, inline=False)
            embed.add_field(name="Incident Date", value=date_time_obj.strftime('%Y-%m-%d'), inline=False)
            embed.add_field(name="Incident Details", value=details, inline=False)
            embed.add_field(name="Incident Evidence", value=evidence if evidence else "No evidence provided", inline=False)
            embed.add_field(name="Incident Outcome", value=outcome, inline=False)

            report_log_channel = bot.get_channel(REPORT_LOG_CHANNEL_ID)
            report_message = await report_log_channel.send(embed=embed)
            
            new_incident_report = {
                "report_id": report_id,
                "subject": subject,
                "handler_id": handler.id,
                "handler_name": handler.display_name,
                "date": date_time_obj.strftime('%Y-%m-%d'),
                "details": details,
                "evidence": evidence,
                "outcome": outcome,
                "message_id": report_message.id
            }
            with open("Data/incident_reports.json") as f: 
                incident_reports = json.load(f)
            # Ensure it's a list
            if not isinstance(incident_reports, list):
                logging.error("incident_reports is not a list, initializing as an empty list.")
            incident_reports = []
            
            unit_staff_channel = bot.get_channel(UNIT_STAFF_CHANNEL_ID)
            if unit_staff_channel:
                await unit_staff_channel.send(f"New incident report filed by {handler.mention}: [View Report]({report_message.jump_url})")
            
            await interaction.response.send_message(f"Incident report successfully filed as **{report_id}**", ephemeral=True)
            del user_persistent_modal_values[interaction.user.id]
        except Exception as e:
            logging.exception(f"Error in IncidentReportModal callback: {e}")
            await interaction.response.send_message("An error occurred while processing the incident report.", ephemeral=True)
            user_persistent_modal_values[interaction.user.id] = {
                "timestamp": datetime.now(timezone.utc).timestamp(),
                "subject": subject,
                "date_time": date_time,
                "details": details,
                "evidence":  evidence,
                "outcome": outcome
            }
    
    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        user_persistent_modal_values[interaction.user.id] = {
            "timestamp": datetime.now(timezone.utc).timestamp(),
            "subject": self.children[0].value,
            "date_time": self.children[1].value,
            "details": self.children[2].value,
            "evidence":  self.children[3].value,
            "outcome": self.children[4].value
        }


# Incident report command
@discord.app_commands.command(name="incident_report", description="Start an incident report")
@discord.app_commands.guilds(GUILD_ID)
@discord.app_commands.checks.has_role(REQUIRED_ROLE)
async def incident_report(interaction: discord.Interaction):
    # Check if the command is invoked in the correct staff channel
    if interaction.channel.id != UNIT_STAFF_CHANNEL_ID:  # Replace with your designated staff channel ID
        await interaction.response.send_message("You can only use this command in the designated staff channel.", ephemeral=True)
        return
    
    try:
        modal = IncidentReportModal(interaction)
        await interaction.response.send_modal(modal)
    except Exception as e:
        logging.exception(f"Error in incident_report command: {e}")
        await interaction.response.send_message("An error occurred while opening the incident report form.", ephemeral=True)

# Record of Punishment Command
@discord.app_commands.command(name="user_report_file", description="Retrieve all reports for a specific user by their Discord ID")
@discord.app_commands.guilds(GUILD_ID)
@discord.app_commands.checks.has_role(REQUIRED_ROLE)  # Ensure only staff can use this command
async def user_report_file(interaction: discord.Interaction, user_id: str):
    # Ensure the command is being used in the designated staff channel
    if interaction.channel.id != UNIT_STAFF_CHANNEL_ID:
        await interaction.response.send_message("This command can only be used in the staff channel.", ephemeral=True)
        return

    try:
        embed = discord.Embed(title=f"Incident Reports for User ID: {user_id}", color=discord.Color.orange())
        reports_found = False  # Flag to check if any reports are found
        
        for report in incident_reports:
            if user_id in report["subject"]:
                reports_found = True
                report_title = f"Incident Report {report['report_id']:04}"
                
                # Check if 'message_id' exists
                if 'message_id' in report:
                    report_url = f"https://discord.com/channels/{GUILD_ID}/{REPORT_LOG_CHANNEL_ID}/{report['message_id']}"
                    embed.add_field(name=report_title, value=f"[View Report]({report_url})", inline=False)
                else:
                    embed.add_field(name=report_title, value="The report has been expunged from their record.", inline=False)

        if reports_found:
            # Send the output to the staff channel
            staff_channel = bot.get_channel(UNIT_STAFF_CHANNEL_ID)
            await staff_channel.send(embed=embed)  # Send the embed to the staff channel
            await interaction.response.send_message("Reports have been sent to the staff channel.", ephemeral=True)
        else:
            await interaction.response.send_message(f"No reports found for user ID: {user_id}", ephemeral=True)
    except Exception as e:
        logging.exception(f"Error in user_report_file command: {e}")
        await interaction.response.send_message("An error occurred while retrieving the reports.", ephemeral=True)

# Delete a report command
@discord.app_commands.command(name="delete_report", description="Delete a report by its ID")
@discord.app_commands.guilds(GUILD_ID)
@discord.app_commands.checks.has_role(REQUIRED_ROLE)  # Ensure only staff can use this command
async def delete_report(interaction: discord.Interaction, report_id: str):
    # Ensure the command is being used in the designated staff channel
    if interaction.channel.id != UNIT_STAFF_CHANNEL_ID:
        await interaction.response.send_message("This command can only be used in the staff channel.", ephemeral=True)
        return

    try:
        report_number = int("".join(filter(str.isdigit, report_id)).lstrip("0"))
        with open("Data/incident_reports.json") as f: 
            incident_reports = json.load(f)

        for i, report in enumerate(incident_reports):
            if report_number == report["report_id"]:
                # Remove Discord message
                guild = bot.get_guild(GUILD_ID)
                if not guild:
                    logging.exception(f"Guild not found.")
                    return
                channel_report_log = guild.get_channel(REPORT_LOG_CHANNEL_ID)
                if not isinstance(channel_report_log, discord.TextChannel):
                    logging.exception(f"channel_report_log not discord.TextChannel.")
                    return
                message = await channel_report_log.fetch_message(report["message_id"])
                await message.delete()

                # Remove from list
                incident_reports.pop(i)
                break
        else:
            await interaction.response.send_message(f"Report ID {report_id} does not exist.", ephemeral=True)
            return
        with open("Data/incident_reports.json", "w") as f:
            json.dump(incident_reports, f, indent=4)
        await interaction.response.send_message(f"Report {report_id} deleted successfully.", ephemeral=True)
    except ValueError:
        await interaction.response.send_message("Invalid report ID format. Please use `Incident Report ####`.", ephemeral=True)
    except discord.NotFound:
        await interaction.response.send_message("Could not find the message.", ephemeral=True)
    except (discord.Forbidden, discord.HTTPException):
        await interaction.response.send_message("Could not delete the message.", ephemeral=True)
    except Exception as e:
        logging.exception(f"Error in delete_report command: {e}")
        await interaction.response.send_message("An error occurred while deleting the report.", ephemeral=True)

# Incident Report Error Logging
@incident_report.error
@user_report_file.error
@delete_report.error
async def role_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.MissingRole):
        await interaction.response.send_message(f"You must have the `{REQUIRED_ROLE}` role to use this command.", ephemeral=True)
    else:
        logging.exception(f"Error in role check: {error}")
        #await interaction.response.send_message("An error occurred while processing your request.", ephemeral=True)

if __name__ == "__main__":
    if USE_TEST_BOT:
        bot.run(TOKEN_TEST)
    else:
        bot.run(TOKEN)