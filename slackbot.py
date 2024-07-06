import os
import slack
from pathlib import Path
from flask import Flask
from slackeventsapi import SlackEventAdapter
from dotenv import load_dotenv
from slackbot_gpt2 import generate_response

# Load environment variables
env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
slackclient = slack.WebClient(token=os.environ["SLACK_TOKEN"])
slack_signing_secret = os.environ["SIGNING_SECRET"]

slack_event_adapter = SlackEventAdapter(slack_signing_secret, "/slack/events", app)

botid = slackclient.api_call("auth.test")["user_id"]


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


@slack_event_adapter.on("message")
def message(payload):
    event = payload.get("event", {})
    channel_id = event.get("channel")
    user_id = event.get("user")
    text = event.get("text")
    if user_id != botid:
        print(
            f"Processing message: {text} from user: {user_id} in channel: {channel_id}"
        )
        process_message(text, channel_id)
    print(f"Received message: {text} from user: {user_id} in channel: {channel_id}")


if __name__ == "__main__":
    app.run(port=3000, debug=True)
