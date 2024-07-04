import os
import openai

openai.api_key = os.environ["OPENAI_API_KEY"]


def generate_response(user_text):
    try:
        response = openai.Completion.create(
            engine="text-davinci-003", prompt=user_text, max_tokens=150
        )
        reply_text = response["choices"][0]["text"].strip()

        return reply_text
    except Exception as e:
        print(f"Error generating response: {e}")
        return "Sorry, I couldn't generate any response."
