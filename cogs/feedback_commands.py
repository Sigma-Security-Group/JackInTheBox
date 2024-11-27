#=================
# Imports. // Jack
#=================
import discord
import config
import secret
from secret import JACK_ID
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

    #============================
    # Bot Feedback Modal. // Jack
    #============================
    class BotFeedBackModal(Modal):
        def __init__(self, bot: commands.Bot):  # Accept bot instance
            super().__init__(title="Jack In The Box (Secure A.I) Feedback")
            self.bot = bot  # Store the bot instance

            # Text field for the feedback. // Jack
            self.feedback_input = TextInput(
                label="Feedback", 
                style=discord.TextStyle.paragraph, 
                placeholder="Enter your feedback here.", 
                required=True
            )

            self.add_item(self.feedback_input)
        
        async def on_submit(self, interaction: discord.Interaction):  
            feedback = self.feedback_input.value
            user = interaction.user  # Command User. // Jack

            embed = discord.Embed(
                title="**Feedback Submission**", 
                description=f"Feedback from {user.mention}", 
                color=discord.Color.yellow()
            )

            embed.add_field(
                name="Feedback:", 
                value=feedback, 
                inline=False
            )

            await (await self.bot.fetch_user(JACK_ID)).send(embed=embed)  
            await interaction.response.send_message("Thank you for the feedback. - Jack MacTavish", ephemeral=True)

    #===============================
    # Zeus in Training Feedback Modal
    #===============================
    class ZeusInTrainingFeedback(Modal):
        def __init__(self, bot: commands.Bot):
            super().__init__(title="Zeus in Training Feedback")
            self.bot = bot

            # Text fields for feedback
            self.zit_fb_name = TextInput(
                label="Name of Zeus",
                style=discord.TextStyle.paragraph,
                placeholder="",
                required=True
            )
            self.zit_op_name = TextInput(
                label="Operation Name & Date (DD/MM/YY)",
                style=discord.TextStyle.paragraph,
                placeholder="",
                required=True
            )
            self.zit_op_details = TextInput(
                label="Operation Details",
                style=discord.TextStyle.paragraph,
                placeholder="",
                required=True
            )
            self.zit_pos_points = TextInput(
                label="Zeus In Training Positive Points",
                style=discord.TextStyle.paragraph,
                placeholder="",
                required=True
            )
            self.zit_poi = TextInput(
                label="Points of Improvement",
                style=discord.TextStyle.paragraph,
                placeholder="",
                required=True
            )

            self.add_item(self.zit_fb_name)
            self.add_item(self.zit_op_name)
            self.add_item(self.zit_op_details)
            self.add_item(self.zit_pos_points)
            self.add_item(self.zit_poi)

        async def on_submit(self, interaction: discord.Interaction):
            embed = discord.Embed(
                title="**Zeus in Training Feedback Submission**",
                description=f"Feedback from {interaction.user.mention}",
                color=discord.Color.purple()
            )

            embed.add_field(name="Zeus in Training Name", value=self.zit_fb_name.value, inline=False)
            embed.add_field(name="Operation Name & Date", value=self.zit_op_name.value, inline=False)
            embed.add_field(name="Operation Details", value=self.zit_op_details.value, inline=False)
            embed.add_field(name="Things Done Well", value=self.zit_pos_points.value, inline=False)
            embed.add_field(name="Points of Improvement", value=self.zit_poi.value, inline=False)

            view = FeedbackCommands.RecommendationSelectView(self.bot, embed)
            await interaction.response.send_message("Please select your recommendation from the dropdown below.", view=view, ephemeral=True)

    #====================================
    # Recommendation Dropdown View
    #====================================
    class RecommendationSelectView(View):
        def __init__(self, bot: commands.Bot, embed: discord.Embed):
            super().__init__()
            self.bot = bot
            self.embed = embed

            # Dropdown for Yes/No recommendation
            self.recommendation_select = Select(
                placeholder="Would you recommend the ZiT for full Zeus tags?",
                options=[
                    discord.SelectOption(label="Yes", description="Recommend for full Zeus tags"),
                    discord.SelectOption(label="No", description="Do not recommend for full Zeus tags")
                ]
            )

            self.recommendation_select.callback = self.recommendation_select_callback
            self.add_item(self.recommendation_select)

        async def recommendation_select_callback(self, interaction: discord.Interaction):
            recommendation = self.recommendation_select.values[0]
            self.embed.add_field(
                name="Recommendation for Full Zeus Tags",
                value=f"**{recommendation}**",
                inline=False
            )

            zit_fb_channel = await self.bot.fetch_channel(config.ZEUS_FEEDBACK_CHANNEL_ID)

            await zit_fb_channel.send(f"<@&{config.CURATOR_ROLE_ID}>, This feedback is awaiting your review.")
            await zit_fb_channel.send(embed=self.embed)

            await interaction.response.edit_message(content="Thank you for the feedback! Your recommendation has been recorded.", view=None)

    #===========================================
    # Jack In The Box Feedback Command. // Jack
    #===========================================
    # @app_commands.command(name="secure-ai-feedback", description="Submit feedback for Sigma's Secure A.I")
    # @app_commands.guilds(config.GUILD_ID)
    # async def secure_ai_feedback(self, interaction: discord.Interaction): 
    #     modal = self.BotFeedBackModal(self.bot) 
    #     await interaction.response.send_modal(modal)  

    #===========================================
    # Zeus in Training Feedback Command. // Jack
    #===========================================
    @app_commands.command(name="zit-feedback", description="Submit feedback for Zeus in Training")
    @app_commands.guilds(config.GUILD_ID)
    @discord.app_commands.checks.has_any_role(config.CURATOR_ROLE_ID, config.ZEUS_ROLE_ID)
    async def zit_feedback(self, interaction: discord.Interaction): 
        modal = self.ZeusInTrainingFeedback(self.bot) 
        await interaction.response.send_modal(modal)  

#=================
# Cog End. // Jack
#=================
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(FeedbackCommands(bot))