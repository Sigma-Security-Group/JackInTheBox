import json
import random
import logging
import discord
import time
import config
from discord.ext import commands
from datetime import datetime, timedelta, timezone


# Logging setup. // Jack
logging.basicConfig(level=logging.INFO)
CURRENT_TIME = datetime.now(timezone.utc)

class CommendCandidateTracking(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__()
        self.bot = bot

    # =============================
    # Commendation Command. // Jack
    # =============================
    @discord.app_commands.command(name="commend", description="Commend a person")
    @discord.app_commands.guilds(config.GUILD_ID)
    async def commend(self, interaction: discord.Interaction, person: discord.Member, role: str, reason: str) -> None:
        try:
            # Log the command invocation. // Jack
            logging.info(f"Commend command invoked by {interaction.user.mention} for {person.mention} with role '{role}' and reason '{reason}'")

            # Fetch the guild and commendations channel. // Jack
            guild = self.bot.get_guild(config.GUILD_ID)
            channel_commendations = await guild.fetch_channel(config.COMMENDATIONS_CHANNEL_ID)

            # Load performance bonuses and timestamps. // Jack
            with open("Data/performance_bonus.json") as f:
                performance_data = json.load(f)

            user_id = str(person.id)
            current_time = time.time()

            if user_id not in performance_data:
                performance_data[user_id] = {"count": 0, "totalBonus": 0, "timestamps": []}

            # Check how many bonuses were given in the last 24 hours (86400 seconds). // Jack
            valid_timestamps = [ts for ts in performance_data[user_id]["timestamps"] if current_time - ts < 86400]

            if len(valid_timestamps) >= 3:
                # User has already received 3 bonuses in the last 24 hours. // Jack
                performance_bonus = 0
                performance_data[user_id]["count"] = len(valid_timestamps)  # Update count to valid bonuses. // Jack
            else:
                # Performance Bonus Generator
                performance_bonus = round(random.randint(1500, 10000) + random.uniform(0, 1), 2)
                valid_timestamps.append(current_time)  # Add current timestamp for the bonus. // Jack
                performance_data[user_id]["count"] = len(valid_timestamps)
                if performance_bonus > 0:
                    performance_data[user_id]["totalBonus"] += performance_bonus
                performance_data[user_id]["timestamps"] = valid_timestamps

            with open("Data/performance_bonus.json", "w") as f:
                json.dump(performance_data, f, indent=4)

            # Send a tagging message to inform who commended whom. // Jack
            await channel_commendations.send(
                f"**Commended: **{person.mention}\n"
                f"**By: **{interaction.user.mention}\n"
                f"**Role: **{role}\n"
                f"**Reason: **{reason}\n"
                f"The Performance Bonus of £{performance_bonus:,.2f} has been wired to your account."
            )

            # Respond to the user with an ephemeral message. // Jack
            await interaction.response.send_message(
                f"Thank you for commending! It has been submitted successfully in {channel_commendations.mention}.",
                ephemeral=True,
                delete_after=10.0
            )

        except Exception as e:
            logging.exception(f"Error in commend command: {e}")
            await interaction.response.send_message("An unexpected error occurred while processing your commendation.",
                ephemeral=True)

    # ===================================
    # Performance Bonus Tracker. // Jack
    # ===================================
    @discord.app_commands.command(name="performance-bonus", description="Track how much you have earned in performance bonuses.")
    @discord.app_commands.guilds(config.GUILD_ID)
    async def performancebonus(self, interaction: discord.Interaction) -> None:
        with open("Data/performance_bonus.json") as f:
            performance_bonus = json.load(f)

        user_id = str(interaction.user.id)
        total_bonus = performance_bonus.get(user_id, {"totalBonus": 0})["totalBonus"]
        await interaction.response.send_message(f"You have earned a total of **£{total_bonus:,.2f}** in performance bonuses.", ephemeral=False)

    # ===================================
    # Candidate Tracking Command. // Jack
    # ===================================
    @discord.app_commands.command(name="track-a-candidate", description="Track a candidate's progress through operations.")
    @discord.app_commands.guilds(config.GUILD_ID)
    @discord.app_commands.checks.has_any_role(config.UNIT_STAFF_ROLE_ID, config.CURATOR_ROLE_ID, config.ZEUS_ROLE_ID, config.ZEUSINTRAINING_ROLE_ID)
    async def track_a_candidate(self, interaction: discord.Interaction, member: discord.Member) -> None:
        # Acknowledge the interaction early. // Jack
        await interaction.response.send_message(f"Tracking progress for {member.display_name}", ephemeral=True)

        # Fetch the Commendations channel // Jack
        channel_commendations = self.bot.get_channel(config.COMMENDATIONS_CHANNEL_ID)
        if not channel_commendations:
            await interaction.followup.send("Commendations channel not found.", ephemeral=True)
            return

        # Initialise operation count and most recent message time for the selected member. // Jack
        operation_count = 1
        most_recent_message_time = None

        # Check for the command target's participation in operations. // Jack
        async for message in channel_commendations.history(limit=500):
            if config.OPERATION_KEYWORD.lower() in message.content.lower() and member in message.mentions:
                operation_count += 1
                if most_recent_message_time is None or message.created_at > most_recent_message_time:
                    most_recent_message_time = message.created_at

        # Get the current time in UTC and make it timezone-aware. // Jack
        current_time = datetime.now(timezone.utc)

        # Ensure the Candidate does not get tracked multiple times for one operation. // Jack & Adrian
        if most_recent_message_time and current_time - most_recent_message_time < timedelta(seconds=1):
            await interaction.followup.send("Error code CCT-0004: Member has already been tracked for this operation. Please try again later. If the error persists, notify Jack MacTavish.", ephemeral=True)
            logging.debug("Skip tracking due to recent message.")
            return

        # Check if the member has completed enough operations. // Jack
        if operation_count >= config.TOTAL_OPERATIONS:
            # The command target has reached the required operations. // Jack
            guild = interaction.guild
            unit_staff_role = guild.get_role(config.UNIT_STAFF_ROLE_ID)

            message_content = (
                f"{member.mention}, after demonstrating valour, resilience, and unwavering dedication across 3 successful deployments, "
                f"you’ve proven yourself to be a true asset to this unit. Your commitment to excellence and operational prowess has not gone unnoticed.\n\n"
                f"Welcome to Sigma. Your journey has only just begun. The battlefield awaits, and now, you stand among the best.\n\n"
                f"{unit_staff_role.mention}, please fulfil the necessary paperwork and notify HR."
            )
            await channel_commendations.send(message_content)
        else:
            # Calculate remaining operations and send a status update. // Jack
            remaining_ops = config.TOTAL_OPERATIONS - operation_count
            await channel_commendations.send(
                f"{member.mention} has attended an operation and is on their way to becoming a Sigma Associate. "
                f"They have {remaining_ops} operations left."
            )

    # ==============================================
    # Performance Bonus Leaderboard Command. // Jack
    # ==============================================
    @discord.app_commands.command(name="performance-bonus-leaderboard", description="Sigma's top performers.")
    @discord.app_commands.guilds(config.GUILD_ID)  # Ensure the command is only available in your guild
    async def list_bonuses(self, interaction: discord.Interaction):
        try:
            # Defer the interaction to prevent timeouts
            await interaction.response.defer(thinking=True)

            # Load performance bonus data
            with open("Data/performance_bonus.json") as f:
                performance_data = json.load(f)

            bonus_list = []
            for user_id, data in performance_data.items():
                if data["totalBonus"] > 0:
                    member = await self.bot.fetch_user(int(user_id))  # Fetch user data
                    bonus_list.append((member.display_name, data["totalBonus"]))

            # Sort the list by totalBonus in descending order
            bonus_list.sort(key=lambda x: x[1], reverse=True)

            # Check if the bonus list is empty
            if not bonus_list:
                embed = discord.Embed(
                    title="Performance Bonuses",
                    description="No members have earned any performance bonuses yet.",
                    colour=discord.Colour.green()
                )
                await interaction.followup.send(embed=embed)
                return

            # Build embeds with a field limit
            MAX_FIELDS = 25
            embed = discord.Embed(
                title="Performance Bonuses Leaderboard",
                description="Here is the leaderboard of operators with the highest performance bonuses:",
                colour=discord.Colour.green()
            )

            for i, (user_name, total_bonus) in enumerate(bonus_list):
                embed.add_field(name=f"{i + 1}. {user_name}", value=f"£{total_bonus:,.2f}", inline=False)

                # If 25 fields are reached, send the current embed and start a new one
                if (i + 1) % MAX_FIELDS == 0:
                    await interaction.followup.send(embed=embed)
                    embed = discord.Embed(
                        title="Performance Bonuses Leaderboard (Continued)",
                        colour=discord.Colour.green()
                    )

            # Send the final embed
            if len(embed.fields) > 0:
                await interaction.followup.send(embed=embed)

        except Exception as e:
            logging.error(f"Error while listing performance bonuses: {e}")
            await interaction.followup.send("An error occurred while retrieving the list of bonuses.", ephemeral=True)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CommendCandidateTracking(bot))