#=================
# Imports. // Jack
#=================
import discord
import config
import secret
import logging
#from secret import JACK_ID
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput, Select, View

#===================
# Cog Setup. // Jack
#===================
class FeedbackCommands(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__()
        self.bot = bot

    # Step 1: Command for ZiT Feedback
    @discord.app_commands.command(name="zit-feedback", description="Submit feedback for a Zeus in Training")
    @discord.app_commands.guilds(config.GUILD_ID)
    @discord.app_commands.checks.has_any_role(config.CURATOR_ROLE_ID, config.ZEUS_ROLE_ID)
    async def zit_feedback(self, interaction: discord.Interaction, person: discord.Member):
        try:
            # Log the feedback target selection
            logging.info(f"ZiT feedback initiated by {interaction.user.mention} for {person.mention}")

            # Proceed directly to modal for feedback
            modal = FeedbackCommands.ZeusInTrainingFeedbackModal(self.bot, person)
            await interaction.response.send_modal(modal)

        except Exception as e:
            logging.exception(f"Error in zit_feedback command: {e}")
            await interaction.followup.send("An unexpected error occurred while processing your feedback.", ephemeral=True)

    # Step 2: Feedback Modal
    class ZeusInTrainingFeedbackModal(Modal):
        def __init__(self, bot: commands.Bot, person: discord.Member):
            super().__init__(title="Zeus in Training Feedback")
            self.bot = bot
            self.person = person  # Target of feedback

            # Text fields for feedback
            self.operation_name = TextInput(
                label="Operation Name & Date (DD/MM/YY)",
                style=discord.TextStyle.paragraph,
                placeholder="Enter the operation name and date",
                required=True
            )
            self.positive_points = TextInput(
                label="Things Done Well",
                style=discord.TextStyle.paragraph,
                placeholder="What did the Zeus in Training do well? Please reference the #zeus-guidelines.",
                required=True
            )
            self.improvement_points = TextInput(
                label="Points for Improvement",
                style=discord.TextStyle.paragraph,
                placeholder="What could be improved? Please reference the #zeus-guidelines.",
                required=True
            )

            self.add_item(self.operation_name)
            self.add_item(self.positive_points)
            self.add_item(self.improvement_points)

        async def on_submit(self, interaction: discord.Interaction):
            # Create the initial embed based on modal input
            embed = discord.Embed(
                title="**Zeus in Training Feedback Submission**",
                description=f"Feedback for {self.person.mention} submitted by {interaction.user.mention}",
                color=discord.Color.purple()
            )
            embed.add_field(name="Operation Name & Date", value=self.operation_name.value, inline=False)
            embed.add_field(name="Things Done Well", value=self.positive_points.value, inline=False)
            embed.add_field(name="Points for Improvement", value=self.improvement_points.value, inline=False)

            # Present the dropdown for recommendation
            view = FeedbackCommands.RecommendationSelectView(self.bot, self.person, embed)
            await interaction.response.send_message(
                content="Please select your recommendation for this Zeus in Training at this stage. Please reference the #zeus-guidelines",
                view=view,
                ephemeral=True
            )

    # Step 3: Recommendation Dropdown View
    class RecommendationSelectView(View):
        def __init__(self, bot: commands.Bot, person: discord.Member, embed: discord.Embed):
            super().__init__()
            self.bot = bot
            self.person = person
            self.embed = embed

            # Dropdown for Yes/No recommendation
            self.recommendation_select = Select(
                placeholder="Would you recommend the ZiT for full Zeus tags?",
                options=[
                    discord.SelectOption(label="Yes", description="Recommend for full Zeus tags"),
                    discord.SelectOption(label="No", description="Do not recommend for full Zeus tags"),
                ]
            )
            self.recommendation_select.callback = self.recommendation_select_callback
            self.add_item(self.recommendation_select)

        async def recommendation_select_callback(self, interaction: discord.Interaction):
            # Add the recommendation to the embed
            recommendation = self.recommendation_select.values[0]
            self.embed.add_field(
                name="Recommendation for Full Zeus Tags",
                value=f"**{recommendation}**",
                inline=False
            )

            # Fetch feedback channel
            feedback_channel = await self.bot.fetch_channel(config.ZEUS_FEEDBACK_CHANNEL_ID)

            # Send the feedback embed to the channel
            await feedback_channel.send(
                f"<@&{config.CURATOR_ROLE_ID}>, this feedback is awaiting your review.",
                embed=self.embed
            )

            # Acknowledge to the user
            await interaction.response.edit_message(
                content="Thank you for the feedback! Your recommendation has been recorded.",
                view=None
            )

#=================
# Cog End. // Jack
#=================
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(FeedbackCommands(bot))