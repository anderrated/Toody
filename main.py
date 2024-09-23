import nextcord
from nextcord import Interaction
from nextcord.ext import commands
import aiosqlite

# Import Bot Token
from apikeys import BOTTOKEN

# Initialize bot
intents = nextcord.Intents.all()
client = commands.Bot(command_prefix='t!', intents=intents)

# Emoji
CHECKMARK = '✅'

@client.event
async def on_ready():
    print("Toody is now ready for use!")
    print("===========================")
    async with aiosqlite.connect("main.db") as db:
        async with db.cursor() as cursor:
            # Drop the existing table if you want to start fresh
            await cursor.execute("DROP TABLE IF EXISTS tasks")

            # Recreate the table with the new schema
            await cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild INTEGER,
                    user INTEGER,
                    task TEXT NOT NULL,
                    checked BOOLEAN NOT NULL DEFAULT FALSE
                )
                """
            )
        await db.commit()

# Hello
@client.command(name='hello', help='Say hello to Toody')
async def hello(ctx):
    await ctx.send("Hello! I am duhless' babyboi, Toody!")

# remove test server id when publishing
# this is used so we don't have to wait for an hour for commands to work
testServerId = 1111972230872699000

@client.slash_command(name="hello", description="Say hello to Toody.", guild_ids=[testServerId])
async def greet(interaction: Interaction):
    await interaction.response.send_message("Hello! I am duhless' babyboi, Toody!")

# Bye
@client.command(name='bye', help='Say goodbye to Toody')
async def bye(ctx):
    await ctx.send("You don't love me anymore. I'm gonna go huhuhu.")

@client.slash_command(name="bye", description="Say goodbye to Toody.", guild_ids=[testServerId])
async def goodbye(interaction: Interaction):
    await interaction.response.send_message("You don't love me anymore. I'm gonna go huhuhu.")

# Add task for a specific user in a guild
@client.command(name='add', help='Add a task to your personal to-do list')
async def tadd(ctx, *, task):
    async with aiosqlite.connect("main.db") as db:
        async with db.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO tasks (guild, user, task, checked) VALUES (?, ?, ?, ?)",
                (ctx.guild.id, ctx.author.id, task, False)
            )
        await db.commit()
    await ctx.send(f'Task "{task}" added to your toody list.')
    await tlist(ctx)

@client.slash_command(name="add", description="Add a task to your personal to-do list.")
async def slash_add(interaction: Interaction, task: str):
    async with aiosqlite.connect("main.db") as db:
        async with db.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO tasks (guild, user, task, checked) VALUES (?, ?, ?, ?)",
                (interaction.guild.id, interaction.user.id, task, False)
            )
        await db.commit()
    await interaction.response.send_message(f'Task "{task}" added to your toody list.')
    # Show the updated list after the add command
    embed = await slash_list(interaction, from_command=True)
    await interaction.followup.send(embed=embed)


# List tasks for a specific user
@client.command(name='list', help='List all tasks in your personal to-do list')
async def tlist(ctx):
    async with aiosqlite.connect("main.db") as db:
        async with db.cursor() as cursor:
            # Fetch tasks for the current user in the current guild
            await cursor.execute(
                "SELECT id, task, checked FROM tasks WHERE guild = ? AND user = ?",
                (ctx.guild.id, ctx.author.id)
            )
            tasks = await cursor.fetchall()

    if not tasks:
        tlist = nextcord.Embed(title="OH NAUR!!!", description="Your toody list is empty.", color=0x784249)
        tlist.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
        await ctx.send(embed=tlist)
    else:
        task_list = "\n".join([f'{"✅ " if task[2] else "◻️ "}{index + 1}. {task[1]}' for index, task in enumerate(tasks)])
        tlist = nextcord.Embed(title="Your toody list:", description=task_list, color=0x784255)
        tlist.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
        await ctx.send(embed=tlist)

@client.slash_command(name="list", description="List all tasks in your personal to-do list.")
async def slash_list(interaction: Interaction, from_command=False):
    async with aiosqlite.connect("main.db") as db:
        async with db.cursor() as cursor:
            await cursor.execute(
                "SELECT id, task, checked FROM tasks WHERE guild = ? AND user = ?",
                (interaction.guild.id, interaction.user.id)
            )
            tasks = await cursor.fetchall()

    if not tasks:
        tlist_embed = nextcord.Embed(title="OH NAUR!!!", description="Your toody list is empty.", color=0x784249)
        tlist_embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar.url)
        if from_command:
            return tlist_embed
        else:
            await interaction.response.send_message(embed=tlist_embed)
    else:
        task_list = "\n".join([f'{"✅ " if task[2] else "◻️ "}{index + 1}. {task[1]}' for index, task in enumerate(tasks)])
        tlist_embed = nextcord.Embed(title="Your toody list:", description=task_list, color=0x784255)
        tlist_embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar.url)
        if from_command:
            return tlist_embed
        else:
            await interaction.response.send_message(embed=tlist_embed)


# Status helper to check/uncheck task for a specific user
async def update_task_status(ctx_or_interaction, task_number: int, checked: bool):
    user_id = ctx_or_interaction.author.id if hasattr(ctx_or_interaction, 'author') else ctx_or_interaction.user.id
    guild_id = ctx_or_interaction.guild.id

    async with aiosqlite.connect("main.db") as db:
        async with db.cursor() as cursor:
            # Fetch tasks for the current user in the current guild
            await cursor.execute(
                "SELECT id, task FROM tasks WHERE guild = ? AND user = ?",
                (guild_id, user_id)
            )
            tasks = await cursor.fetchall()

            # Check if the task_number is valid
            if 0 < task_number <= len(tasks):
                task_id = tasks[task_number - 1][0]
                task_name = tasks[task_number - 1][1]

                # Update the checked status
                await cursor.execute("UPDATE tasks SET checked = ? WHERE id = ?", (checked, task_id))
                await db.commit()

                # Send feedback to the user
                await ctx_or_interaction.send(f'Task "{task_name}" has been {"checked" if checked else "unchecked"}.')
            else:
                await ctx_or_interaction.send('Invalid task number. Please check the list and try again.')


# Check a task in the to-do list
@client.command(name='check', help='Check a task in your personal to-do list')
async def tcheck(ctx, task_number: int):
    await update_task_status(ctx, task_number, True)
    await tlist(ctx)

@client.slash_command(name="check", description="Check a task in your personal to-do list.")
async def slash_check(interaction: Interaction, task_number: int):
    await update_task_status(interaction, task_number, True)
    # Show the updated list after the check command
    embed = await slash_list(interaction, from_command=True)
    await interaction.followup.send(embed=embed)


# Uncheck a task in the to-do list
@client.command(name='uncheck', help='Uncheck a task in your personal to-do list')
async def tuncheck(ctx, task_number: int):
    await update_task_status(ctx, task_number, False)
    await tlist(ctx)

@client.slash_command(name="uncheck", description="Uncheck a task in your personal to-do list.")
async def slash_uncheck(interaction: Interaction, task_number: int):
    await update_task_status(interaction, task_number, False)
    # Show the updated list after the uncheck command
    embed = await slash_list(interaction, from_command=True)
    await interaction.followup.send(embed=embed)


# Remove task for a specific user
@client.command(name='remove', help='Remove a task from your personal to-do list')
async def tremove(ctx, task_number: int):
    await remove_task(ctx, task_number)

@client.slash_command(name="remove", description="Remove a task from your personal to-do list.")
async def slash_remove(interaction: Interaction, task_number: int):
    await remove_task(interaction, task_number)

async def remove_task(ctx_or_interaction, task_number: int):
    user_id = ctx_or_interaction.author.id if hasattr(ctx_or_interaction, 'author') else ctx_or_interaction.user.id
    guild_id = ctx_or_interaction.guild.id

    async with aiosqlite.connect("main.db") as db:
        async with db.cursor() as cursor:
            await cursor.execute("SELECT id, task FROM tasks WHERE guild = ? AND user = ?", (guild_id, user_id))
            tasks = await cursor.fetchall()

            if 0 < task_number <= len(tasks):
                task_id = tasks[task_number - 1][0]
                task_name = tasks[task_number - 1][1]

                # Remove task from database
                await cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                await db.commit()

                await ctx_or_interaction.send(f'Task "{task_name}" removed from your toody list.')
            else:
                await ctx_or_interaction.send('Invalid task number. Please check the list and try again.')

    if hasattr(ctx_or_interaction, 'author'):
        await tlist(ctx_or_interaction)
    else:
        embed = await slash_list(ctx_or_interaction, from_command=True)
        await ctx_or_interaction.followup.send(embed=embed)


# Edit task for a specific user
@client.command(name='edit', help='Edit a task from your personal to-do list')
async def tedit(ctx, task_number: int, *, new_task):
    await edit_task(ctx, task_number, new_task)

@client.slash_command(name="edit", description="Edit a task from your personal to-do list.")
async def slash_edit(interaction: Interaction, task_number: int, new_task: str):
    await edit_task(interaction, task_number, new_task)

async def edit_task(ctx_or_interaction, task_number: int, new_task: str):
    user_id = ctx_or_interaction.author.id if hasattr(ctx_or_interaction, 'author') else ctx_or_interaction.user.id
    guild_id = ctx_or_interaction.guild.id

    async with aiosqlite.connect("main.db") as db:
        async with db.cursor() as cursor:
            # Fetch tasks for the current user
            await cursor.execute("SELECT id FROM tasks WHERE guild = ? AND user = ?", (guild_id, user_id))
            tasks = await cursor.fetchall()

            if 0 < task_number <= len(tasks):
                task_id = tasks[task_number - 1][0]

                # Update task in database
                await cursor.execute("UPDATE tasks SET task = ? WHERE id = ?", (new_task, task_id))
                await db.commit()

                await ctx_or_interaction.send(f'Task "{new_task}" updated in your toody list.')
            else:
                await ctx_or_interaction.send('Invalid task number. Please check the list and try again.')

    if hasattr(ctx_or_interaction, 'author'):
        await tlist(ctx_or_interaction)
    else:
        embed = await slash_list(ctx_or_interaction, from_command=True)
        await ctx_or_interaction.followup.send(embed=embed)


# Clear all tasks for a specific user
@client.command(name='clear', help='Clear your personal to-do list')
async def tclear(ctx):
    await clear_tasks(ctx)

@client.slash_command(name="clear", description="Clear your personal to-do list.")
async def slash_clear(interaction: Interaction):
    await clear_tasks(interaction)

async def clear_tasks(ctx_or_interaction):
    user_id = ctx_or_interaction.author.id if hasattr(ctx_or_interaction, 'author') else ctx_or_interaction.user.id
    guild_id = ctx_or_interaction.guild.id

    async with aiosqlite.connect("main.db") as db:
        async with db.cursor() as cursor:
            # Delete all tasks for the current user in the guild
            await cursor.execute("DELETE FROM tasks WHERE guild = ? AND user = ?", (guild_id, user_id))
            await db.commit()

    await ctx_or_interaction.send('Your toody list has been cleared.')

    if hasattr(ctx_or_interaction, 'author'):
        await tlist(ctx_or_interaction)
    else:
        embed = await slash_list(ctx_or_interaction, from_command=True)
        await ctx_or_interaction.followup.send(embed=embed)


client.run(BOTTOKEN)
