import json
import os
import logging
import discord
from datetime import datetime, timezone
from discord.ext import commands
from discord import app_commands
import config


# Logging setup
logging.basicConfig(level=logging.INFO)


class NoShowTracking(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__()
        self.bot = bot

    @discord.app_commands.command(name="no-show-report", description="Report a member for missing a scheduled event.")
    @discord.app_commands.guilds(config.GUILD_ID)
    @discord.app_commands.checks.has_any_role(
        config.UNIT_STAFF_ROLE_ID,
        config.CURATOR_ROLE_ID,
        config.ADVISOR_ROLE_ID
    )
    
    async def no_show_report(self, interaction: discord.Interaction, member: discord.Member) -> None:
        try:
            await interaction.response.defer(ephemeral=True)  # Acknowledge the interaction early

            # Check if the JSON file exists; create it if it doesn't
            no_show_file_path = "Data/no_show_data.json"
            if not os.path.exists(no_show_file_path):
                with open(no_show_file_path, "w") as f:
                    json.dump({}, f, indent=4)  # Initialize with an empty dictionary

            # Load no-show data from JSON for tracking
            with open(no_show_file_path, "r") as f:
                no_show_data = json.load(f)

            user_id = str(member.id)
            current_time = datetime.now(timezone.utc).isoformat()

            # If the user has no previous record, initialize their data
            if user_id not in no_show_data:
                no_show_data[user_id] = {
                    "count": 0,
                    "timestamps": []
                }

            # Increment the no-show count and add the timestamp
            no_show_data[user_id]["count"] += 1
            no_show_data[user_id]["timestamps"].append(current_time)

            # Save updated no-show data back to the JSON file
            with open(no_show_file_path, "w") as f:
                json.dump(no_show_data, f, indent=4)

            # Notify the user via DM
            try:
                await member.send(
                    embed=discord.Embed(
                        title="No-Show Report",
                        description=(
                            f"You have been marked as a no-show for a scheduled event. "
                            f"This report has been sent to staff for further review."
                        ),
                        color=discord.Color.red()
                    ).set_footer(text="Please ensure you attend scheduled events to avoid further actions.")
                )
            except discord.Forbidden:
                # Log if the bot is unable to DM the user
                logging.warning(f"Could not DM {member.display_name}. User has DMs disabled.")

            # Notify the STAFF_ADVISOR_CHANNEL_ID with a report
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
                description=f"{member.mention} has been reported as a no-show for a scheduled event.",
                color=discord.Color.orange()
            )
            embed.add_field(name="Reported By", value=interaction.user.mention, inline=False)
            embed.add_field(name="No-Show Count", value=no_show_data[user_id]["count"], inline=False)
            embed.set_footer(text="Staff may take further action as necessary.")

            await staff_advisor_channel.send(embed=embed)

            # Check if the user has reached 3 no-shows
            if no_show_data[user_id]["count"] >= 3:
                # Notify the staff with a special alert
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

            # Acknowledge success to the interaction user
            await interaction.followup.send(
                f"Successfully reported {member.mention} as a no-show.",
                ephemeral=True
            )

        except Exception as e:
            logging.exception(f"Error in no_show_report command: {e}")
            await interaction.followup.send(
                "An error occurred while processing the no-show report. Please try again later.",
                ephemeral=True
            )

    @discord.app_commands.command(name="no-show-stats", description="Display a le stat-board of no-show reports.")
    @discord.app_commands.guilds(config.GUILD_ID)
    @discord.app_commands.checks.has_any_role(
        config.UNIT_STAFF_ROLE_ID,
        config.CURATOR_ROLE_ID,
        config.ZEUS_ROLE_ID,
        config.ZEUSINTRAINING_ROLE_ID
    )
    async def no_show_leaderboard(self, interaction: discord.Interaction) -> None:
        try:
            await interaction.response.defer(ephemeral=False)  # Acknowledge the interaction

            # Load no-show data from JSON
            no_show_file_path = "Data/no_show_data.json"
            if not os.path.exists(no_show_file_path):
                await interaction.followup.send("No no-show data found. The file does not exist.", ephemeral=True)
                return

            with open(no_show_file_path, "r") as f:
                no_show_data = json.load(f)

            # Sort users by their no-show count (descending)
            sorted_no_shows = sorted(no_show_data.items(), key=lambda x: x[1]["count"], reverse=True)

            # Check if there are any records
            if not sorted_no_shows:
                await interaction.followup.send("No no-show records found.", ephemeral=True)
                return

            # Build the embed for the leaderboard
            embed = discord.Embed(
                title="No-Show Stat-board",
                description="List of members with the most no-shows (sorted from highest to lowest):",
                color=discord.Color.orange()
            )

            guild = interaction.guild
            for i, (user_id, data) in enumerate(sorted_no_shows[:10]):  # Limit to top 10
                member = guild.get_member(int(user_id))
                member_name = member.display_name if member else f"Unknown User ({user_id})"
                embed.add_field(
                    name=f"{i + 1}. {member_name}",
                    value=f"No-Show Count: {data['count']}",
                    inline=False
                )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            logging.exception(f"Error in no_show_stat command: {e}")
            await interaction.followup.send(
                "An error occurred while generating the no-show stats. Please try again later.",
                ephemeral=True
            )


# Cog setup function
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(NoShowTracking(bot))
