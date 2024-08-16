import discord
from discord.ext import commands
from discord_ui import UI, Modal, TextInput
from secret import TOKEN

intents = discord.Intents.default()
intents.message_content = True  # Required to read message content

bot = commands.Bot(command_prefix='!', intents=intents)
ui = UI(bot)

# Specify the ID of the channel where you want to send the commendations
TARGET_CHANNEL_ID = 1109263109526396938  # Replace with your target channel ID

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')

@bot.command()
async def commend(ctx):
    # Delete the user's command message
    await ctx.message.delete()
    
    # Create the modal
    modal = Modal(title="Commendation Form")
    
    # Add text input fields
    commended_input = TextInput(label="Commended", custom_id="commended_input", style=TextInput.Style.short)
    by_input = TextInput(label="By", custom_id="by_input", style=TextInput.Style.short)
    role_input = TextInput(label="Role", custom_id="role_input", style=TextInput.Style.short)
    reason_input = TextInput(label="Reason", custom_id="reason_input", style=TextInput.Style.long)
    
    # Add fields to modal
    modal.add_item(commended_input)
    modal.add_item(by_input)
    modal.add_item(role_input)
    modal.add_item(reason_input)

    # Send the modal
    await ctx.send_modal(modal)

@ui.modal_submit('commended_input')
async def on_modal_submit(ctx, commended, by, role, reason):
    # Get the target channel
    channel = bot.get_channel(TARGET_CHANNEL_ID)
    
    if channel:
        try:
            # Format the message
            message = (
                f"**Commended:** {commended}\n"
                f"**By:** {by}\n"
                f"**Role:** {role}\n"
                f"**Reason:** {reason}"
            )
            
            # Send the message to the specified channel
            await channel.send(message)
            
            # Acknowledge the modal submission
            await ctx.send("Your commendation has been recorded!")
        except discord.Forbidden:
            print(f"Permission error: Bot does not have permission to send messages in channel {TARGET_CHANNEL_ID}")
        except Exception as e:
            print(f"An error occurred: {e}")
    else:
        print("Channel not found!")

bot.run(TOKEN)
