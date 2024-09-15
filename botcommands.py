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

GUILD_ID = 288446755219963914
GUILD = discord.Object(id=GUILD_ID)

# Define the role required to use update commands
REQUIRED_ROLE = "Unit Staff"

# ID of the channel where update logs will be sent
AUDIT_LOGS_CHANNEL_ID = 825039647456755772
COMMENDATIONS_CHANNEL_ID = 1109263109526396938 # Replace with the actual ID of the commendations channel
reports_log = {}

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
    bot.tree.clear_commands(guild=GUILD)
    bot.tree.add_command(commend, guild=GUILD)
    await bot.tree.sync(guild=GUILD)
    logging.info(f'Logged in as {bot.user.name}')

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

@discord.app_commands.command(name="commend")
@discord.app_commands.guilds(GUILD)
@discord.app_commands.describe(
    person = "Person to commend.",
    role = "The user's role in the operation.",
    reason = "Why you commend these user."
)
async def commend(interaction: discord.Interaction, person: discord.User, role: str, reason: str) -> None:
    """ Commend a person that has done well in an operation. """
    logging.info(f"{interaction.user.display_name} ({interaction.user.id}) commended person {user.display_name} ({user.id}).")
    guild = bot.get_guild(GUILD_ID)
    if guild is None:
        logging.exception("commend: guild is None")
        return

    channelCommendations = await guild.fetch_channel(COMMENDATIONS_CHANNEL_ID)
    if not isinstance(channelCommendations, discord.TextChannel):
        logging.exception("commend: channelCommendations is not discord.TextChannel")
        return

    await channelCommendations.send(
        f"Commended: {user.mention}\n"
        f"By: {interaction.user.mention}\n"
        f"Role: {role}\n"
        f"Reason: {reason}"
    )

    await interaction.response.send_message(f"Thank you for commending! It has been submitted successfully in {channelCommendations.mention}.", ephemeral=True, delete_after=10.0)


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
    await bot.close()

@bot.command(name='Incident_Report')
async def incident_report(ctx):
    # Store a new empty report for this user
    report_data = {
        'subject': '',
        'person_reported': '',
        'staff_handler': '',
        'second_staff': '',
        'details': '',
        'evidence': '',
        'ticket_numbers': '',
        'moderation_action': ''
    }
    
    # Step 1: Ask for the subject of the report
    await ctx.send(
        "Please enter the subject of the report:",
        components=[Button(style=ButtonStyle.green, label="Proceed", custom_id="subject")]
    )

    # Event handling based on user interaction
    async def proceed_report(user_id):
        # Step 2: Ask for the person being reported
        await ctx.send(
            "Enter the name and Discord ID of the person being reported:",
            components=[Button(style=ButtonStyle.green, label="Proceed", custom_id="person_reported")]
        )
        # Add further steps as needed (rest of the fields similar to below)
        # After all fields are filled, store the report in the logger
        reports_log[user_id] = report_data

        logger.info(f"Report added for user ID: {user_id}")

# Command to fetch all reports of a particular user by Discord ID
@bot.command(name='get_reports')
async def get_reports(ctx, user_id: int):
    # Check if there are any reports for the given user ID
    if user_id in reports_log:
        report = reports_log[user_id]
        embed = discord.Embed(title=f"Reports for User ID: {user_id}", color=0x3498db)
        embed.add_field(name="Subject", value=report['subject'], inline=False)
        embed.add_field(name="Person Reported", value=report['person_reported'], inline=False)
        embed.add_field(name="Staff Handler", value=report['staff_handler'], inline=False)
        embed.add_field(name="Second Staff", value=report.get('second_staff', 'None'), inline=False)
        embed.add_field(name="Details", value=report['details'], inline=False)
        embed.add_field(name="Evidence", value=report['evidence'], inline=False)
        embed.add_field(name="Ticket Numbers", value=report['ticket_numbers'], inline=False)
        embed.add_field(name="Moderation Action", value=report['moderation_action'], inline=False)

        await ctx.send(embed=embed)
    else:
        await ctx.send(f"No reports found for user ID: {user_id}")

# Event: On button click, proceed through the report steps
@bot.event
async def on_button_click(interaction: Interaction):
    user_id = interaction.user.id

    # Delete the previous message for cleanup
    await interaction.message.delete()

    # Handle the rest of the interaction steps like collecting data
    # Example for subject
    if interaction.custom_id == "subject":
        await interaction.send(
            "Enter the name and Discord ID of the person being reported:",
            components=[Button(style=ButtonStyle.green, label="Proceed", custom_id="person_reported")]
        )
    elif interaction.custom_id == "person_reported":
        await interaction.send(
            "Tag the staff handler:",
            components=[Button(style=ButtonStyle.green, label="Proceed", custom_id="staff_handler")]
        )
    # Additional steps for other fields

# Delete all previous messages after command completion
async def cleanup_messages(ctx, messages):
    for msg in messages:
        try:
            await msg.delete()
        except discord.Forbidden:
            pass
        except discord.HTTPException:
            pass

@bot.event
async def on_command_completion(ctx):
    # Fetch recent messages from the channel including both user and bot messages
    messages = await ctx.channel.history(limit=10).flatten()
    await cleanup_messages(ctx, messages)

if __name__ == "__main__":
    bot.run(TOKEN)
