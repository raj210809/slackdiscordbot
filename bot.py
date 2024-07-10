import os
from pathlib import Path
from dotenv import load_dotenv
import discord
import requests
import asyncio
from threading import Thread
from flask import Flask, request, jsonify
from slackbot_googleai import generate_response


env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = discord.Client(intents=intents)


async def get_or_create_channel(channel_name):
    for guild in bot.guilds:
        for channel in guild.text_channels:
            if channel.name == channel_name:
                return channel

    for guild in bot.guilds:
        new_channel = await guild.create_text_channel(channel_name)
        return new_channel


@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith('raptor'):
        response = generate_response(message.content)
        await message.channel.send(response)

    requests.post(
        "http://localhost:3000/discord_message", json={"content": str(message.content) ,"user": str(message.author),"channel":str(message.channel)}
    )


async def send_message_to_discord(content, channel, user):
    await channel.send(f'{user} : {content}')

app2 = Flask(__name__)


@app2.route("/slack_message", methods=["POST"])
def handle_slack_message():
    data = request.json
    print(data)
    message_content = data.get("content")
    channel_name = data.get("channel")
    username = data.get("user")

    # Use a future to get the result from the async function
    future = asyncio.run_coroutine_threadsafe(
        get_or_create_channel(channel_name), bot.loop
    )
    channel = future.result()

    if message_content and channel:
        asyncio.run_coroutine_threadsafe(
            send_message_to_discord(message_content, channel, username), bot.loop
        )
        return jsonify({"status": "Message sent"}), 200
    else:
        return jsonify({"error": "No content to send or channel not found"}), 400


def run_flask():
    app2.run(port=5000, debug=True, use_reloader=False)


if __name__ == "__main__":
    flask_thread = Thread(target=run_flask)
    flask_thread.start()
    bot.run(os.environ["DISCORD_TOKEN"])
