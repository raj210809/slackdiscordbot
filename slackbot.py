import requests
import os
import slack
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from pathlib import Path
from flask import Flask, request, jsonify
from slackeventsapi import SlackEventAdapter
from dotenv import load_dotenv
from slackbot_gpt2 import generate_response
import asyncio

# Load environment variables
env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
slackclient = slack.WebClient(token=os.environ["SLACK_TOKEN"])
slack_signing_secret = os.environ["SIGNING_SECRET"]

slack_event_adapter = SlackEventAdapter(slack_signing_secret, "/slack/events", app)

botid = slackclient.api_call("auth.test")["user_id"]

def get_channel_name(channel_id):
    try:
        response = slackclient.conversations_info(channel=channel_id)
        if response["ok"]:
            return response["channel"]["name"]
    except SlackApiError as e:
        print(f"Error fetching channel name: {e.response['error']}")
    return None

def get_username(user_id):
    try:
        response = slackclient.users_info(user=user_id)
        if response["ok"]:
            return response["user"]["name"]
    except SlackApiError as e:
        print(f"Error fetching username: {e.response['error']}")
    return None

def need_ai(text):
    return text.lower().startswith("tellme")

async def process_message(text, channel_id):
    if need_ai(text):
        response = await generate_response(text)
        slackclient.chat_postMessage(channel=channel_id, text=response)

@slack_event_adapter.on("message")
def message(payload):
    event = payload.get('event', {})
    channel_id = event.get('channel')
    user_id = event.get('user')
    text = event.get('text')
    channel_name = get_channel_name(channel_id)
    username = get_username(user_id)

    if user_id != botid:
        try:
            response = requests.post('http://localhost:5000/slack_message', json={'content': text, 'user': username, 'channel': channel_name})
            if response.status_code == 200:
                print("Message forwarded to local server")
            else:
                print(f"Failed to forward message: {response.status_code} - {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Request exception: {e}")

        asyncio.run(process_message(text=text, channel_id=channel_id))

@app.route('/discord_message', methods=['POST'])
def publishmessage():
    data = request.json
    content = data.get('content')
    user = data.get('user')
    channel = data.get('channel')
    slackclient.chat_postMessage(channel=f"#{channel}", text=f"{user}:{content}")
    return jsonify({'status': 'Message sent'}), 200

if __name__ == "__main__":
    app.run(port=3000, debug=True)
