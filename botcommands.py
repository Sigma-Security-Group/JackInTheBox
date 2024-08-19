import json
import os
import asyncio
import logging
import discord
from discord.ext import commands

from secret import TOKEN

# Define intents and create bot instance
intents = discord.Intents.default()
intents.message_content = True  # Ensure the bot can read message content
bot = commands.Bot(command_prefix="!", intents=intents)

# Define the role required to use update commands
REQUIRED_ROLE = "Unit Staff"

# ID of the channel where update logs will be sent
AUDIT_LOGS_CHANNEL_ID = 825039647456755772
COMMENDATIONS_CHANNEL_ID = 1109263109526396938 # Replace with the actual ID of the commendations channel

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
        with open(file_path, 'w') as f:
            json.dump({}, f)
    with open(file_path, 'r') as f:
        return json.load(f)

def save_json(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

async def log_update(ctx, action, category, entry_name, old_desc=None, new_desc=None):
    user = ctx.author

    embed = discord.Embed(
        title=f"Update in `{category_mappings[category]['title']}` Category",
        description=f"**Action**: {action.capitalize()}\n**Entry**: {entry_name}",
        color=discord.Color.green(),
        timestamp=ctx.message.created_at
    )

    if action == 'add':
        embed.add_field(name="Description", value=new_desc, inline=False)
        logging.info(f"{user.name}#{user.discriminator} added entry '{entry_name}' to '{category}' with description '{new_desc}'")
    elif action == 'update':
        embed.add_field(name="Old Description", value=old_desc, inline=False)
        embed.add_field(name="New Description", value=new_desc, inline=False)
        logging.info(f"{user.name}#{user.discriminator} updated entry '{entry_name}' in '{category}' with new description '{new_desc}' from old description '{old_desc}'")
    elif action == 'delete':
        embed.add_field(name="Deleted Description", value=old_desc, inline=False)
        logging.info(f"{user.name}#{user.discriminator} deleted entry '{entry_name}' from '{category}' with description '{old_desc}'")

    embed.set_footer(text=f"Performed by: {user.name}#{user.discriminator}")

    log_channel = bot.get_channel(AUDIT_LOGS_CHANNEL_ID)
    if log_channel is not None:
        await log_channel.send(embed=embed)

@bot.command(name='show', help="Shows all entries in a category. Usage: !show [category]")  # type: ignore
async def show(ctx, category: str):
    category = category.lower()
    if category not in CATEGORY_JSON_FILES:
        await ctx.send(f"Invalid category. Available categories: {', '.join(CATEGORY_JSON_FILES.keys())}")
        return

    data = load_json(CATEGORY_JSON_FILES[category])

    if not data:
        await ctx.send(f"No entries found in `{category}` category.")
        return

    category_info = category_mappings.get(category, {"title": category.capitalize(), "description": "No description available"})
    
    embed = discord.Embed(
        title=category_info["title"],
        description=category_info["description"],
        color=discord.Color.blue()
    )

    for name, description in data.items():
        embed.add_field(name=name, value=description, inline=False)

    await ctx.send(embed=embed)

@bot.command(name='update', help="Add, update, or delete entries in a category.")  # type: ignore
@commands.has_role(REQUIRED_ROLE)
async def update(ctx, category: str):
    category = category.lower()
    if category not in CATEGORY_JSON_FILES:
        await ctx.send(f"Invalid category. Available categories: {', '.join(CATEGORY_JSON_FILES.keys())}")
        return

    data = load_json(CATEGORY_JSON_FILES[category])

    await ctx.send(f"Do you want to `add`, `update`, or `delete` an entry in `{category}`? Type your choice.")

    def matchesContext(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        operation_msg = await bot.wait_for('message', check=matchesContext, timeout=60.0)
        operation = operation_msg.content.strip().lower()

        if operation == "cancel":
            await ctx.send("Cancelled.")
            return

        if operation not in ['add', 'update', 'delete']:
            await ctx.send("Invalid operation. Please start over and choose `add`, `update`, or `delete`.")
            return

        if operation == 'add':
            await ctx.send(f"Enter the **name** of the new entry to add to `{category}`:")
            name_msg = await bot.wait_for('message', check=matchesContext, timeout=60.0)
            name = name_msg.content.strip()

            if name.lower() == "cancel":
                await ctx.send("Cancelled.")
                return

            if name in data:
                await ctx.send(f"An entry with the name `{name}` already exists in `{category}`. Operation cancelled.")
                return

            await ctx.send(f"Enter the **description** for `{name}`:")
            desc_msg = await bot.wait_for('message', check=matchesContext, timeout=300.0)
            description = desc_msg.content.strip()

            data[name] = description
            save_json(CATEGORY_JSON_FILES[category], data)
            await ctx.send(f"Entry `{name}` added to `{category}` successfully.")

            await log_update(ctx, 'add', category, name, new_desc=description)

        elif operation == 'update':
            if not data:
                await ctx.send(f"No entries found in `{category}` to update.")
                return

            entries_list = '\n'.join([f"- {entry}" for entry in data.keys()])
            await ctx.send(f"Current entries in `{category}`:\n{entries_list}\n\nEnter the **name** of the entry you want to update:")

            name_msg = await bot.wait_for('message', check=matchesContext, timeout=60.0)
            name = name_msg.content.strip()

            if name.lower() == "cancel":
                await ctx.send("Cancelled.")
                return

            if name not in data:
                await ctx.send(f"No entry named `{name}` found in `{category}`. Operation cancelled.")
                return

            old_description = data[name]
            await ctx.send(f"Current description for `{name}`:\n{old_description}\n\nEnter the **new description**:")
            desc_msg = await bot.wait_for('message', check=matchesContext, timeout=300.0)
            new_description = desc_msg.content.strip()

            data[name] = new_description
            save_json(CATEGORY_JSON_FILES[category], data)
            await ctx.send(f"Entry `{name}` in `{category}` updated successfully.")

            await log_update(ctx, 'update', category, name, old_desc=old_description, new_desc=new_description)

        elif operation == 'delete':
            if not data:
                await ctx.send(f"No entries found in `{category}` to delete.")
                return

            entries_list = '\n'.join([f"- {entry}" for entry in data.keys()])
            await ctx.send(f"Current entries in `{category}`:\n{entries_list}\n\nEnter the **name** of the entry you want to delete:")

            name_msg = await bot.wait_for('message', check=matchesContext, timeout=60.0)
            name = name_msg.content.strip()

            if name.lower() == "cancel":
                await ctx.send("Cancelled.")
                return

            if name not in data:
                await ctx.send(f"No entry named `{name}` found in `{category}`. Operation cancelled.")
                return

            old_description = data[name]

            await ctx.send(f"Are you sure you want to delete `{name}` from `{category}`? Type `yes` to confirm.")

            confirm_msg = await bot.wait_for('message', check=matchesContext, timeout=30.0)
            if confirm_msg.content.lower() == 'yes':
                del data[name]
                save_json(CATEGORY_JSON_FILES[category], data)
                await ctx.send(f"Entry `{name}` deleted from `{category}` successfully.")

                await log_update(ctx, 'delete', category, name, old_desc=old_description)
            else:
                await ctx.send("Deletion cancelled.")

    except asyncio.TimeoutError:
        await ctx.send("You took too long to respond. Please start the operation again.")

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

@bot.command(name='habibi', help="Responds with a personalized message.")
async def habibi(ctx):
    user_name = ctx.author.name
    response = f"{user_name} is Diddy's Habibi but loves Jack the most"
    await ctx.send(response)

@bot.command(name='evesjoke', help="Diddle East")
async def evesjoke(ctx):
    await ctx.send("Diddy is didling off to the diddle east. - Eve Makya")

@bot.command(name='commend', help="Shows a commendation form.")
async def commend(ctx):
    # Check if the command was used in a DM or a guild (server) channel
    in_guild = ctx.guild is not None

    # Delete the command message if it's in a guild (server)
    if in_guild:
        await ctx.message.delete()

    def matchesContext(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        # Ask for the operation name (title of the commendation)
        operation_question = await ctx.send("Please enter the **operation name** or title of the commendation:")
        operation_msg = await bot.wait_for('message', check=matchesContext, timeout=60.0)
        operation = operation_msg.content.strip()

        if in_guild:
            await operation_question.delete()
            await operation_msg.delete()

        if operation.lower() == "cancel":
            await ctx.send("Cancelled.")
            return

        # Ask for the Commended person's Discord username
        commended_question = await ctx.send("Please enter the **Discord username** (e.g., Username#1234) of the person being commended:")
        commended_msg = await bot.wait_for('message', check=matchesContext, timeout=60.0)
        commended_username = commended_msg.content.strip()

        if in_guild:
            await commended_question.delete()
            await commended_msg.delete()

        if commended_username.lower() == "cancel":
            await ctx.send("Cancelled.")
            return

        # Resolve the user by username in guild context
        commended_user = None
        if in_guild:
            commended_user = discord.utils.get(ctx.guild.members, name=commended_username.split('#')[0], discriminator=commended_username.split('#')[1])

        # If in DM or the user wasn't found in the guild, use the input as the username directly
        commended_display = commended_user.mention if commended_user else commended_username

        # Ask for the name of the person making the commendation
        by_question = await ctx.send("Please enter your **name**:")
        by_msg = await bot.wait_for('message', check=matchesContext, timeout=60.0)
        by = by_msg.content.strip()

        if in_guild:
            await by_question.delete()
            await by_msg.delete()

        if by.lower() == "cancel":
            await ctx.send("Cancelled.")
            return

        # Ask for the role of the commended person
        role_question = await ctx.send("Please enter the **role** of the person being commended:")
        role_msg = await bot.wait_for('message', check=matchesContext, timeout=60.0)
        role = role_msg.content.strip()

        if in_guild:
            await role_question.delete()
            await role_msg.delete()

        if role.lower() == "cancel":
            await ctx.send("Cancelled.")
            return

        # Ask for the reason for the commendation
        reason_question = await ctx.send("Please enter the **reason** for the commendation:")
        reason_msg = await bot.wait_for('message', check=matchesContext, timeout=60.0)
        reason = reason_msg.content.strip()

        if in_guild:
            await reason_question.delete()
            await reason_msg.delete()

        # Create and send the commendation message
        commendations_channel = bot.get_channel(COMMENDATIONS_CHANNEL_ID)
        if commendations_channel:
            try:
                message = (
                    f"Operation Name: {operation}\n"
                    f"Commended: {commended_display}\n"  # Display the mention or the username directly
                    f"By: {by}\n"
                    f"Role: {role}\n"
                    f"Reason: {reason}"
                )
                await commendations_channel.send(message)
                await ctx.send("Thank you for the commendation! It has been submitted successfully.")
            except discord.Forbidden:
                await ctx.send(f"Permission error: Bot does not have permission to send messages in the commendations channel.")
            except Exception as e:
                await ctx.send(f"An error occurred: {e}")
        else:
            await ctx.send("Commendations channel not found!")

    except asyncio.TimeoutError:
        await ctx.send("You took too long to respond. Please start the commendation process again.")


@update.error
async def update_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send(f"This command can only be used by {REQUIRED_ROLE}.")

@bot.command(name='logout', help="Logs out the bot (only Devs).")
async def logout(ctx):
    if ctx.author.id not in [
        782304285387128832,  # Jack
        216027379506741249,  # Adrian
    ]:
        await ctx.send("You are not authorized to use this command.")
        return
    bot.logout()

if __name__ == "__main__":
    bot.run(TOKEN)
