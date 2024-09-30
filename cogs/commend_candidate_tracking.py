import json
import random
import logging
import discord
import time
import config
from discord.ext import commands
from datetime import datetime, timedelta


# Logging setup. // Jack
logging.basicConfig(level=logging.INFO)

class CommendCandidateTracking(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    # =============================
    # Commendation Command. // Jack
    # =============================
    @discord.app_commands.command(name="commend", description="Commend a person")
    @discord.app_commands.guilds(config.GUILD_ID)
    async def commend(self, interaction: discord.Interaction, person: discord.Member, role: str, reason: str):
        try:
            # Log the command invocation. // Jack
            logging.info(f"Commend command invoked by {interaction.user.mention} for {person.mention} with role '{role}' and reason '{reason}'")

            # Fetch the guild and commendations channel. // Jack
            guild = self.bot.get_guild(config.GUILD_ID)
            channelCommendations = await guild.fetch_channel(config.COMMENDATIONS_CHANNEL_ID)

            # Load performance bonuses and timestamps. // Jack
            with open("Data/performance_bonus.json") as f:
                performance_data = json.load(f)

            userId = str(interaction.user.id)
            current_time = time.time()

            if userId not in performance_data:
                performance_data[userId] = {"count": 0, "totalBonus": 0, "timestamps": []}

            # Check how many bonuses were given in the last 24 hours (86400 seconds). // Jack
            valid_timestamps = [ts for ts in performance_data[userId]["timestamps"] if current_time - ts < 86400]

            if len(valid_timestamps) >= 3:
                # User has already received 3 bonuses in the last 24 hours. // Jack
                performanceBonus = 0
                performance_data[userId]["count"] = len(valid_timestamps)  # Update count to valid bonuses. // Jack
            else:
                # Performance Bonus Generator
                performanceBonus = round(random.randint(1000, 10000) + random.uniform(0, 1), 2)
                valid_timestamps.append(current_time)  # Add current timestamp for the bonus. // Jack
                performance_data[userId]["count"] = len(valid_timestamps)
                performance_data[userId]["totalBonus"] += performanceBonus
                performance_data[userId]["timestamps"] = valid_timestamps

            with open("Data/performance_bonus.json", "w") as f:
                json.dump(performance_data, f, indent=4)

            # Send a tagging message to inform who commended whom. // Jack
            await channelCommendations.send(
                f"**Commended: **{person.mention}\n"
                f"**By: **{interaction.user.mention}\n"
                f"**Role: **{role}\n"
                f"**Reason: **{reason}\n"
                f"The Preformance Bonus of ${performanceBonus:,.2f} has been wired to your account."
            )

            # Respond to the user with an ephemeral message. // Jack
            await interaction.response.send_message(
                f"Thank you for commending! It has been submitted successfully in {channelCommendations.mention}.",
                ephemeral=True,
                delete_after=10.0
            )

        except Exception as e:
            logging.exception(f"Error in commend command: {e}")
            await interaction.response.send_message("An unexpected error occurred while processing your commendation.",
                ephemeral=True)

    #===================================
    # Performance Bonus Tracker. // Jack
    #===================================
    @discord.app_commands.command(name="performance-bonus", description="Track how much you have earned in performance bonuses.")
    @discord.app_commands.guilds(config.GUILD_ID)
    async def performancebonus(self, interaction: discord.Interaction):
        with open("Data/performance_bonus.json") as f:
            performance_bonus = json.load(f)

        userId = str(interaction.user.id)
        totalBonus = performance_bonus.get(userId, {"totalBonus": 0})["totalBonus"]
        await interaction.response.send_message(f"You have earned a total of **${totalBonus:,.2f}** in performance bonuses.", ephemeral=False)

    # ===================================
    # Candidate Tracking Command. // Jack
    # ===================================
    @discord.app_commands.command(name="track-a-candidate", description="Track a candidate's progress through operations.")
    @discord.app_commands.guilds(config.GUILD_ID)
    @discord.app_commands.checks.has_any_role(config.UNIT_STAFF_ROLE_ID, config.CURATOR_ROLE_ID, config.ZEUS_ROLE_ID, config.ZEUSINTRAINING_ROLE_ID)
    async def track_a_candidate(self, interaction: discord.Interaction, member: discord.Member):

        # Acknowledge the interaction early. // Jack
        await interaction.response.send_message(f"Tracking progress for {member.display_name}", ephemeral=True)

        # Fetch the Commendations channel // Jack
        channelCommendations = self.bot.get_channel(config.COMMENDATIONS_CHANNEL_ID)
        if not channelCommendations:
            await interaction.followup.send("Commendations channel not found.", ephemeral=True)
            return

        # Initialize operation count for the selected member. // Jack
        operation_count = 1

        # Recent Messages Timer to ensure the Candidate does not get mutiple tracks for one operation. // Jack & Adrian
        mostRecentMessageTime = None

        # Fetch unit staff role // Jack
        guild = interaction.guild
        unit_staff_role = guild.get_role(config.UNIT_STAFF_ROLE_ID)

        # Check if member has reached 3/3 operations to be promoted. // Jack
        async for message in channelCommendations.history(limit=1000):
            # Ensure the message contains the keyword and mentions the member. // Jack
            if config.OPERATION_KEYWORD.lower() in message.content.lower() and member in message.mentions:
                operation_count += 1
                if mostRecentMessageTime is None or mostRecentMessageTime < message.created_at:
                    mostRecentMessageTime = message.created_at.replace(tzinfo=None)

        print(mostRecentMessageTime)
        if mostRecentMessageTime is not None and datetime.utcnow() - mostRecentMessageTime < timedelta(hours=1):
            await interaction.followup.send("Error code CCT-0004 has occurred. Member has already been tracked for this operation. Please try again. If the error persists, please notify Jack MacTavish.", ephemeral=True)
            logging.debug("Skip tracking due to recent message.")
            return

        # Check for the total number of operation attendance of the command target. // Jack
        if operation_count >= config.TOTAL_OPERATIONS:
            # The command target has reached 3/3 operations. Send eligibility message. // Jack
            message_content = (
                f"{member.mention}, after demonstrating valor, resilience, and unwavering dedication across 3 successful deployments, "
                f"you’ve proven yourself to be a true asset to this unit. Your commitment to excellence and operational prowess has not gone unnoticed.\n\n"
                f"With your final deployment logged, you are now ready to take the next step and join the ranks of Sigma. This is no ordinary transition. Sigma is a brotherhood "
                f"of the elite, those who have earned their place through blood, sweat, and loyalty.\n\n"
                f"Welcome to Sigma. Your journey has only just begun. The battlefield awaits, and now, you stand among the best.\n\n"
                f"{unit_staff_role.mention}, please fill in the necessary paperwork and notify HR."
            )
            await channelCommendations.send(message_content)
        else:
            # Calculate remaining operations. // Jack
            remaining_ops = config.TOTAL_OPERATIONS - operation_count

            # Send status update message. // Jack
            message_content = (
                f"{member.mention} has attended an operation and is on their way to becoming a Sigma Associate. "
                f"They have {remaining_ops} operations left."
            )
            await channelCommendations.send(message_content)

async def setup(bot):
    await bot.add_cog(CommendCandidateTracking(bot))
