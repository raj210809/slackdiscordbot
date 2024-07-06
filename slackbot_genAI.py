import os
import openai
from pathlib import Path
from dotenv import load_dotenv


def generate_response(user_text):
    env_path = Path(".") / ".env"
    load_dotenv(dotenv_path=env_path)
    openai.api_key = os.environ["OPENAI_API_KEY"]
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",  # latest free model.
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_text},
            ],
            max_tokens=150,
        )
        reply_text = response["choices"][0]["text"].strip()

        return reply_text
    except Exception as e:
        print(f"Error generating response: {e}")
        return "Sorry, I couldn't generate any response."
