import logging
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta, timezone

# Logging setup
logging.basicConfig(level=logging.INFO)

class BanManager(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__()
        self.bot = bot

    @app_commands.command(name="ban", description="Ban a member with reason, duration, and appeal status.")
    @app_commands.default_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, duration: int, appealable: bool, reason: str):
        try:
            if duration <= 0:
                await interaction.response.send_message("Duration must be at least 1 day.", ephemeral=True)
                return

            if len(reason.strip()) == 0:
                await interaction.response.send_message("You must provide a reason for the ban.", ephemeral=True)
                return

            # Calculate unban date
            unban_date = datetime.now(timezone.utc) + timedelta(days=duration)
            appeal_status = "Yes" if appealable else "No"

            # Create Embed
            embed = discord.Embed(
                title="You Have Been Banned from Sigma Security Group",
                color=discord.Color.red()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Duration", value=f"{duration} days", inline=False)
            embed.add_field(name="Appeal Status", value=appeal_status, inline=False)
            embed.add_field(
                name="How to Appeal", 
                value="If your ban is appealable, contact the Dierector or Deputy Director via [appeal instructions].",
                inline=False
            )
            embed.set_footer(text=f"Your ban was made by {interaction.user.display_name}")

            try:
                await member.send(embed=embed)
                logging.info(f"Ban notification sent to {member}")
            except discord.Forbidden:
                await interaction.response.send_message(f"Could not DM {member.mention} about the ban.", ephemeral=True)
                logging.warning(f"Failed to DM {member}")
                return

            # Ban the user
            await member.ban(reason=reason)
            logging.info(f"{member} banned successfully")

            # Confirmation message
            await interaction.response.send_message(f"{member.mention} has been banned for {duration} days. Reason: {reason}")

            # Logging
            logging_channel = self.bot.get_channel(config.REPORT_LOG_CHANNEL_ID)
            if logging_channel:
                log_embed = discord.Embed(
                    title="Member Banned",
                    color=discord.Color.orange()
                )
                log_embed.add_field(name="Member", value=f"{member} ({member.id})", inline=False)
                log_embed.add_field(name="Moderator", value=f"{interaction.user} ({interaction.user.id})", inline=False)
                log_embed.add_field(name="Reason", value=reason, inline=False)
                log_embed.add_field(name="Duration", value=f"{duration} days", inline=False)
                log_embed.add_field(name="Appealable", value=appeal_status, inline=False)
                log_embed.set_footer(text=f"Unban Date: {unban_date.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                await logging_channel.send(embed=log_embed)
            else:
                logging.warning("Logging channel not found. Ban details will not be logged.")

        except Exception as e:
            logging.exception(f"Error in ban command: {e}")
            await interaction.response.send_message("An unexpected error occurred while processing the ban.", ephemeral=True)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BanManager(bot))
