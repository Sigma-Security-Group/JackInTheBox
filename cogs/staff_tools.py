import json
import logging
import discord
import config
from dateutil.parser import parse
from discord.ext import commands
from datetime import datetime, timedelta, timezone


user_persistent_modal_values: dict[int, dict] = {}

class StaffTools(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot


    # ================================
    # Incident report command. // Jack
    #=================================
    @discord.app_commands.command(name="incident-report", description="Start an incident report")
    @discord.app_commands.guilds(config.GUILD_ID)
    @discord.app_commands.checks.has_role(config.UNIT_STAFF_ROLE_ID)
    async def incident_report(self, interaction: discord.Interaction):
        # Check if the command is invoked in the correct staff channel
        if interaction.channel.id != config.UNIT_STAFF_CHANNEL_ID:  # Replace with your designated staff channel ID
            await interaction.response.send_message("You can only use this command in the designated staff channel.", ephemeral=True)
            return

        try:
            modal = IncidentReportModal(interaction, self.bot)
            await interaction.response.send_modal(modal)
        except Exception as e:
            logging.exception(f"Error in incident_report command: {e}")
            await interaction.response.send_message("An error occurred while opening the incident report form.", ephemeral=True)


    # =====================================
    # Record of Punishment Command. // Jack
    # =====================================

    # Delete a report command
    @discord.app_commands.command(name="delete-report", description="Delete a report by its ID")
    @discord.app_commands.guilds(config.GUILD_ID)
    @discord.app_commands.checks.has_role(config.UNIT_STAFF_ROLE_ID)  # Ensure only staff can use this command
    async def delete_report(self, interaction: discord.Interaction, report_id: str):
        # Ensure the command is being used in the designated staff channel
        if interaction.channel.id != config.UNIT_STAFF_CHANNEL_ID:
            await interaction.response.send_message("This command can only be used in the staff channel.", ephemeral=True)
            return

        try:
            report_number = int("".join(filter(str.isdigit, report_id)).lstrip("0"))
            with open("Data/incident_reports.json") as f:
                incident_reports = json.load(f)

            for i, report in enumerate(incident_reports):
                if report_number == report["report_id"]:
                    # Remove Discord message
                    guild = self.bot.get_guild(config.GUILD_ID)
                    if not guild:
                        logging.exception(f"Guild not found.")
                        return
                    channel_report_log = guild.get_channel(config.REPORT_LOG_CHANNEL_ID)
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
    @delete_report.error
    async def role_error(self, interaction: discord.Interaction, error: commands.CommandError):
        if isinstance(error, discord.app_commands.errors.MissingRole):
            await interaction.response.send_message(f"You must have the `{config.UNIT_STAFF_ROLE_ID}` role to use this command.", ephemeral=True)
        else:
            logging.exception(f"Error in role check: {error}")
            await interaction.response.send_message("An error occurred while processing your request.", ephemeral=True)



# ==============================
# Incident Report Modal. // Jack
# ==============================
class IncidentReportModal(discord.ui.Modal):
    def __init__(self, interaction: discord.Interaction, bot: commands.Bot):
        super().__init__(title="Incident Report")
        self.interaction = interaction
        self.bot = bot

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
            # Open and load the incident reports file
            with open("Data/incident_reports.json") as f:
                incident_reports = json.load(f)

            # Ensure it's a list, if the JSON is invalid, we initialize a new list
            if not isinstance(incident_reports, list):
                logging.error("incident_reports is not a list, initializing as an empty list.")
                incident_reports = []
        except (FileNotFoundError, json.JSONDecodeError):
            # In case the file is missing or contains invalid JSON, initialize an empty list
            logging.error("incident_reports.json not found or contains invalid data. Initializing empty list.")
            incident_reports = []

        print(incident_reports)

        try:
            # Generate the report ID
            report_id = incident_reports[-1]["report_id"] + 1 if len(incident_reports) > 0 else 1
            subject = self.children[0].value
            date_time = self.children[1].value
            details = self.children[2].value
            evidence = self.children[3].value
            outcome = self.children[4].value
            handler = interaction.user

            try:
                # Try to parse the date
                date_time_obj = parse(date_time)
            except Exception as e:
                logging.exception(f"Error converting date. {e}")
                await interaction.response.send_message("Invalid date format. Please use YYYY-MM-DD.", ephemeral=True)
                user_persistent_modal_values[interaction.user.id] = {
                    "timestamp": datetime.now(timezone.utc).timestamp(),
                    "subject": subject,
                    "date_time": date_time,
                    "details": details,
                    "evidence": evidence,
                    "outcome": outcome
                }
                return

            # Create an embed for the incident report
            embed = discord.Embed(title=f"Incident Report {report_id:04}", color=discord.Color.red(), timestamp=discord.utils.utcnow())
            embed.add_field(name="Incident Subject", value=subject, inline=False)
            embed.add_field(name="Incident Handler", value=handler.mention, inline=False)
            embed.add_field(name="Incident Date", value=date_time_obj.strftime('%Y-%m-%d'), inline=False)
            embed.add_field(name="Incident Details", value=details, inline=False)
            embed.add_field(name="Incident Evidence", value=evidence if evidence else "No evidence provided", inline=False)
            embed.add_field(name="Incident Outcome", value=outcome, inline=False)

            # Send the report message to the log channel
            report_log_channel = self.bot.get_channel(config.REPORT_LOG_CHANNEL_ID)
            report_message = await report_log_channel.send(embed=embed)

            # Create a new incident report entry
            new_incident_report = {
                "report_id": report_id,
                "date": date_time_obj.strftime('%Y-%m-%d'),
                "message_id": report_message.id
            }

            # Append the new report to the incident reports list
            incident_reports.append(new_incident_report)

            # Write the updated list back to the JSON file
            with open("Data/incident_reports.json", "w") as f:
                json.dump(incident_reports, f, indent=4)

            print(incident_reports)

            # Notify staff in the unit staff channel
            unit_staff_channel = self.bot.get_channel(config.UNIT_STAFF_CHANNEL_ID)
            if unit_staff_channel:
                await unit_staff_channel.send(f"New incident report filed by {handler.mention}: [View Report]({report_message.jump_url})")

            # Send success response to the user
            await interaction.response.send_message(f"Incident report successfully filed as **{report_id}**", ephemeral=True)

            # Clear persistent modal values
            if interaction.user.id in user_persistent_modal_values:
                del user_persistent_modal_values[interaction.user.id]

        except Exception as e:
            logging.exception(f"Error in IncidentReportModal callback: {e}")
            await interaction.response.send_message("An error occurred while processing the incident report.", ephemeral=True)
            user_persistent_modal_values[interaction.user.id] = {
                "timestamp": datetime.now(timezone.utc).timestamp(),
                "subject": subject,
                "date_time": date_time,
                "details": details,
                "evidence": evidence,
                "outcome": outcome
            }


async def setup(bot: commands.Bot):
    await bot.add_cog(StaffTools(bot))
