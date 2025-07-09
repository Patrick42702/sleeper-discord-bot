import os

import discord
from discord.ext import commands

# Define intents
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent for prefix commands

client = commands.Bot(intents=intents, command_prefix="/")

# Access the tree for slash commands
tree = client.tree


@client.event
async def on_ready():
    await tree.sync()  # Sync slash commands with Discord
    print(f"Logged in as {client.user}")


# Example: a slash command with an autocomplete option
OPTIONS = ["apple", "banana", "cherry", "date", "elderberry"]


@tree.command(name="fruit", description="Pick a fruit with autocomplete!")
@discord.app_commands.describe(name="Name of the fruit")
async def fruit_command(interaction: discord.Interaction, name: str):
    await interaction.response.send_message(f"You selected: {name}")


@fruit_command.autocomplete("name")
async def fruit_autocomplete(
    interaction: discord.Interaction, current: str
) -> list[discord.app_commands.Choice[str]]:
    matches = [fruit for fruit in OPTIONS if current.lower() in fruit.lower()]
    return [
        discord.app_commands.Choice(name=fruit, value=fruit) for fruit in matches[:25]
    ]


@client.command(name="hello", help="Says hello to the user")
async def hello(ctx):
    await ctx.send("Hello world!")


token = os.environ("TOKEN")
client.run(token)
