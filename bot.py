import os
from pathlib import Path
from dotenv import load_dotenv
import discord
import requests
import asyncio
from threading import Thread
from flask import Flask, request, jsonify

# Load environment variables
env_path = Path(".") / '.env'
load_dotenv(dotenv_path=env_path)

# Discord setup
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = discord.Client(intents=intents)

channel_id = None  # This will store the channel ID after on_ready event

@bot.event
async def on_ready():
    global channel_id
    print(f'We have logged in as {bot.user}')
    for guild in bot.guilds:
        for channel in guild.text_channels:
            if channel.name == 'general':  # Replace with your desired channel name
                channel_id = channel.id
                print(f'Channel found: {channel.name} (ID: {channel.id})')
                break

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith('vibhu') or message.content.startswith('Vibhu'):
        await message.channel.send('vibhu randi h')
    requests.post('http://localhost:3000/discord_message', json={'content': message.content})

def send_message_to_discord(content, message_id):
    if channel_id:
        channel = bot.get_channel(channel_id)
        print(channel)
        if channel:
            asyncio.run_coroutine_threadsafe(channel.send(f'{content} (discord:{message_id})'), bot.loop)

app2 = Flask(__name__)

@app2.route('/slack_message', methods=['POST'])
def handle_slack_message():
    data = request.json
    message_content = data.get('content')
    if message_content:
        send_message_to_discord(message_content, message_id)
        return jsonify({'status': 'Message sent'}), 200
    else:
        return jsonify({'error': 'No content to send'}), 400

def run_flask():
    app2.run(port=5000, debug=True, use_reloader=False)  # Disable reloader

if __name__ == "__main__":
    flask_thread = Thread(target=run_flask)
    flask_thread.start()
    bot.run(os.environ['DISCORD_TOKEN'])
