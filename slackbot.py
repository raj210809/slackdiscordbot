import requests
import os
import slack
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
slackclient = WebClient(token=os.environ["SLACK_TOKEN"])
slack_signing_secret = os.environ["SIGNING_SECRET"]

slack_event_adapter = SlackEventAdapter(slack_signing_secret, "/slack/events", app)

botid = slackclient.api_call("auth.test")["user_id"]

prev_client_id = 35664547

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
    return text.lower().startswith('raptor')

def is_backup_command(text):
    bot_mentioned = f"<@{botid}>" in text
    backup_command_present = "backup" in text.lower()
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

def process_message(text, channel_id):
    if need_ai(text):
        response = generate_response(text)
        slackclient.chat_postMessage(channel=channel_id, text=response)

def post(timestamp, channel_id, user_id, text, username, channel_name):
    try:
        response = requests.post(
            "http://localhost:5000/slack_message",
            json={"content": text, "user": username, "channel": channel_name},
        )
        if response.status_code == 200:
            print("Message forwarded to local server")
        else:
            print(f"Failed to forward the message: {response.status_code} - {response.text}")
        
        process_message(text=text , channel_id=channel_id)
    except requests.exceptions.RequestException as e:
        print(f"Request exception: {e}")

@slack_event_adapter.on("message")
def message(payload):
    global prev_client_id
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
        if botid != user_id:
            post(timestamp, channel_id, user_id, text, username, channel_name)

@app.route("/discord_message", methods=["POST"])
def publishmessage():
    data = request.json
    content = data.get("content")
    username = data.get('user')
    channel = data.get('channel')
    slackclient.chat_postMessage(channel=f"#{channel}", text=f"{username}:{content}")
    return jsonify({"status": "Message sent"}), 200

if __name__ == "__main__":
    app.run(port=3000, debug=True)
