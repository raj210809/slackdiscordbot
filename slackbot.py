import requests
import os, slack
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from pathlib import Path
from flask import Flask, request, jsonify
from slackeventsapi import SlackEventAdapter
from dotenv import load_dotenv
from slackbot_gpt2_2 import generate_response
from slack_backup import mybackup, prev_log, retrieve

# Load environment variables
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


def need_ai(text):
    bot_mentioned = f"<@{botid}>" in text
    command_present = "tellme" in text.lower()
    return bot_mentioned and command_present


def process_message(text, channel_id):
    # slackclient.chat_postMessage(
    #     channel=channel_id, text=text
    # )  # assign properly ratherthan sending to same channel
    if need_ai(text):
        response = generate_response(text)
        slackclient.chat_postMessage(channel=channel_id, text=response)
        print(f"posted the response at channel id: {channel_id}")


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

        process_message(text, channel_id)
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
        prev_client_id=client_id

    channel_id = event.get("channel")
    user_id = event.get("user")
    text = event.get("text")
    channel_name = get_channel_name(channel_id)
    username = get_username(user_id)
    timestamp = event.get("timestamp")

    while prev_log():
        myitem = retrieve()
        if not post(
            myitem["timestamp"],
            myitem["channel_id"],
            myitem["user_id"],
            myitem["text"],
            myitem["username"],
            myitem["channel_name"],
        ):
            break

    # post the message which just came.
    post(timestamp, channel_id, user_id, text, username, channel_name)


# @app.route("/discord_message", methods=["POST"])
# def publishmessage():
#     data = request.json
#     content = data.get("content")
#     slackclient.chat_postMessage(channel="#slackbo", text=content)
#     return jsonify({"status": "Message sent"}), 200


if __name__ == "__main__":
    #app.run(port=3000, debug=True)
    from waitress import serve
    serve(app, host="0.0.0.0", port=3000)
