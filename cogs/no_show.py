import json
import os
import logging
import discord
from datetime import datetime, timedelta, timezone
from discord.ext import commands
from discord import app_commands
import config

# Logging setup
logging.basicConfig(level=logging.INFO)


class NoShowTracking(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__()
        self.bot = bot

    def ensure_json_file_exists(self, file_path: str) -> None:
        """Ensure the JSON file exists and initialize it if it doesn't."""
        if not os.path.exists(file_path):
            os.makedirs(os.path.dirname(file_path), exist_ok=True)  # Create directory if necessary
            with open(file_path, "w") as f:
                json.dump({}, f, indent=4)  # Initialize with an empty dictionary

    @discord.app_commands.command(name="no-show-report", description="Report a member for missing a scheduled operation.")
    @discord.app_commands.guilds(config.GUILD_ID)
    @discord.app_commands.checks.has_any_role(
        config.UNIT_STAFF_ROLE_ID,
        config.CURATOR_ROLE_ID,
        config.ADVISOR_ROLE_ID
    )
    async def no_show_report(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        operation_name: str,
        zeus: str
    ) -> None:
        """Report a no-show for a specific operation."""
        try:
            await interaction.response.defer(ephemeral=True)  # Acknowledge the interaction early

            # Ensure JSON file exists
            no_show_file_path = "Data/no_show_data.json"
            self.ensure_json_file_exists(no_show_file_path)

            # Load no-show data from JSON
            with open(no_show_file_path, "r") as f:
                no_show_data = json.load(f)

            user_id = str(member.id)
            current_time = datetime.now(timezone.utc).isoformat()

            # If the user has no previous record, initialize their data
            if user_id not in no_show_data:
                no_show_data[user_id] = {
                    "count": 0,
                    "records": []  # Initialize an empty list for operation records
                }

            # Increment the no-show count and log operation details
            no_show_data[user_id]["count"] += 1
            no_show_data[user_id]["records"].append({
                "operation_name": operation_name,
                "date": current_time,
                "zeus": zeus
            })

            # Save updated no-show data back to the JSON file
            with open(no_show_file_path, "w") as f:
                json.dump(no_show_data, f, indent=4)

            # Notify the user via DM
            try:
                await member.send(
                    embed=discord.Embed(
                        title="No-Show Report",
                        description=(
                            f"You have been marked as a no-show for the operation **{operation_name}** "
                            f"organized by **{zeus}**. Staff has been notified."
                        ),
                        color=discord.Color.red()
                    ).set_footer(text="Please ensure you attend scheduled operations to avoid further actions.")
                )
            except discord.Forbidden:
                logging.warning(f"Could not DM {member.display_name}. User has DMs disabled.")

            # Notify staff in the configured channel
            staff_advisor_channel = self.bot.get_channel(config.STAFF_ADVISOR_CHANNEL_ID)
            if not staff_advisor_channel:
                await interaction.followup.send(
                    "Could not find the staff advisor channel. Please check the configuration.",
                    ephemeral=True
                )
                return

            # Embed for tracking purposes
            embed = discord.Embed(
                title="No-Show Report",
                description=f"{member.mention} has been reported as a no-show.",
                color=discord.Color.orange()
            )
            embed.add_field(name="Operation Name", value=operation_name, inline=False)
            embed.add_field(name="Zeus", value=zeus, inline=False)
            embed.add_field(name="Reported By", value=interaction.user.mention, inline=False)
            embed.add_field(name="No-Show Count", value=no_show_data[user_id]["count"], inline=False)
            embed.set_footer(text="Staff may take further action as necessary.")
            await staff_advisor_channel.send(embed=embed)

            # Notify if 3 no-shows are reached
            if no_show_data[user_id]["count"] >= 3:
                staff_role = interaction.guild.get_role(config.UNIT_STAFF_ROLE_ID)
                alert_embed = discord.Embed(
                    title="Repeated No-Show Alert",
                    description=(
                        f"{member.mention} has missed **3 scheduled operations**. "
                        f"This requires immediate attention."
                    ),
                    color=discord.Color.red()
                )
                alert_embed.set_footer(text="Please take the necessary actions to address this.")
                await staff_advisor_channel.send(content=staff_role.mention, embed=alert_embed)

            # Acknowledge success
            await interaction.followup.send(
                f"Successfully reported {member.mention} as a no-show for **{operation_name}**.",
                ephemeral=True
            )

        except Exception as e:
            logging.exception(f"Error in no_show_report command: {e}")
            await interaction.followup.send(
                "An error occurred while processing the no-show report. Please try again later.",
                ephemeral=True
            )

    @discord.app_commands.command(name="no-show-stats", description="Display a leaderboard of no-show reports.")
    @discord.app_commands.guilds(config.GUILD_ID)
    @discord.app_commands.checks.has_any_role(
        config.UNIT_STAFF_ROLE_ID,
        config.CURATOR_ROLE_ID,
        config.ZEUS_ROLE_ID,
        config.ZEUSINTRAINING_ROLE_ID
    )
    async def no_show_leaderboard(self, interaction: discord.Interaction) -> None:
        """Display stats for no-shows, including operations and dates."""
        try:
            await interaction.response.defer(ephemeral=False)  # Acknowledge the interaction

            # Load no-show data from JSON
            no_show_file_path = "Data/no_show_data.json"
            self.ensure_json_file_exists(no_show_file_path)

            with open(no_show_file_path, "r") as f:
                no_show_data = json.load(f)

            # Check if there are any records
            if not no_show_data:
                await interaction.followup.send("No no-show records found.", ephemeral=True)
                return

            # Build the embed for the leaderboard
            embed = discord.Embed(
                title="No-Show Leaderboard",
                description="List of members with their no-show records (sorted by highest count):",
                color=discord.Color.orange()
            )

            guild = interaction.guild
            sorted_no_shows = sorted(no_show_data.items(), key=lambda x: x[1]["count"], reverse=True)

            for i, (user_id, data) in enumerate(sorted_no_shows[:10]):  # Limit to top 10
                member = guild.get_member(int(user_id))
                member_name = member.display_name if member else f"Unknown User ({user_id})"

                # Ensure "records" exists in the user's data
                records = data.get("records", [])
                formatted_records = "\n".join(
                    f"**{record['operation_name']}** on {datetime.fromisoformat(record['date']).strftime('%Y-%m-%d %H:%M:%S UTC')}"
                    for record in records
                ) if records else "No specific records found."

                embed.add_field(
                    name=f"{i + 1}. {member_name}",
                    value=f"No-Show Count: {data['count']}\n\n{formatted_records}",
                    inline=False
                )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            logging.exception(f"Error in no_show_stats command: {e}")
            await interaction.followup.send(
                "An error occurred while generating the no-show stats. Please try again later.",
                ephemeral=True
            )

    # ===================================
    # Candidate Tracking Command. // Jack
    # ===================================
    @discord.app_commands.command(name="track-a-candidate", description="Track a candidate's progress through operations.")
    @discord.app_commands.guilds(config.GUILD_ID)
    @discord.app_commands.checks.has_any_role(config.UNIT_STAFF_ROLE_ID, config.CURATOR_ROLE_ID, config.ZEUS_ROLE_ID, config.ZEUSINTRAINING_ROLE_ID)
    async def track_a_candidate(self, interaction: discord.Interaction, member: discord.Member) -> None:
        await interaction.response.send_message(f"Tracking progress for {member.display_name}", ephemeral=True)

        channel_commendations = self.bot.get_channel(config.COMMENDATIONS_CHANNEL_ID)
        if not channel_commendations:
            await interaction.followup.send("Commendations channel not found.", ephemeral=True)
            return

        operation_count = 1
        most_recent_message_time = None

        async for message in channel_commendations.history(limit=500):
            if config.OPERATION_KEYWORD.lower() in message.content.lower() and member in message.mentions:
                operation_count += 1
                if most_recent_message_time is None or message.created_at > most_recent_message_time:
                    most_recent_message_time = message.created_at

        current_time = datetime.now(timezone.utc)

        if most_recent_message_time and current_time - most_recent_message_time < timedelta(seconds=1):
            await interaction.followup.send("Error code CCT-0004: Member has already been tracked for this operation. Please try again later.", ephemeral=True)
            logging.debug("Skip tracking due to recent message.")
            return

        if operation_count >= config.TOTAL_OPERATIONS:
            guild = interaction.guild
            unit_staff_role = guild.get_role(config.UNIT_STAFF_ROLE_ID)

            text_message = (
                f"{member.mention}, after demonstrating valour and dedication across {operation_count} successful deployments, "
                f"you’ve proven yourself an asset to this unit.\n\nWelcome to Sigma. Your journey has just begun.\n\n"
                f"{member.mention}, it is now time for your assessment with {unit_staff_role.mention}."
            )
            await channel_commendations.send(text_message)

            embed = discord.Embed(
                title="Candidate Progress Update",
                color=discord.Color.green()
            )
            embed.add_field(name="Candidate", value=member.mention, inline=False)
            embed.add_field(name="Progress", value=f"{operation_count}/{config.TOTAL_OPERATIONS} operations completed.", inline=False)
            embed.add_field(name="Status", value="**Promoted to Sigma Associate**", inline=False)
            embed.set_footer(text="Congratulations on your outstanding achievement!")

            await channel_commendations.send(embed=embed)

        else:
            remaining_ops = config.TOTAL_OPERATIONS - operation_count

            text_message = (
                f"{member.mention} has attended an operation and is on their way to becoming a Sigma Associate. "
                f"They have {remaining_ops} operations left."
            )
            await channel_commendations.send(text_message)

            embed = discord.Embed(
                title="Candidate Progress Update",
                color=discord.Color.blue()
            )
            embed.add_field(name="Candidate", value=member.mention, inline=False)
            embed.add_field(name="Progress", value=f"{operation_count}/{config.TOTAL_OPERATIONS} operations completed.", inline=False)
            embed.add_field(name="Remaining Operations", value=f"{remaining_ops} left.", inline=False)
            embed.set_footer(text="Keep up the great work!")

            await channel_commendations.send(embed=embed)

# Cog setup function
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(NoShowTracking(bot))
