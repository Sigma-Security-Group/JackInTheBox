import json
import discord
from discord.ext import commands
from discord_ui import UI, Modal, TextInput
import os
import asyncio
from secret import TOKEN

# Define intents and create bot instance
intents = discord.Intents.default()
intents.message_content = True  # Ensure the bot can read message content
bot = commands.Bot(command_prefix="!", intents=intents)
ui = UI(bot)

# Define the role required to use update commands
REQUIRED_ROLE = "Unit Staff"

# ID of the channel where update logs will be sent
LOG_CHANNEL_ID = 825039647456755772

# ID of the channel where update logs will be sent
LOG_CHANNEL_ID = 825039647456755772
TARGET_CHANNEL_ID = 1109263109526396938

# Dictionary to map categories to their display names and descriptions
category_mappings = {
    "certs": {"title": "Certifications", "description": "All achievable certifications."},
    "info": {"title": "Information", "description": "General information."},
    "docs": {"title": "Documentation", "description": "Official documentation and guidelines."},
    "ranks": {"title": "Ranks Information", "description": "Details on ranks and progression."},
    "badges": {"title": "Badges", "description": "All available badges and how to earn them."},
    "sme": {"title": "Lead Subject Matter Experts", "description": "List of lead subject matter experts."}
}

# Mapping of categories to their respective JSON file paths
CATEGORY_JSON_FILES = {
    "ranks": "Data/ranks.json",
    "certs": "Data/certs.json",
    "badges": "Data/badges.json",
    "sme": "Data/sme.json",
    "info": "Data/info.json",
    "docs": "Data/docs.json"
}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

def load_json(file_path):
    if not os.path.exists(file_path):
        # If the file doesn't exist, create an empty JSON structure
        with open(file_path, 'w') as f:
            json.dump({}, f)
    with open(file_path, 'r') as f:
        return json.load(f)

def save_json(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

# Function to log changes made via the update command
async def log_update(ctx, action, category, entry_name, old_desc=None, new_desc=None):
    # Get the user who made the change
    user = ctx.author

    # Prepare the embed message
    embed = discord.Embed(
        title=f"Update in `{category_mappings[category]['title']}` Category",
        description=f"**Action**: {action.capitalize()}\n**Entry**: {entry_name}",
        color=discord.Color.green(),
        timestamp=ctx.message.created_at  # Adds a timestamp to the embed
    )

    # Add details based on the action
    if action == 'add':
        embed.add_field(name="Description", value=new_desc, inline=False)
    elif action == 'update':
        embed.add_field(name="Old Description", value=old_desc, inline=False)
        embed.add_field(name="New Description", value=new_desc, inline=False)
    elif action == 'delete':
        embed.add_field(name="Deleted Description", value=old_desc, inline=False)

    # Footer with the user who performed the action
    embed.set_footer(text=f"Performed by: {user.name}#{user.discriminator}")

    # Send the embed to the specified log channel
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        await log_channel.send(embed=embed)

# Generalized command to display entries from a category
@bot.command(name='show', help="Shows all entries in a category. Usage: !show [category]")
async def show(ctx, category: str):
    category = category.lower()
    if category not in CATEGORY_JSON_FILES:
        await ctx.send(f"Invalid category. Available categories: {', '.join(CATEGORY_JSON_FILES.keys())}")
        return

    data = load_json(CATEGORY_JSON_FILES[category])

    if not data:
        await ctx.send(f"No entries found in `{category}` category.")
        return

    # Fetch the title and description from category_mappings
    category_info = category_mappings.get(category, {"title": category.capitalize(), "description": "No description available"})
    
    embed = discord.Embed(
        title=category_info["title"],  # Use title from category_mappings
        description=category_info["description"],  # Use description from category_mappings
        color=discord.Color.blue()
    )

    for name, description in data.items():
        embed.add_field(name=name, value=description, inline=False)

    await ctx.send(embed=embed)

# Command to interactively add, update, or delete entries
@bot.command(name='update', help="Add, update, or delete entries in a category.")
@commands.has_role(REQUIRED_ROLE)
async def update(ctx, category: str):
    category = category.lower()
    if category not in CATEGORY_JSON_FILES:
        await ctx.send(f"Invalid category. Available categories: {', '.join(CATEGORY_JSON_FILES.keys())}")
        return

    data = load_json(CATEGORY_JSON_FILES[category])

    await ctx.send(f"Do you want to `add`, `update`, or `delete` an entry in `{category}`? Type your choice.")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        operation_msg = await bot.wait_for('message', check=check, timeout=60.0)
        operation = operation_msg.content.lower()

        if operation not in ['add', 'update', 'delete']:
            await ctx.send("Invalid operation. Please start over and choose `add`, `update`, or `delete`.")
            return

        if operation == 'add':
            # Adding a new entry
            await ctx.send(f"Enter the **name** of the new entry to add to `{category}`:")
            name_msg = await bot.wait_for('message', check=check, timeout=60.0)
            name = name_msg.content.strip()

            if name in data:
                await ctx.send(f"An entry with the name `{name}` already exists in `{category}`. Operation cancelled.")
                return

            await ctx.send(f"Enter the **description** for `{name}`:")
            desc_msg = await bot.wait_for('message', check=check, timeout=300.0)  # Increased timeout for longer descriptions
            description = desc_msg.content.strip()

            data[name] = description
            save_json(CATEGORY_JSON_FILES[category], data)
            await ctx.send(f"Entry `{name}` added to `{category}` successfully.")

            # Log the addition
            await log_update(ctx, 'add', category, name, new_desc=description)

        elif operation == 'update':
            if not data:
                await ctx.send(f"No entries found in `{category}` to update.")
                return

            entries_list = '\n'.join([f"- {entry}" for entry in data.keys()])
            await ctx.send(f"Current entries in `{category}`:\n{entries_list}\n\nEnter the **name** of the entry you want to update:")

            name_msg = await bot.wait_for('message', check=check, timeout=60.0)
            name = name_msg.content.strip()

            if name not in data:
                await ctx.send(f"No entry named `{name}` found in `{category}`. Operation cancelled.")
                return

            old_description = data[name]  # Save old description for logging
            await ctx.send(f"Current description for `{name}`:\n{old_description}\n\nEnter the **new description**:")
            desc_msg = await bot.wait_for('message', check=check, timeout=300.0)
            new_description = desc_msg.content.strip()

            data[name] = new_description
            save_json(CATEGORY_JSON_FILES[category], data)
            await ctx.send(f"Entry `{name}` in `{category}` updated successfully.")

            # Log the update
            await log_update(ctx, 'update', category, name, old_desc=old_description, new_desc=new_description)

        elif operation == 'delete':
            if not data:
                await ctx.send(f"No entries found in `{category}` to delete.")
                return

            entries_list = '\n'.join([f"- {entry}" for entry in data.keys()])
            await ctx.send(f"Current entries in `{category}`:\n{entries_list}\n\nEnter the **name** of the entry you want to delete:")

            name_msg = await bot.wait_for('message', check=check, timeout=60.0)
            name = name_msg.content.strip()

            if name not in data:
                await ctx.send(f"No entry named `{name}` found in `{category}`. Operation cancelled.")
                return

            old_description = data[name]  # Save description for logging

            await ctx.send(f"Are you sure you want to delete `{name}` from `{category}`? Type `yes` to confirm.")

            confirm_msg = await bot.wait_for('message', check=check, timeout=30.0)
            if confirm_msg.content.lower() == 'yes':
                del data[name]
                save_json(CATEGORY_JSON_FILES[category], data)
                await ctx.send(f"Entry `{name}` deleted from `{category}` successfully.")

                # Log the deletion
                await log_update(ctx, 'delete', category, name, old_desc=old_description)
            else:
                await ctx.send("Deletion cancelled.")

    except asyncio.TimeoutError:
        await ctx.send("You took too long to respond. Please start the operation again.")

# ALL COMMANDS
@bot.command(name='certs', aliases=['certifications'], help="Shows all Certifications.")
async def certs(ctx):
    await show(ctx, 'certs')

@bot.command(name='badges', help="Shows all Badges.")
async def badges(ctx):
    await show(ctx, 'badges')

@bot.command(name='sme', aliases=['subjectmatterexperts'], help="Shows all SMEs.")
async def sme(ctx):
    await show(ctx, 'sme')

@bot.command(name='info', aliases=['information'], help="Shows all Information.")
async def info(ctx):
    await show(ctx, 'info')

@bot.command(name='docs', aliases=['documentation'], help="Shows all Documentation.")
async def docs(ctx):
    await show(ctx, 'docs')

@bot.command(name='ranks', help="Shows all Ranks.")
async def ranks(ctx):
    await show(ctx, 'ranks')

# Command that responds with a personalized message
@bot.command(name='habibi', help="Responds with a personalized message.")
async def habibi(ctx):
    # Get the user's name
    user_name = ctx.author.name
    # Create a personalized message
    response = f"{user_name} is Diddy's Habibi but loves Jack the most"
    # Send the response message
    await ctx.send(response)

# Command that responds with a specific message
@bot.command(name='evesjoke', help="Diddle East")
async def evesjoke(ctx):
    # Send the response message
    await ctx.send("Diddy is didling off to the diddle east. - Eve Makya")

# Error handler for missing role
@update.error
async def update_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send(f"This command can only be used by {REQUIRED_ROLE}.")

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
        except discord.Forbidden:
            print(f"Permission error: Bot does not have permission to send messages in channel {TARGET_CHANNEL_ID}")
        except Exception as e:
            print(f"An error occurred: {e}")
    else:
        print("Channel not found!")

bot.run(TOKEN)
