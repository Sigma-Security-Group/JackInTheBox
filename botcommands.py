import json
import discord
from discord.ext import commands
import os
import asyncio

from secret import TOKEN

# Define intents and create bot instance
intents = discord.Intents.default()
intents.message_content = True  # Ensure the bot can read message content
bot = commands.Bot(command_prefix="!", intents=intents)

# Define the role required to use update commands
REQUIRED_ROLE = "Unit Staff"

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

    embed = discord.Embed(
        title=category.capitalize(),
        description=f"Entries in the {category} category.",
        color=discord.Color.blue()
    )

    for name, description in data.items():
        embed.add_field(name=name, value=description, inline=False)

    await ctx.send(embed=embed)

# Command to interactively add, update, or delete entries
@bot.command(name='update', help="Add, update, or delete entries in a category. Usage: !update [category]")
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

            await ctx.send(f"Current description for `{name}`:\n{data[name]}\n\nEnter the **new description**:")
            desc_msg = await bot.wait_for('message', check=check, timeout=300.0)
            description = desc_msg.content.strip()

            data[name] = description
            save_json(CATEGORY_JSON_FILES[category], data)
            await ctx.send(f"Entry `{name}` in `{category}` updated successfully.")

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

            await ctx.send(f"Are you sure you want to delete `{name}` from `{category}`? Type `yes` to confirm.")

            confirm_msg = await bot.wait_for('message', check=check, timeout=30.0)
            if confirm_msg.content.lower() == 'yes':
                del data[name]
                save_json(CATEGORY_JSON_FILES[category], data)
                await ctx.send(f"Entry `{name}` deleted from `{category}` successfully.")
            else:
                await ctx.send("Deletion cancelled.")

    except asyncio.TimeoutError:
        await ctx.send("You took too long to respond. Please start the operation again.")

# ALL COMMAMNDS
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

# Command that responds with a specific message
@bot.command(name='habibi', help="Responds with a personalized message.")
async def habibi(ctx):
    # Get the user's name
    user_name = ctx.author.name
    # Create a personalized message
    response = f"{user_name} is Diddy's Habibi"
    # Send the response message
    await ctx.send(response)

# Command that responds with a specific message
@bot.command(name='evesjoke', help="Diddle East")
async def habibi(ctx):
    # Send the response message
    await ctx.send("Diddy is didling off to the diddle east. - Eve")

# Error handler for missing role
@update.error
async def update_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send(f"This command can only be used by {REQUIRED_ROLE}.")

bot.run(TOKEN)