import os
import slack
from pathlib import Path
from flask import Flask
from slackeventsapi import SlackEventAdapter
from dotenv import load_dotenv

env_path = Path(".") / '.env'
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
slackclient = slack.WebClient(token=os.environ['SLACK_TOKEN'])
slack_event_adapter = SlackEventAdapter(
    os.environ['SIGNING_SECRET'], '/slack/events', app
)

botid = slackclient.api_call("auth.test")["user_id"]

@slack_event_adapter.on('message')
def message(payload):
    event = payload.get('event', {})
    channel_id = event.get('channel')
    user_id = event.get('user')
    text = event.get('text')
    if user_id != botid:
        slackclient.chat_postMessage(channel=channel_id, text=text)

if __name__ == "__main__":
    app.run(port=3000,debug=True)
