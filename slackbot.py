import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from pathlib import Path
from flask import Flask, request , jsonify
from slackeventsapi import SlackEventAdapter
from dotenv import load_dotenv
import requests
import json

# Load environment variables
env_path = Path(".") / '.env'
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
slackclient = WebClient(token=os.environ['SLACK_TOKEN'])
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
        try:
            response = requests.post('http://localhost:5000/slack_message', json={'content': text})
            if response.status_code == 200:
                print("Message forwarded to local server")
            else:
                print(f"Failed to forward message: {response.status_code} - {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Request exception: {e}")

@app.route('/discord_message' , methods=['POST'])
def publishmessage():
    data = request.json
    content = data.get('content')
    slackclient.chat_postMessage(channel='#slackbo' , text=content)
    return jsonify({'status': 'Message sent'}), 200

if __name__ == "__main__":
    app.run(port=3000, debug=True)
