import json
import random
import logging
import discord
import time
import config
import asyncio
from discord.ext import commands
from discord import app_commands
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
            if person.id == interaction.user.id:
                await interaction.response.send_message(
                    "You cheeky bugger! You cannot commend yourself.", ephemeral=True
                )
                return

            logging.info(f"Commend command invoked by {interaction.user.mention} for {person.mention} with role '{role}' and reason '{reason}'")

            guild = self.bot.get_guild(config.GUILD_ID)
            channel_commendations = await guild.fetch_channel(config.COMMENDATIONS_CHANNEL_ID)

            # Commented out performance bonus logic
            # with open("Data/performance_bonus.json") as f:
            #     performance_data = json.load(f)
            
            # user_id = str(person.id)
            # current_time = time.time()
            
            # if user_id not in performance_data:
            #     performance_data[user_id] = {"count": 0, "totalBonus": 0, "timestamps": []}
            
            # valid_timestamps = [ts for ts in performance_data[user_id]["timestamps"] if current_time - ts < 86400]
            
            # if len(valid_timestamps) >= 3:
            #     performance_bonus = 0
            # else:
            #     performance_bonus = round(random.randint(1500, 10000) + random.uniform(0, 1), 2)
            #     valid_timestamps.append(current_time)
            #     performance_data[user_id]["count"] = len(valid_timestamps)
            #     if performance_bonus > 0:
            #         performance_data[user_id]["totalBonus"] += performance_bonus
            #     performance_data[user_id]["timestamps"] = valid_timestamps
            
            # with open("Data/performance_bonus.json", "w") as f:
            #     json.dump(performance_data, f, indent=4)

            await channel_commendations.send(
                f"{person.mention} has been commended by {interaction.user.mention}!"
            )

            embed = discord.Embed(
                title="Commendation Received!",
                color=discord.Color.green()
            )
            embed.add_field(name="Commended", value=person.mention, inline=False)
            embed.add_field(name="By", value=interaction.user.mention, inline=False)
            embed.add_field(name="Role", value=role, inline=False)
            embed.add_field(name="Reason", value=reason, inline=False)
            # embed.add_field(
            #     name="Performance Bonus",
            #     value=f"£{performance_bonus:,.2f}" if performance_bonus > 0 else "No bonus awarded.",
            #     inline=False
            # )
            embed.set_footer(text="Great work deserves recognition!")

            await channel_commendations.send(embed=embed)

            await interaction.response.send_message(
                f"Thank you for commending! It has been submitted successfully in {channel_commendations.mention}.",
                ephemeral=True,
                delete_after=10.0
            )
        except Exception as e:
            logging.exception(f"Error in commend command: {e}")
            await interaction.response.send_message(
                "An unexpected error occurred while processing your commendation.",
                ephemeral=True
            )

    # ===================================
    # Commented out Performance Bonus Commands // Jack
    # ===================================
    # @discord.app_commands.command(name="performance-bonus", description="Track how much you have earned in performance bonuses.")
    # @discord.app_commands.guilds(config.GUILD_ID)
    # async def performancebonus(self, interaction: discord.Interaction) -> None:
    #     with open("Data/performance_bonus.json") as f:
    #         performance_bonus = json.load(f)
    #
    #     user_id = str(interaction.user.id)
    #     total_bonus = performance_bonus.get(user_id, {"totalBonus": 0})["totalBonus"]
    #     await interaction.response.send_message(f"You have earned a total of **£{total_bonus:,.2f}** in performance bonuses.", ephemeral=False)

    # @discord.app_commands.command(name="performance-bonus-leaderboard", description="Sigma's top performers.")
    # @discord.app_commands.guilds(config.GUILD_ID)
    # async def list_bonuses(self, interaction: discord.Interaction):
    #     try:
    #         await interaction.response.defer(thinking=True)
    #
    #         with open("Data/performance_bonus.json") as f:
    #             performance_data = json.load(f)
    #
    #         bonus_list = []
    #         guild = interaction.guild
    #
    #         for user_id, data in performance_data.items():
    #             if data["totalBonus"] > 0:
    #                 member = guild.get_member(int(user_id))
    #                 if member:
    #                     bonus_list.append((member.display_name, data["totalBonus"]))
    #
    #         bonus_list.sort(key=lambda x: x[1], reverse=True)
    #
    #         if not bonus_list:
    #             embed = discord.Embed(
    #                 title="Performance Bonuses",
    #                 description="No members have earned any performance bonuses yet.",
    #                 colour=discord.Colour.green()
    #             )
    #             await interaction.followup.send(embed=embed)
    #             return
    #
    #         MAX_FIELDS = 25
    #         embed = discord.Embed(
    #             title="Performance Bonuses Leaderboard",
    #             description="Here is the leaderboard of operators with the highest performance bonuses:",
    #             colour=discord.Colour.green()
    #         )
    #         for i, (user_name, total_bonus) in enumerate(bonus_list):
    #             embed.add_field(name=f"{i + 1}. {user_name}", value=f"£{total_bonus:,.2f}", inline=False)
    #         await interaction.followup.send(embed=embed)
    #     except Exception as e:
    #         logging.error(f"Error while listing performance bonuses: {e}")
    #         await interaction.followup.send("An error occurred while retrieving the list of bonuses.", ephemeral=True)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CommendCandidateTracking(bot))
