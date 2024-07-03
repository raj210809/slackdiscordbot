import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask
from slackeventsapi import SlackEventAdapter
from slack_sdk import WebClient as SlackClient
import discord
import asyncio
import threading
import uvicorn

# Load environment variables
env_path = Path(".") / '.env'
load_dotenv(dotenv_path=env_path)


# Discord setup
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith('vibhu'):
        await message.channel.send('vibhu randi h')

bot.run(os.environ['DISCORD_TOKEN'])