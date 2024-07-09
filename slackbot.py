import requests
import os, slack
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from pathlib import Path
from flask import Flask, request, jsonify
from slackeventsapi import SlackEventAdapter
from dotenv import load_dotenv
from slackbot_googleai import generate_response
import asyncio
from slack_backup import upload_to_google_drive
from datetime import datetime
import json

env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
slackclient = slack.WebClient(token=os.environ["SLACK_TOKEN"])
slack_signing_secret = os.environ["SIGNING_SECRET"]

slack_event_adapter = SlackEventAdapter(slack_signing_secret, "/slack/events", app)

botid = slackclient.api_call("auth.test")["user_id"]

prev_client_id=''

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

def fetch_channel_history(channel_id):
    try:
        result = slackclient.conversations_history(channel=channel_id)
        return result['messages']
    except SlackApiError as e:
        print(f"Error fetching conversations: {e.response['error']}")
        return None

def upload():
    messages = fetch_channel_history(CHANNEL_ID)
    if messages:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"chat_history_{timestamp}.json"
        with open(filename, 'w') as file:
            json.dump(messages, file)
        upload_to_google_drive(filename)
        os.remove(filename)


def need_ai(text):
    bot_mentioned = f"<@{botid}>" in text
    command_present = "tellme" in text.lower()
    return bot_mentioned and command_present
def is_backup_command(text):
    bot_mentioned = f"<@{botid}>" in text
    backup_command_present = "bot backup" in text.lower()
    return bot_mentioned and backup_command_present
def backup_channel_history(channel_id):
    messages = fetch_channel_history(channel_id)
    if messages:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"chat_history_{timestamp}.json"
        with open(filename, 'w') as file:
            json.dump(messages, file)
        upload_to_google_drive(filename)
        os.remove(filename)


async def process_message(text, channel_id):
    if need_ai(text):
        response = await generate_response(text)
        slackclient.chat_postMessage(channel=channel_id, text=response)

        
def post(timestamp, channel_id, user_id, text, username, channel_name):
    try:
        response = requests.post(
            "http://localhost:5000/slack_message",
            json={"content": text, "user": username, "channel": channel_name},
        )
        if response.status_code == 200:
            print("Message forwarded to local server")
            return 1
        else:
            print(
                f"Failed to forward message: {response.status_code} - {response.text}"
            )
            mybackup(timestamp, channel_id, user_id, text, username, channel_name)

        # process_message(text, channel_id)
    except requests.exceptions.RequestException as e:
        print(f"Request exception: {e}")
        return 0


@slack_event_adapter.on("message")
def message(payload):
    event = payload.get("event", {})
    client_id = event.get("client_msg_id")

    if client_id == prev_client_id:
        return jsonify({"status": "ignored"}), 200
    else:
        prev_client_id = client_id

    channel_id = event.get("channel")
    user_id = event.get("user")
    text = event.get("text")
    channel_name = get_channel_name(channel_id)
    username = get_username(user_id)
    timestamp = event.get("timestamp")
    if is_backup_command(text):
        backup_channel_history(channel_id)
    else:
        post(timestamp, channel_id, user_id, text, username, channel_name)


@app.route("/discord_message", methods=["POST"])
def publishmessage():
    data = request.json
    content = data.get("content")
    slackclient.chat_postMessage(channel="#slackbo", text=content)
    return jsonify({"status": "Message sent"}), 200


if __name__ == "__main__":
    app.run(port=3000 , debug=True)